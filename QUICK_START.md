# ⚡ Quick Start - 5 Minutos

Guia rápido para começar com o ATTI Agent Template.

---

## 1️⃣ Clonar o Template

```bash
git clone https://github.com/Marcslourenco/atti-agent-template.git
cd atti-agent-template
```

---

## 2️⃣ Instalar Dependências

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

## 3️⃣ Preparar Dados

Edite `data/questions.json` com suas perguntas e respostas:

```json
[
  {
    "question": "Sua pergunta aqui?",
    "answer": "Sua resposta aqui."
  }
]
```

Gere embeddings:

```bash
cd backend
python orchestrator/generate_embeddings.py
cd ..
```

---

## 4️⃣ Deploy Backend (Modal)

```bash
# Autenticar
modal token new

# Deploy
cd backend
bash deploy/deploy_orchestrator.sh
bash deploy/deploy_voice_pipeline.sh
cd ..
```

**Salve as URLs!**

---

## 5️⃣ Deploy Frontend (Netlify)

```bash
# Configurar variáveis de ambiente
cd frontend
cat > .env.production << EOF
VITE_APP_NAME=Meu Agente
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run
EOF

# Build
npm run build

# Deploy
netlify deploy --prod --dir=dist
cd ..
```

---

## ✅ Pronto!

Seu agente está online! 🎉

- 💬 Chat de texto funcionando
- 🎤 Chat de voz funcionando
- 🌍 Acessível publicamente

---

## 📚 Próximas Etapas

1. Leia [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) para personalizar
2. Consulte [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) se tiver problemas
3. Explore [ARCHITECTURE.md](docs/ARCHITECTURE.md) para entender como funciona

---

**Pronto para começar?** Clone o repositório agora! 🚀
