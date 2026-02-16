# 🔧 Troubleshooting

Problemas comuns e soluções.

---

## Frontend

### Problema: Página em branco

**Causa:** Build falhou ou assets não carregaram

**Solução:**
```bash
cd frontend
npm install
npm run build
npm run dev
```

Verificar console do navegador (F12) para erros.

### Problema: Chat não conecta ao backend

**Causa:** URL do backend incorreta ou CORS bloqueado

**Solução:**
1. Verificar `.env.production`:
```env
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run
```

2. Testar conexão:
```bash
curl -X POST https://seu-orquestrador.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "teste"}'
```

3. Se falhar, verificar CORS no backend:
```python
# backend/orchestrator/modal_orchestrator_api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problema: Áudio não funciona

**Causa:** Navegador não suporta MediaRecorder ou permissão negada

**Solução:**
1. Usar navegador moderno (Chrome, Firefox, Safari)
2. Verificar permissão de microfone
3. Testar em HTTPS (Netlify já é HTTPS)

### Problema: Tema escuro não funciona

**Causa:** ThemeProvider não está configurado

**Solução:**
```tsx
// frontend/src/App.tsx
import { ThemeProvider } from '@/components/theme-provider';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      {/* ... */}
    </ThemeProvider>
  );
}
```

---

## Backend - Orquestrador

### Problema: Deploy falha

**Causa:** Dependências faltando ou erro de sintaxe

**Solução:**
```bash
# Verificar dependências
pip install -r backend/requirements.txt

# Testar localmente
cd backend
modal serve orchestrator/modal_orchestrator_api.py

# Verificar erros
modal logs seu-app
```

### Problema: Respostas ruins

**Causa:** Base de conhecimento fraca ou prompt ruim

**Solução:**
1. Verificar qualidade de `data/questions.json`
2. Ajustar prompt em `modal_orchestrator_api.py`:
```python
SYSTEM_PROMPT = """
Você é um assistente especializado em [seu domínio].
Responda de forma clara e profissional.
Se não souber, diga "Não tenho informação sobre isso".
"""
```

3. Testar com modelo LLM mais poderoso:
```python
MODEL_LLM = "meta-llama/llama-2-70b"
```

### Problema: Embeddings não carregam

**Causa:** Arquivo `faiss_index.pkl` faltando ou corrompido

**Solução:**
```bash
cd backend
python orchestrator/generate_embeddings.py
cd ..
```

Verificar se o arquivo foi criado:
```bash
ls -la backend/orchestrator/faiss_index.pkl
```

### Problema: Timeout na resposta

**Causa:** LLM está lento ou base de conhecimento muito grande

**Solução:**
1. Usar modelo LLM mais rápido:
```python
MODEL_LLM = "mistralai/mistral-7b"
```

2. Reduzir número de resultados FAISS:
```python
TOP_K = 3  # Em vez de 5
```

3. Aumentar timeout:
```python
TIMEOUT = 30  # Em segundos
```

### Problema: Erro 500 no endpoint

**Causa:** Erro não tratado no código

**Solução:**
```bash
# Ver logs
modal logs seu-app

# Procurar por "Traceback" ou "Error"
# Corrigir erro e fazer deploy novamente
modal deploy orchestrator/modal_orchestrator_api.py
```

---

## Backend - Voice Pipeline

### Problema: ASR não reconhece áudio

**Causa:** Áudio de baixa qualidade ou idioma errado

**Solução:**
1. Verificar qualidade do áudio:
   - Usar microfone de boa qualidade
   - Falar claramente
   - Evitar ruído de fundo

2. Testar com arquivo de áudio:
```bash
curl -X POST https://seu-voice-pipeline.modal.run/process-audio \
  -F "file=@test.wav"
```

3. Usar Whisper Medium (mais rápido):
```python
# backend/asr/modal_asr_whisper.py
MODEL_ASR = "whisper-medium"
```

### Problema: TTS não gera áudio

**Causa:** pyttsx3 não inicializado ou erro de sintaxe

**Solução:**
```bash
# Testar localmente
cd backend
python -c "import pyttsx3; pyttsx3.init()"

