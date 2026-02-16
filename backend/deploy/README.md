# 🚀 Deploy Scripts

Scripts para fazer deploy do backend no Modal.

---

## Pré-requisitos

- Modal CLI: `pip install modal`
- Autenticação: `modal token new`

---

## Deploy Orquestrador

```bash
bash deploy_orchestrator.sh
```

Faz deploy de `modal_orchestrator_api.py` no Modal.

**Saída esperada:**
```
✓ Created app 'seu-app-orchestrator-api'
✓ App URL: https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run
```

---

## Deploy Voice Pipeline

```bash
bash deploy_voice_pipeline.sh
```

Faz deploy de `modal_voice_pipeline.py` no Modal.

**Saída esperada:**
```
✓ Created app 'seu-app-voice-pipeline'
✓ App URL: https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run
```

---

## Testar Após Deploy

### Orquestrador

```bash
curl -X POST https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá"}'
```

### Voice Pipeline

```bash
curl -X POST https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run/health
```

---

## Troubleshooting

### Deploy falha

```bash
# Verificar autenticação
modal token show

# Renovar token
modal token new

# Tentar deploy novamente
modal deploy --force modal_orchestrator_api.py
```

### Ver logs

```bash
modal logs seu-app
```

---

**Pronto para deploy!** 🚀
