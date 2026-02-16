# 🎨 Guia de Customização

Este guia mostra como customizar o template ATTI para seu caso de uso específico.

---

## 1. Substituir Base de Conhecimento

### Passo 1: Preparar Dados

Crie um arquivo `data/questions.json` com suas perguntas e respostas:

```json
[
  {
    "question": "Qual é a política de férias?",
    "answer": "Todos os funcionários têm direito a 30 dias de férias por ano, podendo ser fracionadas conforme acordado com o gestor."
  },
  {
    "question": "Como solicitar um dia de folga?",
    "answer": "Você pode solicitar através do sistema RH com até 10 dias de antecedência."
  },
  {
    "question": "Qual é o horário de trabalho?",
    "answer": "O horário padrão é de 9h às 18h, com 1 hora de intervalo para almoço."
  }
]
```

### Passo 2: Gerar Embeddings

```bash
cd backend
python orchestrator/generate_embeddings.py
cd ..
```

Isso cria um arquivo `faiss_index.pkl` com o índice otimizado.

### Passo 3: Fazer Deploy

```bash
cd backend
bash deploy/deploy_orchestrator.sh
cd ..
```

---

## 2. Gerar Embeddings FAISS

### O que são Embeddings?

Embeddings são representações numéricas de texto em um espaço vetorial. O FAISS usa embeddings para busca semântica rápida.

### Como Funciona

```python
# backend/orchestrator/generate_embeddings.py

from sentence_transformers import SentenceTransformer

# Carregar modelo de embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensões

# Gerar embeddings para cada pergunta
embeddings = model.encode(questions)

# Criar índice FAISS
index = faiss.IndexFlatL2(384)
index.add(embeddings)

# Salvar índice
faiss.write_index(index, 'faiss_index.pkl')
```

### Customizar Modelo de Embeddings

```python
# backend/orchestrator/generate_embeddings.py

# Mudar para modelo maior (mais preciso, mais lento)
model = SentenceTransformer('all-mpnet-base-v2')  # 768 dimensões

# Ou modelo menor (mais rápido, menos preciso)
model = SentenceTransformer('all-MiniLM-L12-v2')  # 384 dimensões
```

---

## 3. Ajustar Prompts do LLM

### Prompt Padrão

```python
# backend/orchestrator/modal_orchestrator_api.py

SYSTEM_PROMPT = """
Você é um assistente inteligente especializado em Recursos Humanos.
Responda perguntas dos funcionários de forma clara, concisa e profissional.
Use as informações fornecidas como contexto.
Se não souber a resposta, diga "Não tenho informação sobre isso".
"""

USER_PROMPT = """
Contexto:
{context}

Pergunta: {question}

Responda em português.
"""
```

### Customizar para Seu Domínio

```python
# Para agente jurídico
SYSTEM_PROMPT = """
Você é um assistente jurídico especializado em direito empresarial.
Forneça informações precisas e cite as leis relevantes.
Sempre recomende consultar um advogado para questões críticas.
"""

# Para agente de suporte técnico
SYSTEM_PROMPT = """
Você é um especialista em suporte técnico.
Forneça soluções passo a passo.
Se o problema persistir, recomende abrir um ticket.
"""

# Para agente de vendas
SYSTEM_PROMPT = """
Você é um assistente de vendas amigável e profissional.
Responda dúvidas sobre produtos e preços.
Ofereça soluções personalizadas para cada cliente.
"""
```

---

## 4. Trocar Modelos (ASR, TTS, LLM)

### Trocar Modelo LLM

```python
# backend/orchestrator/modal_orchestrator_api.py

# Padrão: Nemotron 3 Nano
MODEL_LLM = "nvidia/nemotron-3-nano-30b"

# Alternativas:
MODEL_LLM = "meta-llama/llama-2-70b"       # Llama 2 (mais poderoso)
MODEL_LLM = "mistralai/mistral-7b"         # Mistral (rápido)
MODEL_LLM = "gpt-3.5-turbo"                # GPT-3.5 (via API)
```

### Trocar Modelo ASR (Reconhecimento de Fala)

```python
# backend/asr/modal_asr_whisper.py

# Padrão: Whisper Large-V3
MODEL_ASR = "whisper-large-v3"

# Alternativas:
MODEL_ASR = "whisper-medium"               # Mais rápido, menos preciso
MODEL_ASR = "whisper-small"                # Muito rápido, menos preciso
MODEL_ASR = "whisper-base"                 # Rápido, menos preciso
```

### Trocar Modelo TTS (Síntese de Fala)

```python
# backend/tts/modal_tts_pyttsx3.py

# Padrão: pyttsx3
# Alternativas:
# - gTTS (Google Text-to-Speech)
# - ElevenLabs (mais natural)
# - Azure Text-to-Speech
# - AWS Polly

# Exemplo com ElevenLabs:
import elevenlabs

def synthesize_speech(text: str) -> bytes:
    audio = elevenlabs.generate(
        text=text,
        voice="Bella",  # Voz feminina
        model="eleven_monolingual_v1"
    )
    return audio
```

---

## 5. Customizar Frontend (Cores, Logo, Tema)

### Mudar Cores Primárias

