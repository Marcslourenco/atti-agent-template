# 🚀 Guia de Deployment

Instruções passo a passo para fazer deploy do seu agente em produção.

---

## Pré-requisitos

- Node.js 20+
- Python 3.10+
- Git
- Modal CLI (`pip install modal`)
- Netlify CLI (`npm install -g netlify-cli`)
- Contas criadas:
  - GitHub
  - Modal.com
  - Netlify

---

## 1. Preparação Inicial

### 1.1 Clonar Template

```bash
git clone https://github.com/Marcslourenco/atti-agent-template.git
cd atti-agent-template
```

### 1.2 Criar Repositório Próprio

```bash
# Criar novo repositório no GitHub
# https://github.com/new

# Renomear remote
git remote remove origin
git remote add origin https://github.com/seu-usuario/seu-agente.git

# Push inicial
git branch -M main
git push -u origin main
```

### 1.3 Instalar Dependências

```bash
# Frontend
cd frontend
npm install
cd ..

# Backend
cd backend
pip install -r requirements.txt
cd ..
```

---

## 2. Preparar Base de Conhecimento

### 2.1 Adicionar Dados

```bash
# Editar data/questions.json com seus dados
nano data/questions.json
```

### 2.2 Gerar Embeddings

```bash
cd backend
python orchestrator/generate_embeddings.py
cd ..
```

Isso cria `backend/orchestrator/faiss_index.pkl`

---

## 3. Deploy do Backend (Modal)

### 3.1 Autenticar no Modal

```bash
# Instalar Modal CLI
pip install modal

# Criar token
modal token new

# Seguir instruções para autenticar
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env no backend
cd backend
cat > .env << EOF
MODEL_LLM=nvidia/nemotron-3-nano-30b
MODEL_ASR=whisper-large-v3
MODEL_TTS=pyttsx3
FAISS_INDEX_PATH=./faiss_index.pkl
EOF
cd ..
```

### 3.3 Deploy Orquestrador

```bash
cd backend/orchestrator
modal deploy modal_orchestrator_api.py
cd ../..
```

**Saída esperada:**
```
✓ Created app 'seu-app-orchestrator-api'
✓ App URL: https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run
```

**Salve a URL!** Você vai precisar dela.

### 3.4 Deploy Voice Pipeline

```bash
cd backend/voice_pipeline
modal deploy modal_voice_pipeline.py
cd ../..
```

**Saída esperada:**
```
✓ Created app 'seu-app-voice-pipeline'
✓ App URL: https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run
```

**Salve a URL!** Você vai precisar dela.

### 3.5 Testar Backend

```bash
# Testar Orquestrador
curl -X POST https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, como você funciona?"}'

# Resposta esperada:
# {"response": "Sou um assistente inteligente...", "sources": [...]}
```

---

## 4. Deploy do Frontend (Netlify)

### 4.1 Configurar Variáveis de Ambiente

```bash
cd frontend

# Criar arquivo .env.production
cat > .env.production << EOF
VITE_APP_NAME=Meu Agente
VITE_APP_DESCRIPTION=Um agente conversacional inteligente
VITE_PRIMARY_COLOR=#2563eb
VITE_API_BASE_URL=https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run
VITE_VOICE_API_URL=https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run
EOF

cd ..
```

### 4.2 Build Local

```bash
cd frontend
npm run build
cd ..
```

**Saída esperada:**
```
✓ built in 10.07s
dist/index.html                            367.80 kB │ gzip: 105.59 kB
dist/assets/index-B7tqg8z0.css             117.51 kB │ gzip:  18.82 kB
dist/assets/index-DJgZjEoN.js            1,789.83 kB │ gzip: 533.88 kB
```

### 4.3 Autenticar no Netlify

```bash
# Login
netlify login

# Seguir instruções no navegador
```

### 4.4 Deploy

```bash
cd frontend

# Deploy em staging (teste)
netlify deploy --dir=dist

# Deploy em produção
netlify deploy --prod --dir=dist

cd ..
```

**Saída esperada:**
```
✓ Site deployed to https://seu-agente.netlify.app
```

