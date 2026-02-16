# 🔧 Backend

Backend do agente conversacional com orquestrador LLM e voice pipeline.

---

## Estrutura

```
backend/
├── orchestrator/              # Orquestrador LLM + RAG
│   ├── modal_orchestrator_api.py
│   ├── generate_embeddings.py
│   └── requirements.txt
├── asr/                       # Automatic Speech Recognition
│   ├── modal_asr_interface.py
│   ├── modal_asr_whisper.py
│   └── README.md
├── tts/                       # Text-to-Speech
│   ├── modal_tts_interface.py
│   ├── modal_tts_pyttsx3.py
│   └── README.md
├── voice_pipeline/            # Pipeline completo (ASR → Orq → TTS)
│   ├── modal_voice_pipeline.py
│   └── README.md
├── deploy/                    # Scripts de deployment
│   ├── deploy_orchestrator.sh
│   ├── deploy_voice_pipeline.sh
│   └── README.md
└── requirements.txt           # Dependências Python
```

---

## Instalação

```bash
cd backend
pip install -r requirements.txt
```

---

## Componentes

### 1. Orquestrador

Responsável por:
- Receber perguntas do usuário
- Buscar respostas relevantes em FAISS
- Gerar respostas com LLM
- Retornar resposta ao frontend

**Endpoints:**
- `POST /chat` - Chat de texto
- `POST /query` - Busca semântica
- `GET /health` - Health check

**Testar:**
```bash
modal serve orchestrator/modal_orchestrator_api.py
```

### 2. Voice Pipeline

Responsável por:
- Receber áudio do usuário
- Transcrever com ASR (Whisper)
- Chamar orquestrador
- Sintetizar resposta com TTS

**Endpoints:**
- `POST /process-audio` - Processar áudio (WAV)
- `POST /process-audio-base64` - Processar áudio (base64)
- `GET /health` - Health check

**Testar:**
```bash
modal serve voice_pipeline/modal_voice_pipeline.py
```

### 3. ASR (Whisper)

Transcreve áudio em texto com suporte a 99+ idiomas.

**Configuração:**
```python
# backend/asr/modal_asr_whisper.py
MODEL_ASR = "whisper-large-v3"  # Mais preciso
# MODEL_ASR = "whisper-medium"  # Mais rápido
```

### 4. TTS (pyttsx3)

Sintetiza texto em áudio.

**Configuração:**
```python
# backend/tts/modal_tts_pyttsx3.py
VOICE_RATE = 150      # Velocidade
VOICE_VOLUME = 1.0    # Volume
VOICE_ID = 0          # Voz (0=masculina, 1=feminina)
```

---

## Variáveis de Ambiente

```env
MODEL_LLM=nvidia/nemotron-3-nano-30b
MODEL_ASR=whisper-large-v3
MODEL_TTS=pyttsx3
FAISS_INDEX_PATH=./faiss_index.pkl
MODAL_API_KEY=seu_modal_api_key
```

---

## Gerar Embeddings

```bash
cd orchestrator
python generate_embeddings.py
cd ..
```

Cria `faiss_index.pkl` com embeddings de `../data/questions.json`

---

## Deploy

### Orquestrador

```bash
cd orchestrator
modal deploy modal_orchestrator_api.py
cd ..
```

### Voice Pipeline

```bash
cd voice_pipeline
modal deploy modal_voice_pipeline.py
cd ..
```

---

## Testes

```bash
# Testar orquestrador
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá"}'

# Testar voice pipeline
curl -X POST http://localhost:8001/process-audio-base64 \
  -H "Content-Type: application/json" \
  -d '{"audio": "base64_audio"}'
```

---

## Customização

### Trocar Modelo LLM

```python
# orchestrator/modal_orchestrator_api.py
MODEL_LLM = "meta-llama/llama-2-70b"
```

### Trocar Modelo ASR

```python
# asr/modal_asr_whisper.py
MODEL_ASR = "whisper-medium"
```

### Trocar Modelo TTS

Implementar nova classe em `tts/` seguindo `modal_tts_interface.py`

---

## Performance

| Componente | Latência |
|-----------|----------|
| Orquestrador | ~400ms |
| ASR | ~800ms |
| TTS | ~300ms |
| Voice Pipeline Total | ~1.5-2s |

---

## Troubleshooting

### Embeddings não carregam
```bash
python orchestrator/generate_embeddings.py
```

### Deploy falha
```bash
modal token new
modal deploy --force orchestrator/modal_orchestrator_api.py
```

### Respostas ruins
1. Verificar qualidade de `data/questions.json`
2. Ajustar prompt em `modal_orchestrator_api.py`
3. Usar modelo LLM mais poderoso

---

## Próximas Melhorias

- [ ] Streaming de áudio (ASR em tempo real)
- [ ] Cache de respostas
- [ ] Análise de sentimento
- [ ] Suporte a múltiplas vozes
- [ ] Integração com APIs externas

---

**Pronto para começar!** 🚀
