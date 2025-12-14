from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict, deque
import threading
import time
import sys
import uvicorn
import requests

app = FastAPI()

myProcessId = 0
N = 3  # número de réplicas (ajuste conforme processes)
V = []  # vetor de relógios locais
posts = {}  # evtId -> Event
replies = defaultdict(list)  # parentEvtId -> [Event]
buffer = deque()  # eventos aguardando causalidade ou dependências
processes = [
    "localhost:8080",
    "localhost:8081",
    "localhost:8082",
]

class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    vc: Optional[List[int]] = None  # relógio vetorial

@app.post("/post")
def post(msg: Event):
    # Emissão local: incrementa vetor e carimba
    if msg.processId == myProcessId:
        V[myProcessId] += 1
        msg.vc = V.copy()

    deliver_or_buffer(msg)

    # Reencaminhar
    payload = msg.model_dump()  
    for i, addr in enumerate(processes):
        if i == myProcessId:
            continue
        async_send(f"http://{addr}/share", payload)
    return {"status": "ok", "handledBy": myProcessId}

@app.post("/share")
def share(msg: Event):
    deliver_or_buffer(msg)
    return {"status": "ok", "receivedBy": myProcessId}

def async_send(url: str, payload: dict):
    def worker():
        try:
            # (Opcional) atraso controlado
            # if myProcessId == 0:
            #     time.sleep(0.5)
            requests.post(url, json=payload, timeout=2)
        except Exception as e:
            print(f"[WARN] send to {url} failed: {e}")
    threading.Thread(target=worker, daemon=True).start()

# casualidade
def can_deliver(msg: Event) -> bool:
    """Verifica regra de causalidade vetorial para evento do autor i."""
    if msg.vc is None or len(msg.vc) != N:
        return False
    i = msg.processId
    # Regra: para k != i: msg.vc[k] <= V[k]
    for k in range(N):
        if k == i:
            continue
        if msg.vc[k] > V[k]:
            return False
    # Regra: msg.vc[i] == V[i] + 1
    if msg.vc[i] != V[i] + 1:
        return False
    # Dependência semântica: se é reply, o post pai já deve estar entregue
    if msg.parentEvtId is not None and msg.parentEvtId not in posts:
        return False
    return True

def try_deliver_buffer():
    """Tenta entregar eventos do buffer que agora podem ser entregues."""
    delivered_any = True
    while delivered_any:
        delivered_any = False
        size = len(buffer)
        for _ in range(size):
            msg = buffer.popleft()
            if can_deliver(msg):
                apply_event(msg)
                delivered_any = True
            else:
                buffer.append(msg)

def deliver_or_buffer(msg: Event):
    if can_deliver(msg):
        apply_event(msg)
        # Após entregar algo, novas dependências podem ser satisfeitas
        try_deliver_buffer()
    else:
        buffer.append(msg)
    showFeed()


def apply_event(msg: Event):
    """Aplica evento ao estado e atualiza relógio local."""
    i = msg.processId
    # Atualiza relógio local: V[i] = msg.vc[i]
    V[i] = msg.vc[i]
    # Aplica no estado
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)


def showFeed():
    print("\n====== FEED CAUSAL (Replica", myProcessId, ") ======")
    print(f"Local V={V}, buffer={len(buffer)}")
    # Mostrar posts e suas replies (sem órfãs)
    for postId, p in sorted(posts.items(), key=lambda kv: kv[1].vc or [0]*N):
        print(f"[POST] {postId} by {p.author} vc={p.vc}: {p.text}")
        if postId in replies and replies[postId]:
            # Ordena por vc[i] do autor para leitura
            for r in sorted(replies[postId], key=lambda e: (e.vc[e.processId], e.processId)):
                print(f"  [REPLY] {r.evtId} by {r.author} vc={r.vc}: {r.text}")
    print("====== END FEED ======\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <myProcessId>")
        sys.exit(1)
    myProcessId = int(sys.argv[1])
    N = len(processes)
    V = [0] * N

    host, port = processes[myProcessId].split(":")
    uvicorn.run(app, host=host, port=int(port))