### 4.5 Testar Frontend

Acesse a URL do Netlify e teste:
- Chat de texto
- Chat de voz
- Gravação e reprodução de áudio

---

## 5. Configurar Domínio Personalizado (Opcional)

### 5.1 Netlify

```bash
# Adicionar domínio
netlify domain add seu-dominio.com

# Configurar DNS (seguir instruções)
```

### 5.2 Verificar

```bash
# Testar domínio
curl https://seu-dominio.com
```

---

## 6. Configurar CI/CD (Opcional)

### 6.1 GitHub Actions

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Frontend
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
        run: |
          cd frontend
          npm install
          npm run build
          netlify deploy --prod --dir=dist
          
      - name: Deploy Backend
        env:
          MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
          MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
        run: |
          cd backend
          pip install modal
          modal deploy orchestrator/modal_orchestrator_api.py
          modal deploy voice_pipeline/modal_voice_pipeline.py
```

### 6.2 Configurar Secrets

```bash
# No GitHub:
# Settings → Secrets and variables → Actions

# Adicionar:
# - NETLIFY_AUTH_TOKEN
# - NETLIFY_SITE_ID
# - MODAL_TOKEN_ID
# - MODAL_TOKEN_SECRET
```

---

## 7. Monitoramento

### 7.1 Modal Logs

```bash
# Ver logs do Orquestrador
modal logs seu-app-orchestrator-api

# Ver logs do Voice Pipeline
modal logs seu-app-voice-pipeline
```

### 7.2 Netlify Analytics

```bash
# Acessar dashboard
netlify open --admin
```

### 7.3 Health Checks

```bash
# Verificar status do Orquestrador
curl https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run/health

# Verificar status do Voice Pipeline
curl https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run/health
```

---

## 8. Troubleshooting

### Problema: Modal Deploy Falha

**Solução:**
```bash
# Verificar autenticação
modal token show

# Verificar logs
modal logs seu-app

# Tentar novamente
modal deploy --force modal_orchestrator_api.py
```

### Problema: Netlify Build Falha

**Solução:**
```bash
# Verificar build local
cd frontend
npm run build

# Verificar dependências
npm install

# Verificar variáveis de ambiente
cat .env.production
```

### Problema: Frontend não conecta ao Backend

**Solução:**
1. Verificar URLs no `.env.production`
2. Verificar CORS no backend
3. Testar com curl:
```bash
curl -X POST https://seu-orquestrador.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "teste"}'
```

### Problema: ASR não funciona

**Solução:**
1. Verificar se o áudio é válido (WAV/MP3)
2. Verificar modelo Whisper está baixado
3. Testar com arquivo de áudio:
```bash
curl -X POST https://seu-voice-pipeline.modal.run/process-audio \
  -F "file=@test.wav"
```

---

## 9. Checklist Final

- [ ] Base de conhecimento preparada
- [ ] Embeddings FAISS gerados
- [ ] Backend deployado no Modal
- [ ] Frontend deployado no Netlify
- [ ] URLs configuradas corretamente
- [ ] Chat de texto testado
- [ ] Chat de voz testado
- [ ] Domínio personalizado configurado (opcional)
- [ ] CI/CD configurado (opcional)
- [ ] Monitoramento ativo

---

## 10. Próximas Etapas

1. ✅ Monitorar performance
2. ✅ Coletar feedback de usuários
3. ✅ Iterar e melhorar
4. ✅ Adicionar novas features
5. ✅ Escalar conforme necessário

---

## URLs Importantes

| Serviço | URL |
|---------|-----|
| GitHub | https://github.com/seu-usuario/seu-agente |
| Netlify | https://seu-agente.netlify.app |
| Orquestrador Modal | https://seu-usuario--seu-app-orchestrator-api-fastapi-app.modal.run |
| Voice Pipeline Modal | https://seu-usuario--seu-app-voice-pipeline-fastapi-app.modal.run |

---

**Pronto para produção!** 🚀

Se tiver dúvidas, consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md) ou abra uma issue no GitHub.
