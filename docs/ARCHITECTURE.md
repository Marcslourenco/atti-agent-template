# 🏗️ Arquitetura do ATTI Agent Template

## Visão Geral

O template ATTI é um sistema de agente conversacional multimodal que combina:

- **Chat de Texto** - Integração com LLM para respostas contextualizadas
- **Chat de Voz** - ASR (reconhecimento de fala) + TTS (síntese de fala)
- **RAG (Retrieval-Augmented Generation)** - Busca semântica em base de conhecimento
- **Deploy Automatizado** - Netlify + Modal.com

---

## Componentes Principais

### 1. Frontend (React + Vite)

**Localização:** `frontend/`

**Responsabilidades:**
- Interface de usuário para chat de texto e voz
- Gravação e reprodução de áudio
- Comunicação com backend APIs
- Temas e customização visual

**Componentes Principais:**
- `ChatWidget.tsx` - Widget de chat de texto
- `VoiceWidget.tsx` - Widget de chat de voz
- `App.tsx` - Aplicação principal
- `services/chatService.ts` - Integração com orquestrador
- `services/voiceService.ts` - Integração com voice pipeline

**Stack:**
- React 19
- TypeScript
- Vite 7.3.1
- Tailwind CSS 4
- shadcn/ui

---

### 2. Backend - Orquestrador (FastAPI + Modal)

**Localização:** `backend/orchestrator/`

**Responsabilidades:**
- Receber perguntas do usuário
- Buscar respostas relevantes na base de conhecimento (FAISS)
- Gerar respostas contextualizadas com LLM
- Retornar resposta ao frontend

**Fluxo:**

```
Pergunta do Usuário
        ↓
Gerar Embedding (384 dimensões)
        ↓
Buscar em FAISS (Top-K resultados)
        ↓
Construir Prompt com contexto
        ↓
Chamar LLM (Nemotron 3 Nano)
        ↓
Retornar Resposta
```

**Endpoints:**
- `POST /chat` - Chat de texto
- `POST /query` - Busca semântica
- `GET /health` - Health check

**Latência Típica:** ~400ms

---

### 3. Backend - Voice Pipeline (FastAPI + Modal)

**Localização:** `backend/voice_pipeline/`

**Responsabilidades:**
- Receber áudio do usuário
- Transcrever áudio para texto (ASR)
- Chamar orquestrador para gerar resposta
- Sintetizar resposta em áudio (TTS)
- Retornar áudio ao frontend

**Fluxo:**

```
Áudio do Usuário (WAV/MP3)
        ↓
ASR (Whisper Large-V3) ~800ms
        ↓
Transcrição de Texto
        ↓
Chamar Orquestrador ~400ms
        ↓
Resposta de Texto
        ↓
TTS (pyttsx3) ~300ms
        ↓
Áudio de Resposta (base64)
```

**Endpoints:**
- `POST /process-audio` - Processar áudio (WAV)
- `POST /process-audio-base64` - Processar áudio (base64)
- `GET /health` - Health check

**Latência Total:** ~1.5-2 segundos

---

### 4. Busca Semântica (FAISS)

**Localização:** `backend/orchestrator/`

**Responsabilidades:**
- Indexar base de conhecimento em embeddings
- Buscar respostas relevantes por similaridade semântica
- Otimizar performance de busca

**Características:**
- Embeddings de 384 dimensões
- Busca rápida em bases grandes
- Suporte a múltiplos idiomas

**Geração de Embeddings:**

```bash
python backend/orchestrator/generate_embeddings.py
```

Isso cria um arquivo `faiss_index.pkl` com o índice otimizado.

---

### 5. Modelos de IA

#### LLM (Large Language Model)

**Padrão:** Nvidia Nemotron 3 Nano (30B)

**Responsabilidades:**
- Gerar respostas contextualizadas
- Entender intenção do usuário
- Formatar respostas de forma clara

**Customização:**
```python
# backend/orchestrator/modal_orchestrator_api.py
MODEL_LLM = "nvidia/nemotron-3-nano-30b"
# Ou trocar por outro modelo:
# MODEL_LLM = "meta-llama/llama-2-70b"
# MODEL_LLM = "mistralai/mistral-7b"
```

#### ASR (Automatic Speech Recognition)

**Padrão:** OpenAI Whisper Large-V3

**Responsabilidades:**
- Transcrever áudio para texto
- Suportar 99+ idiomas
- Detectar idioma automaticamente

