import { ChatWidget } from './components/ChatWidget'
import { VoiceWidget } from './components/VoiceWidget'

export default function App() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const voiceApiUrl = import.meta.env.VITE_VOICE_API_URL || 'http://localhost:8001'
  const appName = import.meta.env.VITE_APP_NAME || 'ATTI Agent'

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">{appName}</h1>
          <p className="text-sm text-muted-foreground">
            Um agente conversacional inteligente com suporte a texto e voz
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid gap-8 md:grid-cols-2">
          {/* Chat de Texto */}
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-xl font-semibold mb-2">💬 Chat de Texto</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Faça perguntas e receba respostas inteligentes em tempo real
              </p>
            </div>
            <div className="flex-1 rounded-lg border border-border bg-card p-4">
              <ChatWidget apiUrl={apiBaseUrl} />
            </div>
          </div>

          {/* Chat de Voz */}
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-xl font-semibold mb-2">🎤 Chat de Voz</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Fale suas perguntas e ouça as respostas em áudio
              </p>
            </div>
            <div className="flex-1 rounded-lg border border-border bg-card p-4">
              <VoiceWidget apiUrl={voiceApiUrl} />
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 rounded-lg border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-4">ℹ️ Sobre este Template</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Este é o ATTI Agent Template - um template reutilizável para criar agentes 
            conversacionais multimodais (texto + voz) com suporte a RAG (Retrieval-Augmented Generation) 
            e LLM (Large Language Models).
          </p>
          <div className="grid gap-4 md:grid-cols-3 text-sm">
            <div>
              <h4 className="font-semibold mb-2">🚀 Rápido</h4>
              <p className="text-muted-foreground">
                Crie novos agentes em dias, não meses
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">🔧 Modular</h4>
              <p className="text-muted-foreground">
                Customize cada componente conforme necessário
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">📚 Documentado</h4>
              <p className="text-muted-foreground">
                Documentação completa em português
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>
            ATTI Agent Template • 
            <a href="https://github.com/Marcslourenco/atti-agent-template" className="ml-1 text-primary hover:underline">
              GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