```css
/* frontend/src/index.css */

@layer base {
  :root {
    --primary: 37 99 235;        /* Azul */
    --secondary: 168 85 247;     /* Roxo */
    --accent: 59 130 246;        /* Azul claro */
    --destructive: 239 68 68;    /* Vermelho */
    --muted: 107 114 128;        /* Cinza */
    --background: 255 255 255;   /* Branco */
    --foreground: 15 23 42;      /* Preto */
  }

  .dark {
    --primary: 59 130 246;       /* Azul claro */
    --secondary: 168 85 247;     /* Roxo */
    --accent: 99 102 241;        /* Índigo */
    --background: 15 23 42;      /* Preto */
    --foreground: 248 250 252;   /* Branco */
  }
}
```

### Mudar Logo

```tsx
// frontend/src/App.tsx

import logo from './assets/logo.png';

export default function App() {
  return (
    <div>
      <img src={logo} alt="Logo" className="h-8 w-8" />
      {/* ... */}
    </div>
  );
}
```

### Mudar Fontes

```html
<!-- frontend/index.html -->

<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

```css
/* frontend/src/index.css */

@layer base {
  body {
    font-family: "Poppins", sans-serif;
  }
}
```

### Mudar Tema (Claro/Escuro)

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

## 6. Fazer Deploy

### Deploy do Backend (Modal)

```bash
# 1. Instalar Modal CLI
pip install modal

# 2. Autenticar
modal token new

# 3. Deploy do Orquestrador
cd backend
bash deploy/deploy_orchestrator.sh

# 4. Deploy do Voice Pipeline
bash deploy/deploy_voice_pipeline.sh
cd ..
```

### Deploy do Frontend (Netlify)

```bash
# 1. Build
cd frontend
npm run build

# 2. Deploy
netlify deploy --prod --dir=dist

# 3. Configurar domínio (opcional)
netlify domain add seu-dominio.com
cd ..
```

---

## 7. Configurar Variáveis de Ambiente

### Frontend (.env)

```env
VITE_APP_NAME=Meu Agente RH
VITE_APP_DESCRIPTION=Assistente de Recursos Humanos
VITE_PRIMARY_COLOR=#2563eb
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run
```

### Backend (.env)

```env
MODEL_LLM=nvidia/nemotron-3-nano-30b
MODEL_ASR=whisper-large-v3
MODEL_TTS=pyttsx3
MODAL_API_KEY=seu_modal_api_key
FAISS_INDEX_PATH=./faiss_index.pkl
```

---

## 8. Exemplos Práticos por Domínio

### Agente de RH

**Base de Conhecimento:**
```json
[
  {"question": "Qual é a política de férias?", "answer": "..."},
  {"question": "Como solicitar licença maternidade?", "answer": "..."},
  {"question": "Qual é o horário de trabalho?", "answer": "..."}
]
```

**Customizações:**
- Prompt: Especializado em políticas de RH
- Cores: Azul corporativo
- Logo: Logo da empresa

### Agente Jurídico

**Base de Conhecimento:**
```json
[
  {"question": "O que é LGPD?", "answer": "..."},
  {"question": "Como fazer uma denúncia?", "answer": "..."}
]
```

**Customizações:**
- Prompt: Especializado em direito
- Modelo LLM: Llama 2 70B (mais poderoso)
- Integração: APIs de jurisprudência

### Agente de Suporte Técnico

**Base de Conhecimento:**
```json
[
  {"question": "Como resetar minha senha?", "answer": "..."},
  {"question": "O sistema está fora do ar?", "answer": "..."}
]
```

**Customizações:**
- Prompt: Especializado em suporte técnico
- Integração: Ticket system
- Analytics: Rastreamento de problemas

---

## 9. Monitoramento e Testes

### Testar Localmente

```bash
# Frontend
cd frontend
npm run dev

# Backend (em outro terminal)
cd backend
modal serve modal_orchestrator_api.py
```

### Testar em Produção

```bash
# Testar orquestrador
curl -X POST https://seu-orquestrador.modal.run/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual é a política de férias?"}'

# Testar voice pipeline
curl -X POST https://seu-voice-pipeline.modal.run/process-audio-base64 \
  -H "Content-Type: application/json" \
  -d '{"audio": "base64_encoded_audio"}'
```

---

## 10. Troubleshooting

### Problema: Respostas ruins

**Solução:**
1. Verifique a qualidade da base de conhecimento
2. Ajuste o prompt do LLM
3. Teste com um modelo LLM mais poderoso

### Problema: ASR não reconhece bem

**Solução:**
1. Verifique a qualidade do áudio
2. Tente com Whisper Large-V3 (mais preciso)
3. Ajuste o idioma

### Problema: Deploy falha

**Solução:**
1. Verifique credenciais (Modal, Netlify)
2. Verifique dependências (requirements.txt, package.json)
3. Verifique logs: `modal logs`

---

## Próximas Etapas

1. ✅ Customizar base de conhecimento
2. ✅ Ajustar prompts
3. ✅ Trocar modelos (se necessário)
4. ✅ Customizar frontend
5. ✅ Fazer deploy
6. ✅ Testar e iterar

**Pronto para começar? Clone o template e comece a customizar!** 🚀
