# 🤖 ATTI Agent Template

Um template reutilizável para criar **agentes conversacionais multimodais** (texto + voz) com suporte a RAG (Retrieval-Augmented Generation), LLM e busca semântica.

> **Baseado no projeto ATTI** - Um agente contador especializado em Reforma Tributária 2026, agora transformado em um template genérico para qualquer domínio.

---

## ✨ Características Principais

- ✅ **Chat de Texto** - Integração com LLM (Nemotron 3 Nano)
- ✅ **Chat de Voz** - ASR (Whisper Large-V3) + TTS (pyttsx3)
- ✅ **Busca Semântica** - FAISS com embeddings de 384 dimensões
- ✅ **RAG (Retrieval-Augmented Generation)** - Base de conhecimento customizável
- ✅ **Frontend Moderno** - React 19 + TypeScript + Tailwind CSS 4
- ✅ **Deploy Automatizado** - Netlify (frontend) + Modal (backend)
- ✅ **Suporte a 99+ Idiomas** - Via Whisper
- ✅ **Latência Otimizada** - ~400ms para texto, ~1.5-2s para voz

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + Vite)                │
│  ChatWidget (Texto) + VoiceWidget (Voz)             │
│         Deploy: Netlify                             │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│  Orquestrador    │  │ Voice Pipeline   │
│  (FastAPI)       │  │ (FastAPI)        │
│  - LLM           │  │ - ASR (Whisper)  │
│  - RAG (FAISS)   │  │ - TTS (pyttsx3)  │
│  Deploy: Modal   │  │ Deploy: Modal    │
└──────────────────┘  └──────────────────┘
```

---

## 🚀 Quick Start (5 minutos)

### Pré-requisitos

- Node.js 20+
- Python 3.10+
- Modal CLI (`pip install modal`)
- Netlify CLI (`npm install -g netlify-cli`)
- Git

### 1. Clonar o Template

```bash
git clone https://github.com/Marcslourenco/atti-agent-template.git
cd atti-agent-template
```

### 2. Instalar Dependências

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

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Frontend
VITE_APP_NAME=Meu Agente
VITE_APP_DESCRIPTION=Um agente conversacional inteligente
VITE_PRIMARY_COLOR=#2563eb
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run

# Backend
MODEL_LLM=nvidia/nemotron-3-nano-30b
MODEL_ASR=whisper-large-v3
MODEL_TTS=pyttsx3
MODAL_API_KEY=seu_modal_api_key
```

### 4. Substituir Base de Conhecimento

```bash
# Coloque seus dados em data/questions.json
# Formato:
# [
#   {"question": "...", "answer": "..."},
#   {"question": "...", "answer": "..."}
# ]

# Gerar embeddings FAISS
python backend/orchestrator/generate_embeddings.py
```

### 5. Deploy do Backend (Modal)

```bash
cd backend
bash deploy/deploy_orchestrator.sh
bash deploy/deploy_voice_pipeline.sh
cd ..
```

### 6. Deploy do Frontend (Netlify)

```bash
cd frontend
npm run build
netlify deploy --prod --dir=dist
cd ..
```

### 7. Testar!

Acesse a URL do Netlify e comece a usar seu agente! 🎉

---

## 📚 Documentação Completa

| Documento | Descrição |
|-----------|-----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Visão geral da arquitetura |
| [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) | Guia passo a passo para customizar |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Como fazer deploy (Netlify + Modal) |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Problemas comuns e soluções |
| [backend/README.md](backend/README.md) | Documentação do backend |
| [frontend/README.md](frontend/README.md) | Documentação do frontend |

---

## 🎯 Exemplos de Uso

### Criar um Agente de RH

1. Clone o template
2. Substitua `data/questions.json` com Q&As sobre políticas de RH
3. Customize o frontend com cores da empresa
4. Deploy em 30 minutos!

### Criar um Agente Jurídico

1. Clone o template
2. Adicione base de conhecimento jurídico
3. Ajuste prompts do LLM para contexto jurídico
4. Deploy em 1 hora!

### Criar um Agente de Suporte

1. Clone o template
2. Integre com sua base de conhecimento de suporte
3. Customize widgets de chat
4. Deploy em 1 dia!

---

## 🔧 Personalização Rápida

