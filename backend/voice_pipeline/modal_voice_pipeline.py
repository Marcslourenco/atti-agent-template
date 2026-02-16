"""
Voice Pipeline - Pipeline completo de voz (ASR + Orquestrador + TTS)

Fase D.3: Integração ao Pipeline LangGraph
- Recebe áudio como input
- Transcreve com Whisper ASR
- Processa com orquestrador
- Sintetiza resposta com pyttsx3 TTS
- Retorna áudio como output
"""

import modal
import time
import logging
from datetime import datetime
from typing import Optional
import base64

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DO MODAL
# ============================================================================

image = modal.Image.debian_slim().pip_install(
    "openai-whisper>=20240314",
    "pyttsx3>=2.90",
    "torch>=2.1.0",
    "torchaudio>=2.1.0",
    "transformers>=4.40.0",
    "requests>=2.31.0",
    "numpy>=1.24.0",
    "pydantic>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "langchain>=0.1.0",
    "langgraph>=0.0.1",
).run_commands(
    "apt-get update && apt-get install -y espeak-ng libsndfile1"
)

app = modal.App(name="atti-voice-pipeline")

# ============================================================================
# CLASSE DO PIPELINE DE VOZ
# ============================================================================


class VoicePipeline:
    """Pipeline completo de processamento de voz"""

    def __init__(
        self,
        asr_url: str = "https://braziltradesp--atti-asr-whisper-fastapi-app.modal.run",
        orchestrator_url: str = "https://braziltradesp--atti-orchestrator-api-fastapi-app.modal.run",
        tts_url: str = "https://braziltradesp--atti-tts-pyttsx3-fastapi-app.modal.run",
    ):
        """
        Inicializar pipeline de voz.

        Args:
            asr_url: URL do serviço ASR
            orchestrator_url: URL do orquestrador
            tts_url: URL do serviço TTS
        """
        self.asr_url = asr_url
        self.orchestrator_url = orchestrator_url
        self.tts_url = tts_url
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "asr_latency": 0.0,
            "orchestrator_latency": 0.0,
            "tts_latency": 0.0,
        }

    async def process_audio(
        self, audio_bytes: bytes, language: Optional[str] = None
    ) -> dict:
        """
        Processar áudio completo (ASR + Orquestrador + TTS).

        Args:
            audio_bytes: Áudio em formato bytes (WAV, MP3, etc.)
            language: Código de idioma (pt, en, etc.)

        Returns:
            Dict com áudio de resposta e metadados
        """
        import requests

        start_time = time.time()

        try:
            # ====================================================================
            # ETAPA 1: ASR (Speech-to-Text)
            # ====================================================================

            logger.info("🎤 Etapa 1: Transcrição de áudio (ASR)...")
            asr_start = time.time()

            # Enviar áudio para ASR
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            params = {"language": language or "pt"}

            asr_response = requests.post(
                f"{self.asr_url}/transcribe",
                files=files,
                params=params,
                timeout=30,
            )
            asr_response.raise_for_status()

            asr_result = asr_response.json()
            transcription = asr_result.get("transcription", "")

            asr_latency = time.time() - asr_start
            self.metrics["asr_latency"] += asr_latency

            logger.info(f"✅ ASR concluído ({asr_latency:.2f}s): {transcription[:50]}...")

            if not transcription:
                raise ValueError("ASR retornou transcrição vazia")

            # ====================================================================
            # ETAPA 2: Orquestrador (Chat)
            # ====================================================================

            logger.info("🧠 Etapa 2: Processamento com orquestrador...")
            orchestrator_start = time.time()

            # Enviar transcrição para orquestrador
            chat_payload = {"message": transcription}

            orchestrator_response = requests.post(
                f"{self.orchestrator_url}/chat",
                json=chat_payload,
                timeout=30,
            )
            orchestrator_response.raise_for_status()

            orchestrator_result = orchestrator_response.json()
            response_text = orchestrator_result.get("response", "")

            orchestrator_latency = time.time() - orchestrator_start
            self.metrics["orchestrator_latency"] += orchestrator_latency

            logger.info(
                f"✅ Orquestrador concluído ({orchestrator_latency:.2f}s): {response_text[:50]}..."
            )

            if not response_text:
                raise ValueError("Orquestrador retornou resposta vazia")

            # ====================================================================
            # ETAPA 3: TTS (Text-to-Speech)
            # ====================================================================

            logger.info("🔊 Etapa 3: Síntese de fala (TTS)...")
            tts_start = time.time()

            # Enviar resposta para TTS
            tts_payload = {
                "text": response_text,
                "language": language or "pt",
            }

            tts_response = requests.post(
                f"{self.tts_url}/synthesize",
                json=tts_payload,
                timeout=30,
            )
            tts_response.raise_for_status()

            tts_result = tts_response.json()
            audio_base64 = tts_result.get("audio_base64", "")

            # Converter de base64 para bytes
            response_audio_bytes = base64.b64decode(audio_base64)

            tts_latency = time.time() - tts_start
            self.metrics["tts_latency"] += tts_latency

            logger.info(f"✅ TTS concluído ({tts_latency:.2f}s): {len(response_audio_bytes)} bytes")

            # ====================================================================
            # RESULTADO FINAL
            # ====================================================================

            total_latency = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += total_latency

            logger.info(f"✅ Pipeline completo concluído ({total_latency:.2f}s)")

            return {
                "status": "success",
                "transcription": transcription,
                "response_text": response_text,
                "response_audio_base64": audio_base64,
                "response_audio_bytes": response_audio_bytes,
                "latencies": {
                    "asr_ms": round(asr_latency * 1000, 2),
                    "orchestrator_ms": round(orchestrator_latency * 1000, 2),
                    "tts_ms": round(tts_latency * 1000, 2),
                    "total_ms": round(total_latency * 1000, 2),
                },
                "language": language or "pt",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1

            logger.error(f"❌ Erro no pipeline: {e}")

            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_status(self) -> dict:
        """Obter status do pipeline"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["successful_requests"]
            if self.metrics["successful_requests"] > 0
            else 0
        )

        success_rate = (
            (self.metrics["successful_requests"] / self.metrics["total_requests"] * 100)
            if self.metrics["total_requests"] > 0
            else 0
        )

        return {
            "service": "voice-pipeline",
            "status": "operational",
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "average_latency_ms": round(avg_latency * 1000, 2),
            "success_rate_percent": round(success_rate, 2),
            "latencies": {
                "asr_ms": round(self.metrics["asr_latency"] * 1000, 2),
                "orchestrator_ms": round(self.metrics["orchestrator_latency"] * 1000, 2),
                "tts_ms": round(self.metrics["tts_latency"] * 1000, 2),
            },
            "dependencies": {
                "asr": self.asr_url,
                "orchestrator": self.orchestrator_url,
                "tts": self.tts_url,
            },
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# FUNÇÕES MODAL
# ============================================================================


@app.cls(
    timeout=120,
    allow_concurrent_inputs=5,
)
class VoicePipelineServer:
    """Servidor do pipeline de voz"""

    def __init__(self):
        self.pipeline = VoicePipeline()

    async def process_audio(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        """Processar áudio"""
        return await self.pipeline.process_audio(audio_bytes, language)

    async def get_status(self) -> dict:
        """Obter status do pipeline"""
        return await self.pipeline.get_status()

    async def health_check(self) -> dict:
        """Health check"""
        return {
            "status": "healthy",
            "service": "voice-pipeline",
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# API FASTAPI
# ============================================================================


@app.function(timeout=120)
@modal.asgi_app()
def fastapi_app():
    """Aplicação FastAPI para Voice Pipeline"""
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    app_fastapi = FastAPI(
        title="ATTI Voice Pipeline",
        version="1.0",
        description="Pipeline completo de processamento de voz (ASR + Orquestrador + TTS)",
    )

    # Inicializar pipeline
    pipeline = VoicePipeline()

    # ========================================================================
    # MODELOS
    # ========================================================================

    class ProcessAudioRequest(BaseModel):
        audio_base64: str
        language: Optional[str] = "pt"

    # ========================================================================
    # ENDPOINTS
    # ========================================================================

    @app_fastapi.get("/health")
    async def health_check():
        """Health check do pipeline"""
        return {
            "status": "healthy",
            "service": "voice-pipeline",
            "timestamp": datetime.now().isoformat(),
        }

    @app_fastapi.post("/process-audio")
    async def process_audio_file(
        file: UploadFile = File(...),
        language: Optional[str] = "pt",
    ):
        """
        Processar áudio completo (ASR + Orquestrador + TTS).

        Parâmetros:
            file: Arquivo de áudio (WAV, MP3, OGG, M4A, etc.)
            language: Código de idioma (pt, en, es, etc.)

        Retorna:
            Transcrição, resposta e áudio de resposta
        """
        try:
            # Ler arquivo
            content = await file.read()

            # Processar
            result = await pipeline.process_audio(content, language)

            return JSONResponse(result)

        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app_fastapi.post("/process-audio-base64")
    async def process_audio_base64(request: ProcessAudioRequest):
        """
        Processar áudio em base64.

        Parâmetros:
            audio_base64: Áudio em formato base64
            language: Código de idioma (pt, en, es, etc.)

        Retorna:
            Transcrição, resposta e áudio de resposta (base64)
        """
        try:
            # Decodificar base64
            audio_bytes = base64.b64decode(request.audio_base64)

            # Processar
            result = await pipeline.process_audio(audio_bytes, request.language)

            return JSONResponse(result)

        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app_fastapi.get("/status")
    async def get_status():
        """Obter status do pipeline"""
        return await pipeline.get_status()

    @app_fastapi.get("/info")
    async def get_info():
        """Obter informações do pipeline"""
        return {
            "service": "voice-pipeline",
            "description": "Pipeline completo de processamento de voz",
            "components": {
                "asr": "Whisper Large-V3",
                "orchestrator": "ATTI Orchestrator",
                "tts": "pyttsx3",
            },
            "supported_languages": ["pt", "en", "es", "fr", "de", "it", "ja", "zh"],
            "estimated_latency_ms": 2000,  # ASR (800) + Orchestrator (400) + TTS (300)
            "concurrent_requests": 5,
            "timestamp": datetime.now().isoformat(),
        }

    return app_fastapi


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 Voice Pipeline")
    print("=" * 60)
    print("")
    print("Para rodar o pipeline:")
    print("  modal serve modal_voice_pipeline.py")
    print("")
    print("Para testar:")
    print("  curl http://localhost:8000/health")
    print("")
