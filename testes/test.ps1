# Teste 1: criar post em replica 1 (autor Levi)
Invoke-RestMethod -Uri "http://localhost:8081/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 1,
    "evtId": "p-001",
    "author": "Levi",
    "text": "Ola mundo",
    "parentEvtId": null
  }'

# Teste 2: criar reply em replica 0 (autor Pedro)
Invoke-RestMethod -Uri "http://localhost:8080/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 0,
    "evtId": "r-001",
    "author": "Pedro",
    "text": "Bom dia",
    "parentEvtId": "p-001"
  }'

# Teste 3: criar outro post em replica 2 (autor Lele)
Invoke-RestMethod -Uri "http://localhost:8082/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 2,
    "evtId": "p-002",
    "author": "Lele",
    "text": "Post de teste",
    "parentEvtId": null
  }'

# Teste 4: reply para segundo post (autor Levi)
Invoke-RestMethod -Uri "http://localhost:8081/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 1,
    "evtId": "r-002",
    "author": "Levi",
    "text": "Reply de Levi para p-002",
    "parentEvtId": "p-002"
  }'

# Teste 5: reply antes do post (autor Pedro)
Invoke-RestMethod -Uri "http://localhost:8080/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 0,
    "evtId": "r-003",
    "author": "Pedro",
    "text": "Reply antes do post p-003",
    "parentEvtId": "p-003"
  }'

# Depois criar o post em replica 2 (autor Lele)
Invoke-RestMethod -Uri "http://localhost:8082/post" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{
    "processId": 2,
    "evtId": "p-003",
    "author": "Lele",
    "text": "Post que chega depois do reply",
    "parentEvtId": null
  }'