**Customização:**
```python
# backend/asr/modal_asr_whisper.py
MODEL_ASR = "whisper-large-v3"
# Ou trocar por:
# MODEL_ASR = "whisper-medium"
# MODEL_ASR = "whisper-small"
```

#### TTS (Text-to-Speech)

**Padrão:** pyttsx3

**Responsabilidades:**
- Sintetizar texto em áudio
- Suportar múltiplas vozes
- Ajustar velocidade e tom

**Customização:**
```python
# backend/tts/modal_tts_pyttsx3.py
VOICE_RATE = 150  # Velocidade
VOICE_VOLUME = 1.0  # Volume
VOICE_ID = 0  # Voz (0=masculina, 1=feminina)
```

---

## Fluxo de Dados Completo

### Chat de Texto

```
┌─────────────────────────────────────────────────────┐
│ 1. Usuário digita pergunta no ChatWidget            │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 2. Frontend envia POST /chat para Orquestrador      │
│    {                                                 │
│      "message": "Qual é a política de férias?"     │
│    }                                                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 3. Orquestrador:                                    │
│    - Gera embedding da pergunta                     │
│    - Busca em FAISS (Top-5 resultados)              │
│    - Monta prompt com contexto                      │
│    - Chama LLM (Nemotron)                           │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 4. Orquestrador retorna resposta:                   │
│    {                                                 │
│      "response": "A política de férias é...",      │
│      "sources": [...]                               │
│    }                                                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 5. Frontend exibe resposta no ChatWidget            │
└─────────────────────────────────────────────────────┘
```

**Latência Total:** ~400ms

### Chat de Voz

```
┌─────────────────────────────────────────────────────┐
│ 1. Usuário clica "Gravar" no VoiceWidget            │
│    MediaRecorder captura áudio                      │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 2. Frontend envia POST /process-audio-base64        │
│    com áudio em base64                              │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 3. Voice Pipeline:                                  │
│    - Decodifica áudio (base64 → WAV)                │
│    - Chama ASR (Whisper) ~800ms                     │
│    - Obtém transcrição                              │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 4. Voice Pipeline:                                  │
│    - Chama Orquestrador com transcrição ~400ms      │
│    - Obtém resposta                                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 5. Voice Pipeline:                                  │
│    - Chama TTS (pyttsx3) ~300ms                     │
│    - Gera áudio de resposta                         │
│    - Codifica em base64                             │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 6. Voice Pipeline retorna:                          │
│    {                                                 │
│      "transcription": "Qual é a política...",      │
│      "response": "A política de férias é...",      │
│      "audio": "base64_encoded_audio"                │
│    }                                                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ 7. Frontend:                                        │
│    - Decodifica áudio                               │
│    - Reproduz com player                            │
│    - Exibe transcrição e resposta                   │
└─────────────────────────────────────────────────────┘
```

**Latência Total:** ~1.5-2 segundos

---

## Deployment

### Frontend (Netlify)

```
Git Push
   ↓
GitHub Webhook
   ↓
Netlify Build (npm run build)
   ↓
Deploy em CDN Global
   ↓
URL Pública: https://seu-agente.netlify.app
```

### Backend (Modal)

```
Deploy Script
   ↓
Modal CLI Upload
   ↓
Container Serverless
   ↓
URL Pública: https://seu-orquestrador.modal.run
```

---

## Performance

| Métrica | Valor | Gargalo |
|---------|-------|---------|
| Latência Chat (Texto) | ~400ms | Orquestrador |
| Latência Voice (Voz) | ~1.5-2s | ASR (Whisper) |
| Taxa de Sucesso | >99% | - |
| Requisições Simultâneas | até 5 | Modal |
| Suporte de Idiomas | 99+ | Whisper |

---

## Segurança

- ✅ CORS configurado corretamente
- ✅ Validação de entrada
- ✅ Rate limiting (Modal)
- ✅ Tokens em variáveis de ambiente
- ✅ HTTPS em produção

---

## Escalabilidade

- **Frontend:** CDN Global (Netlify)
- **Backend:** Serverless (Modal) - escala automaticamente
- **Busca:** FAISS em memória - otimizado para até 1M documentos
- **Concorrência:** até 5 requisições simultâneas por padrão

---

## Próximas Melhorias

- [ ] Streaming de áudio (ASR em tempo real)
- [ ] Cache de respostas
- [ ] Análise de sentimento
- [ ] Dashboard de monitoramento
- [ ] Autenticação de usuários
- [ ] Analytics e logging