# Ver logs
modal logs seu-app-voice-pipeline
```

### Problema: Voice Pipeline muito lento

**Causa:** Latência de rede ou modelos pesados

**Solução:**
1. Usar modelos mais rápidos:
```python
MODEL_ASR = "whisper-small"  # Em vez de large-v3
MODEL_LLM = "mistralai/mistral-7b"  # Em vez de nemotron
```

2. Aumentar recursos Modal:
```python
@app.function(memory=2048, timeout=30)
def process_audio(audio: bytes):
    ...
```

### Problema: Erro de CORS no voice pipeline

**Causa:** Frontend não pode chamar voice pipeline

**Solução:**
```python
# backend/voice_pipeline/modal_voice_pipeline.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment

### Problema: Netlify build falha

**Causa:** Dependências faltando ou erro de build

**Solução:**
```bash
# Testar build local
cd frontend
npm install
npm run build

# Verificar erros
npm run build 2>&1 | tail -50

# Limpar cache
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Problema: Modal deploy falha

**Causa:** Token expirado ou erro de autenticação

**Solução:**
```bash
# Verificar token
modal token show

# Renovar token
modal token new

# Tentar deploy novamente
modal deploy --force orchestrator/modal_orchestrator_api.py
```

### Problema: Domínio não funciona

**Causa:** DNS não configurado ou propagação lenta

**Solução:**
1. Verificar DNS:
```bash
nslookup seu-dominio.com
```

2. Aguardar propagação (até 48h)

3. Testar com IP:
```bash
curl https://seu-dominio.com
```

---

## Performance

### Latência Alta

**Causa:** Rede lenta, modelos pesados ou base de conhecimento grande

**Solução:**
1. Medir latência:
```bash
time curl -X POST https://seu-orquestrador.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "teste"}'
```

2. Otimizar:
   - Usar modelos menores
   - Reduzir TOP_K em FAISS
   - Aumentar recursos Modal

### Taxa de Erro Alta

**Causa:** Modelos instáveis ou base de conhecimento ruim

**Solução:**
1. Monitorar erros:
```bash
modal logs seu-app | grep -i error
```

2. Melhorar base de conhecimento
3. Usar modelo LLM mais robusto

---

## Segurança

### Problema: Tokens expostos

**Causa:** Tokens em arquivo `.env` commitado

**Solução:**
```bash
# Adicionar .env ao .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# Remover arquivo do git
git rm --cached .env
git commit -m "Remove .env"

# Renovar tokens
modal token new
netlify login
```

### Problema: CORS muito permissivo

**Causa:** `allow_origins=["*"]` permite qualquer origem

**Solução:**
```python
# Restringir a origens específicas
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seu-agente.netlify.app",
        "https://seu-dominio.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

---

## Debugging

### Ativar Logs Detalhados

**Frontend:**
```tsx
// frontend/src/services/chatService.ts
console.log('Enviando:', message);
console.log('Resposta:', response);
```

**Backend:**
```python
# backend/orchestrator/modal_orchestrator_api.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Pergunta: {message}")
```

### Testar com cURL

```bash
# Chat
curl -X POST https://seu-orquestrador.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá"}'

# Voice
curl -X POST https://seu-voice-pipeline.modal.run/process-audio-base64 \
  -H "Content-Type: application/json" \
  -d '{"audio": "base64_audio_data"}'

# Health
curl https://seu-orquestrador.modal.run/health
```

---

## Suporte

Se o problema persistir:

1. 📖 Consulte a [Documentação](ARCHITECTURE.md)
2. 🐛 Abra uma [Issue no GitHub](https://github.com/Marcslourenco/atti-agent-template/issues)
3. 💬 Participe das [Discussões](https://github.com/Marcslourenco/atti-agent-template/discussions)

---

**Boa sorte! 🚀**
