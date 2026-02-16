# 🎨 Frontend

Interface React para o agente conversacional.

---

## Estrutura

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWidget.tsx       # Widget de chat de texto
│   │   ├── VoiceWidget.tsx      # Widget de chat de voz
│   │   └── ...
│   ├── services/
│   │   ├── chatService.ts       # Integração com orquestrador
│   │   └── voiceService.ts      # Integração com voice pipeline
│   ├── hooks/
│   │   └── useMediaRecorder.ts  # Hook para gravação de áudio
│   ├── App.tsx                  # Aplicação principal
│   ├── main.tsx                 # Entry point
│   └── index.css                # Estilos globais
├── public/                      # Assets estáticos
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

---

## Instalação

```bash
cd frontend
npm install
```

---

## Desenvolvimento

```bash
npm run dev
```

Acesse `http://localhost:5173`

---

## Build

```bash
npm run build
```

Cria pasta `dist/` pronta para deploy.

---

## Componentes

### ChatWidget

Widget de chat de texto.

```tsx
import { ChatWidget } from '@/components/ChatWidget';

export default function App() {
  return (
    <ChatWidget 
      apiUrl="https://seu-orquestrador.modal.run"
    />
  );
}
```

### VoiceWidget

Widget de chat de voz.

```tsx
import { VoiceWidget } from '@/components/VoiceWidget';

export default function App() {
  return (
    <VoiceWidget 
      apiUrl="https://seu-voice-pipeline.modal.run"
    />
  );
}
```

---

## Serviços

### chatService

Integração com orquestrador.

```tsx
import { chatService } from '@/services/chatService';

const response = await chatService.sendMessage(
  'Qual é a política de férias?',
  'https://seu-orquestrador.modal.run'
);

console.log(response.response);
```

### voiceService

Integração com voice pipeline.

```tsx
import { voiceService } from '@/services/voiceService';

const response = await voiceService.processAudio(
  audioBlob,
  'https://seu-voice-pipeline.modal.run'
);

console.log(response.transcription);
console.log(response.response);
// response.audio é base64
```

---

## Hooks

### useMediaRecorder

Hook para gravação de áudio.

```tsx
import { useMediaRecorder } from '@/hooks/useMediaRecorder';

export default function MyComponent() {
  const { 
    isRecording, 
    startRecording, 
    stopRecording, 
    audioBlob 
  } = useMediaRecorder();

  return (
    <>
      <button onClick={startRecording}>Gravar</button>
      <button onClick={stopRecording}>Parar</button>
      {audioBlob && <audio src={URL.createObjectURL(audioBlob)} />}
    </>
  );
}
```

---

## Variáveis de Ambiente

```env
VITE_APP_NAME=Meu Agente
VITE_APP_DESCRIPTION=Um agente conversacional inteligente
VITE_PRIMARY_COLOR=#2563eb
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run
```

---

## Customização

### Mudar Cores

```css
/* src/index.css */

@layer base {
  :root {
    --primary: 37 99 235;        /* Azul */
    --secondary: 168 85 247;     /* Roxo */
    --accent: 59 130 246;        /* Azul claro */
  }
}
```

### Mudar Tema

```tsx
// src/App.tsx
import { ThemeProvider } from '@/components/theme-provider';

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      {/* ... */}
    </ThemeProvider>
  );
}
```

### Mudar Logo

```tsx
// src/App.tsx
import logo from '@/assets/logo.png';

export default function App() {
  return (
    <img src={logo} alt="Logo" className="h-8 w-8" />
  );
}
```

---

## Deploy

### Netlify

```bash
# Build
npm run build

# Deploy
netlify deploy --prod --dir=dist
```

### Vercel

```bash
# Build
npm run build

# Deploy (com Vercel CLI)
vercel --prod
```

---

## Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite 7.3.1** - Build tool
- **Tailwind CSS 4** - Styling
- **shadcn/ui** - UI components
- **Wouter** - Routing

---

## Troubleshooting

### Página em branco

```bash
npm install
npm run dev
```

Verificar console (F12) para erros.

### Chat não conecta

Verificar URLs em `.env`:
```env
VITE_API_BASE_URL=https://seu-orquestrador.modal.run
VITE_VOICE_API_URL=https://seu-voice-pipeline.modal.run
```

### Áudio não funciona

- Usar navegador moderno
- Verificar permissão de microfone
- Testar em HTTPS

---

## Próximas Melhorias

- [ ] Dark mode toggle
- [ ] Histórico de chat
- [ ] Exportar conversa
- [ ] Análise de sentimento
- [ ] Suporte a anexos

---

**Pronto para começar!** 🚀