### Mudar Cores

Edite `frontend/src/index.css`:

```css
@layer base {
  :root {
    --primary: 37 99 235; /* Azul */
    --secondary: 168 85 247; /* Roxo */
    --accent: 59 130 246; /* Azul claro */
  }
}
```

### Mudar Logo

Coloque sua logo em `frontend/public/logo.png` e atualize `frontend/src/App.tsx`

### Mudar Modelos

Edite `backend/orchestrator/modal_orchestrator_api.py`:

```python
MODEL_LLM = "meta-llama/llama-2-70b"  # Trocar modelo LLM
MODEL_ASR = "openai/whisper-medium"  # Trocar ASR
MODEL_TTS = "elevenlabs"  # Trocar TTS
```

---

## 📊 Performance

| Métrica | Valor |
|---------|-------|
| Latência Chat (Texto) | ~400ms |
| Latência Voice (Voz) | ~1.5-2s |
| Taxa de Sucesso | >99% |
| Suporte de Idiomas | 99+ |
| Requisições Simultâneas | até 5 |

---

## 🛠️ Stack Tecnológico

| Componente | Tecnologia |
|-----------|-----------|
| Frontend | React 19 + TypeScript + Vite 7.3.1 |
| Estilos | Tailwind CSS 4 + shadcn/ui |
| Backend | Python 3.10+ + FastAPI |
| Deploy Frontend | Netlify |
| Deploy Backend | Modal.com |
| LLM | Nvidia Nemotron 3 Nano |
| ASR | OpenAI Whisper Large-V3 |
| TTS | pyttsx3 |
| Busca Semântica | FAISS (384 dimensões) |

---

## 📝 Estrutura de Diretórios

```
atti-agent-template/
├── backend/                          # Backend (Modal)
│   ├── orchestrator/
│   │   ├── modal_orchestrator_api.py
│   │   ├── generate_embeddings.py
│   │   └── requirements.txt
│   ├── asr/
│   │   ├── modal_asr_interface.py
│   │   ├── modal_asr_whisper.py
│   │   └── README.md
│   ├── tts/
│   │   ├── modal_tts_interface.py
│   │   ├── modal_tts_pyttsx3.py
│   │   └── README.md
│   ├── voice_pipeline/
│   │   ├── modal_voice_pipeline.py
│   │   └── README.md
│   ├── deploy/
│   │   ├── deploy_orchestrator.sh
│   │   ├── deploy_voice_pipeline.sh
│   │   └── README.md
│   └── README.md
├── frontend/                         # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget.tsx
│   │   │   ├── VoiceWidget.tsx
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── chatService.ts
│   │   │   └── voiceService.ts
│   │   ├── hooks/
│   │   │   └── useMediaRecorder.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── README.md
├── data/                             # Base de Conhecimento
│   ├── README.md
│   └── sample_questions.json
├── docs/                             # Documentação
│   ├── ARCHITECTURE.md
│   ├── CUSTOMIZATION.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD (opcional)
└── README.md
```

---

## 🤝 Contribuindo

Este é um template de código aberto! Sugestões, melhorias e contribuições são bem-vindas.

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adicionar MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja [LICENSE](LICENSE) para detalhes.

---

## 🚀 Roadmap

- [ ] Suporte a mais modelos de LLM (GPT-4, Claude, etc.)
- [ ] Dashboard de monitoramento
- [ ] Análise de sentimento
- [ ] Integração com APIs externas
- [ ] Suporte a múltiplas vozes (TTS)
- [ ] Streaming de áudio (ASR em tempo real)
- [ ] Autenticação de usuários
- [ ] Analytics e logging

---

## 📞 Suporte

- 📖 [Documentação Completa](docs/)
- 🐛 [Reportar Issues](https://github.com/Marcslourenco/atti-agent-template/issues)
- 💬 [Discussões](https://github.com/Marcslourenco/atti-agent-template/discussions)

---

## 🙏 Agradecimentos

Template criado baseado no projeto **ATTI** - Um agente contador especializado em Reforma Tributária 2026.

**Desenvolvido com ❤️ por [Marcslourenco](https://github.com/Marcslourenco)**

---

**Transforme sua ideia em um agente conversacional inteligente em dias, não meses! 🚀**
