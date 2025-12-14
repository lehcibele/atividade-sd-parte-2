# Twitter Distribuido - Consistência Eventual e Causal

Este projeto implementa duas versões simplificadas de um "Twitter distribuído" usando **FastAPI**:

- **Consistência Eventual:** aceita qualquer ordem de chegada. Replies podem aparecer órfãs até que o post pai seja recebido.
- **Consistência Causal:** usa relógios vetoriais e um buffer para garantir que mensagens só sejam entregues quando suas dependências forem satisfeitas, evitando replies órfãs.

## ⚙️ Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/atividade-sd-parte-2.git
```

2. Entre na pasta do projeto:
```bash
cd atividade-sd-parte-2
```

3. Crie o ambiente virtual:
```bash
python -m venv .venv
```

4. Ative o ambiente virtual:
```bash
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate # Windows PowerShell
```

5. Instale as dependências: 
```
pip install -r requirements.txt
```

## 🚀 Como Executar

### Versão Eventual
- Abra 3 terminais e rode:
```bash
cd eventual
python app.py 0
python app.py 1
python app.py 2
```

### Versão Causal
- Abra 3 terminais e rode:
```bash
cd causal
python app.py 0
python app.py 1
python app.py 2
```

## 🧪 Testes Simples

### Criar um post
```bash
Invoke-RestMethod -Uri "http://localhost:8081/post" `
  -Method POST -ContentType "application/json" `
  -Body '{
    "processId": 1,
    "evtId": "p-001",
    "author": "Levi",
    "text": "Ola mundo",
    "parentEvtId": null
  }'
```

### Criar uma reply
```bash
Invoke-RestMethod -Uri "http://localhost:8080/post" `
  -Method POST -ContentType "application/json" `
  -Body '{
    "processId": 0,
    "evtId": "r-001",
    "author": "Pedro",
    "text": "Bom dia",
    "parentEvtId": "p-001"
  }'
```

## 📜 Testes completos
- Script de testes:
```bash
testes/test.ps1
```


