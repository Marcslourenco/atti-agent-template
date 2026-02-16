"""
Whisper ASR Service - Implementação com OpenAI Whisper

Fase D.1: Implementação de ASR com Whisper Large-V3
- Suporte a múltiplos idiomas (português, inglês, espanhol, etc.)
- Latência otimizada
- Interface compatível com ASRService abstrata
"""

import modal
import time
import logging
from datetime import datetime
from typing import Optional
import io

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DO MODAL
# ============================================================================

image = modal.Image.debian_slim().pip_install(
    "openai-whisper>=20240314",
    "torch>=2.1.0",
    "torchaudio>=2.1.0",
    "transformers>=4.40.0",
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
    "numpy>=1.24.0",
    "pydantic>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
)

app = modal.App(name="atti-asr-whisper")

# ============================================================================
# CLASSE DO SERVIÇO WHISPER
# ============================================================================


class WhisperASRService:
    """Serviço de ASR com OpenAI Whisper"""

    def __init__(self, model_size: str = "large-v3"):
        """
        Inicializar serviço Whisper.

        Args:
            model_size: Tamanho do modelo (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self.initialized = False
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
        }

    def initialize(self):
        """Inicializar modelo Whisper"""
        if self.initialized:
            return

        print(f"🔄 Inicializando Whisper {self.model_size}...")

        try:
            import whisper

            # Carregar modelo (será baixado automaticamente)
            self.model = whisper.load_model(self.model_size, device="cuda")
            self.initialized = True

            print(f"✅ Whisper {self.model_size} inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar Whisper: {e}")
            raise

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Transcrever áudio para texto.

        Args:
            audio_bytes: Áudio em formato bytes
            language: Código de idioma (ex: 'pt', 'en'). Se None, auto-detecta.

        Returns:
            Texto transcrito
        """
        if not self.initialized:
            self.initialize()

        start_time = time.time()

        try:
            import whisper
            import tempfile
            import os

            # Salvar áudio em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                # Transcrever com Whisper
                result = self.model.transcribe(
                    tmp_path,
                    language=language,
                    verbose=False,
                )

                transcription = result["text"].strip()

                # Registrar métrica
                latency = time.time() - start_time
                self.metrics["total_requests"] += 1
                self.metrics["successful_requests"] += 1
                self.metrics["total_latency"] += latency

                logger.info(f"✅ Transcrição bem-sucedida ({latency:.2f}s): {transcription[:50]}...")

                return transcription

            finally:
                # Limpar arquivo temporário
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            latency = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1

            logger.error(f"❌ Erro ao transcrever: {e}")
            raise RuntimeError(f"Erro ao transcrever áudio: {str(e)}")

    async def get_status(self) -> dict:
        """Obter status do serviço"""
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
            "service": "whisper-asr",
            "model": f"whisper-{self.model_size}",
            "status": "operational" if self.initialized else "not_initialized",
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "average_latency_ms": round(avg_latency * 1000, 2),
            "success_rate_percent": round(success_rate, 2),
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """Verificar saúde do serviço"""
        return self.initialized


# ============================================================================
# FUNÇÕES MODAL
# ============================================================================


@app.cls(
    gpu="A100",
    timeout=600,
    allow_concurrent_inputs=10,
)
class WhisperServer:
    """Servidor Whisper rodando em GPU A100"""

    def __init__(self):
        self.service = WhisperASRService(model_size="large-v3")
        self.service.initialize()

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> dict:
        """Transcrever áudio"""
        try:
            text = await self.service.transcribe(audio_bytes, language)
            return {
                "status": "success",
                "transcription": text,
                "language": language,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_status(self) -> dict:
        """Obter status do serviço"""
        return await self.service.get_status()

    async def health_check(self) -> dict:
        """Health check"""
        is_healthy = await self.service.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "whisper-asr",
            "model": "whisper-large-v3",
            "gpu": "A100",
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# API FASTAPI
# ============================================================================


@app.function(
    gpu="A100",
    timeout=600,
)
@modal.asgi_app()
def fastapi_app():
    """Aplicação FastAPI para Whisper ASR"""
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import JSONResponse

    app_fastapi = FastAPI(
        title="ATTI Whisper ASR Service",
        version="1.0",
        description="Serviço de reconhecimento de fala com OpenAI Whisper",
    )

    # Inicializar serviço
    service = WhisperASRService(model_size="large-v3")
    service.initialize()

    # ========================================================================
    # ENDPOINTS
    # ========================================================================

    @app_fastapi.get("/health")
    async def health_check():
        """Health check do serviço"""
        return {
            "status": "healthy",
            "service": "whisper-asr",
            "model": "whisper-large-v3",
            "gpu": "A100",
            "timestamp": datetime.now().isoformat(),
        }

    @app_fastapi.post("/transcribe")
    async def transcribe_file(
        file: UploadFile = File(...),
        language: Optional[str] = None,
    ):
        """
        Transcrever arquivo de áudio.

        Parâmetros:
            file: Arquivo de áudio (WAV, MP3, OGG, M4A, etc.)
            language: Código de idioma (pt, en, es, fr, de, etc.). Se None, auto-detecta.

        Retorna:
            Transcrição e metadados
        """
        try:
            # Ler arquivo
            content = await file.read()

            # Transcrever
            text = await service.transcribe(content, language)

            return JSONResponse(
                {
                    "status": "success",
                    "transcription": text,
                    "language": language,
                    "filename": file.filename,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Erro ao transcrever: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app_fastapi.get("/status")
    async def get_status():
        """Obter status do serviço"""
        return await service.get_status()

    @app_fastapi.get("/info")
    async def get_info():
        """Obter informações do serviço"""
        return {
            "service": "whisper-asr",
            "model": "whisper-large-v3",
            "model_size_gb": 2.9,
            "supported_languages": [
                "pt",
                "en",
                "es",
                "fr",
                "de",
                "it",
                "ja",
                "zh",
                "ru",
                "ar",
            ],
            "max_audio_duration_seconds": 3600,
            "estimated_latency_ms": 800,
            "wer_librispeech": 3.0,
            "wer_portuguese": 4.5,
            "gpu": "A100",
            "concurrent_inputs": 10,
            "timestamp": datetime.now().isoformat(),
        }

    return app_fastapi


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 Whisper ASR Service")
    print("=" * 60)
    print("")
    print("Para rodar o serviço:")
    print("  modal serve modal_asr_whisper.py")
    print("")
    print("Para testar:")
    print("  curl http://localhost:8000/health")
    print("")
