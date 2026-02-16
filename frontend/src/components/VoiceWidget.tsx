import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Mic, Square, Play, X } from "lucide-react";

const VOICE_PIPELINE_URL = "https://braziltradesp--atti-voice-pipeline-fastapi-app.modal.run";

interface VoiceMessage {
  id: string;
  audioUrl: string;
  transcript: string;
  response: string;
  responseAudio: string;
  timestamp: Date;
}

export function VoiceWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/wav",
        });
        await handleAudioSubmit(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Erro ao acessar microfone:", error);
      alert("Não foi possível acessar o microfone. Verifique as permissões.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setLoading(true);

    try {
      // Converter blob para base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);

      reader.onload = async () => {
        const base64Audio = (reader.result as string).split(",")[1];

        // Enviar para Voice Pipeline
        const response = await fetch(
          `${VOICE_PIPELINE_URL}/process-audio-base64`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              audio_base64: base64Audio,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("Erro ao processar áudio");
        }

        const data = await response.json();

        // Criar mensagem com áudio e resposta
        const voiceMessage: VoiceMessage = {
          id: Date.now().toString(),
          audioUrl: reader.result as string,
          transcript: data.transcript || "Não foi possível transcrever",
          response: data.response || "Desculpe, não consegui processar.",
          responseAudio: data.response_audio || "",
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, voiceMessage]);

        // Reproduzir áudio de resposta se disponível
        if (data.response_audio) {
          const audio = new Audio(
            `data:audio/wav;base64,${data.response_audio}`
          );
          audio.play().catch((err) =>
            console.error("Erro ao reproduzir áudio:", err)
          );
        }
      };
    } catch (error) {
      console.error("Erro no processamento de voz:", error);
      alert("Erro ao processar áudio. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (audioUrl: string) => {
    const audio = new Audio(audioUrl);
    audio.play();
  };

  return (
    <>
      {/* Botão flutuante */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-24 right-6 z-40 rounded-full bg-purple-600 p-4 text-white shadow-lg hover:bg-purple-700 transition-colors"
          title="Abrir chat de voz"
        >
          <Mic size={24} />
        </button>
      )}

      {/* Widget de voz */}
      {isOpen && (
        <Card className="fixed bottom-24 right-6 z-50 flex flex-col w-96 h-[500px] shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between bg-purple-600 text-white p-4 rounded-t-lg">
            <h3 className="font-semibold">Assistente de Voz ATTI</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-purple-700 p-1 rounded transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm mt-8">
                Clique no microfone para começar a falar
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className="space-y-3">
                {/* Pergunta do usuário */}
                <div className="flex justify-end">
                  <div className="max-w-xs bg-purple-600 text-white px-4 py-2 rounded-lg rounded-br-none">
                    <p className="text-sm font-semibold mb-2">Você:</p>
                    <p className="text-sm">{msg.transcript}</p>
                    <button
                      onClick={() => playAudio(msg.audioUrl)}
                      className="mt-2 text-xs bg-purple-700 hover:bg-purple-800 px-2 py-1 rounded flex items-center gap-1"
                    >
                      <Play size={12} /> Reproduzir
                    </button>
                  </div>
                </div>

                {/* Resposta do bot */}
                <div className="flex justify-start">
                  <div className="max-w-xs bg-white text-gray-900 border border-gray-200 px-4 py-2 rounded-lg rounded-bl-none">
                    <p className="text-sm font-semibold mb-2">ATTI:</p>
                    <p className="text-sm">{msg.response}</p>
                    {msg.responseAudio && (
                      <button
                        onClick={() =>
                          playAudio(
                            `data:audio/wav;base64,${msg.responseAudio}`
                          )
                        }
                        className="mt-2 text-xs bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded flex items-center gap-1"
                      >
                        <Play size={12} /> Reproduzir Resposta
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-center">
                <div className="text-gray-500 text-sm">
                  Processando áudio...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Controles de gravação */}
          <div className="border-t p-4 bg-white rounded-b-lg">
            <div className="flex gap-2">
              {!isRecording ? (
                <Button
                  onClick={startRecording}
                  disabled={loading}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 flex items-center gap-2"
                >
                  <Mic size={16} /> Gravar
                </Button>
              ) : (
                <Button
                  onClick={stopRecording}
                  className="flex-1 bg-red-600 hover:bg-red-700 flex items-center gap-2"
                >
                  <Square size={16} /> Parar
                </Button>
              )}
            </div>
            {isRecording && (
              <p className="text-xs text-red-600 mt-2 text-center">
                🔴 Gravando...
              </p>
            )}
          </div>
        </Card>
      )}
    </>
  );
}
