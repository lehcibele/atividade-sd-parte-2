from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import threading
import time
import sys
import uvicorn
import requests

app = FastAPI()

myProcessId = 0
timestamp = 0  # Lamport-style simples para ordenação local
posts = {}  # evtId -> Event
replies = defaultdict(list)  # parentEvtId -> [Event]
orphans = defaultdict(list)  # parentEvtId -> [Event] (apenas debug)
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
    timestamp: Optional[int] = None  # gerado pelo autor local

@app.post("/post")
def post(msg: Event):
    global timestamp
    if msg.processId == myProcessId:
        timestamp += 1
        msg.timestamp = timestamp

    processMsg(msg)

    # Reencaminhar para outras réplicas
    payload = msg.model_dump()
    for i, addr in enumerate(processes):
        if i == myProcessId:
            continue
        async_send(f"http://{addr}/share", payload)
    return {"status": "ok", "handledBy": myProcessId}

@app.post("/share")
def share(msg: Event):
    processMsg(msg)
    return {"status": "ok", "receivedBy": myProcessId}


def async_send(url: str, payload: dict):
    def worker():
        try:
            requests.post(url, json=payload, timeout=2)
        except Exception as e:
            print(f"[WARN] send to {url} failed: {e}")
    t = threading.Thread(target=worker, daemon=True)
    t.start()


def processMsg(msg: Event):
    # Aceita qualquer ordem (eventual)
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
        # Se tem órfãs esperando pelo pai, mova para replies
        if msg.evtId in orphans:
            for r in orphans[msg.evtId]:
                replies[msg.evtId].append(r)
            del orphans[msg.evtId]
    else:
        # Se o pai já existe, anexar, senão registrar como órfã
        if msg.parentEvtId in posts:
            replies[msg.parentEvtId].append(msg)
        else:
            orphans[msg.parentEvtId].append(msg)
    showFeed()


def showFeed():
    print("\n====== FEED (Replica", myProcessId, ") ======")
    # Posts conhecidos
    for postId, p in sorted(posts.items(), key=lambda kv: kv[1].timestamp or 0):
        print(f"[POST] {postId} by {p.author} @ts={p.timestamp}: {p.text}")
        # Replies conhecidas para este post
        if postId in replies and replies[postId]:
            for r in sorted(replies[postId], key=lambda e: e.timestamp or 0):
                print(f"  [REPLY] {r.evtId} by {r.author} @ts={r.timestamp}: {r.text}")
    # Órfãs
    if orphans:
        print("---- Orphans ----")
        for parent, lst in orphans.items():
            for r in lst:
                print(f"[ORPHAN] reply {r.evtId} -> parent {parent} by {r.author}: {r.text}")
    print("====== END FEED ======\n")


if __name__ == "__main__":
    # Ler myProcessId
    if len(sys.argv) < 2:
        print("Usage: python app.py <myProcessId>")
        sys.exit(1)
    myProcessId = int(sys.argv[1])

    host, port = processes[myProcessId].split(":")
    uvicorn.run(app, host=host, port=int(port))
