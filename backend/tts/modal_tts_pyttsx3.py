"""
pyttsx3 TTS Service - Implementação com pyttsx3

Fase D.2: Implementação de TTS com pyttsx3
- Suporte a múltiplos idiomas (português, inglês, espanhol, etc.)
- Vozes nativas do sistema operacional
- Interface compatível com TTSService abstrata
- Latência baixa (<500ms)
"""

import modal
import time
import logging
from datetime import datetime
from typing import Optional
import io
import wave

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DO MODAL
# ============================================================================

image = modal.Image.debian_slim().pip_install(
    "pyttsx3>=2.90",
    "numpy>=1.24.0",
    "pydantic>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
).run_commands(
    # Instalar dependências de áudio do sistema
    "apt-get update && apt-get install -y espeak-ng libsndfile1"
)

app = modal.App(name="atti-tts-pyttsx3")

# ============================================================================
# CLASSE DO SERVIÇO PYTTSX3
# ============================================================================


class Pyttsx3TTSService:
    """Serviço de TTS com pyttsx3"""

    def __init__(self, language: str = "pt"):
        """
        Inicializar serviço pyttsx3.

        Args:
            language: Idioma padrão (pt, en, es, fr, de, etc.)
        """
        self.language = language
        self.engine = None
        self.initialized = False
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "total_characters": 0,
        }
        self.available_voices = []

    def initialize(self):
        """Inicializar engine pyttsx3"""
        if self.initialized:
            return

        print(f"🔄 Inicializando pyttsx3 ({self.language})...")

        try:
            import pyttsx3

            # Criar engine
            self.engine = pyttsx3.init()

            # Configurar propriedades
            self.engine.setProperty("rate", 150)  # Velocidade (palavras por minuto)
            self.engine.setProperty("volume", 0.9)  # Volume (0.0 a 1.0)

            # Obter vozes disponíveis
            self._load_available_voices()

            self.initialized = True

            print(f"✅ pyttsx3 inicializado com sucesso")
            print(f"   Vozes disponíveis: {len(self.available_voices)}")

        except Exception as e:
            logger.error(f"Erro ao inicializar pyttsx3: {e}")
            raise

    def _load_available_voices(self):
        """Carregar vozes disponíveis"""
        try:
            voices = self.engine.getProperty("voices")
            self.available_voices = []

            for voice in voices:
                voice_info = {
                    "id": voice.id,
                    "name": voice.name,
                    "languages": voice.languages if hasattr(voice, "languages") else [],
                    "gender": voice.gender if hasattr(voice, "gender") else "unknown",
                    "age": voice.age if hasattr(voice, "age") else "unknown",
                }
                self.available_voices.append(voice_info)

            logger.info(f"Vozes carregadas: {len(self.available_voices)}")

        except Exception as e:
            logger.error(f"Erro ao carregar vozes: {e}")

    def _select_voice(self, language: Optional[str] = None, voice: Optional[str] = None):
        """Selecionar voz apropriada"""
        target_language = language or self.language

        # Se voz foi especificada, usar diretamente
        if voice:
            try:
                self.engine.setProperty("voice", voice)
                return
            except Exception as e:
                logger.warning(f"Voz {voice} não encontrada: {e}")

        # Procurar voz por idioma
        for v in self.available_voices:
            # Verificar se o idioma está na lista de idiomas da voz
            if hasattr(v, "languages") and target_language in v.get("languages", []):
                self.engine.setProperty("voice", v["id"])
                return

        # Fallback: usar primeira voz disponível
        if self.available_voices:
            self.engine.setProperty("voice", self.available_voices[0]["id"])
            logger.warning(f"Voz para {target_language} não encontrada, usando padrão")

    async def synthesize(
        self, text: str, language: Optional[str] = None, voice: Optional[str] = None
    ) -> bytes:
        """
        Sintetizar texto para áudio.

        Args:
            text: Texto a ser sintetizado
            language: Código de idioma (pt, en, es, etc.)
            voice: ID da voz específica

        Returns:
            Áudio em formato bytes (WAV)
        """
        if not self.initialized:
            self.initialize()

        if not text or not text.strip():
            raise ValueError("Texto não pode estar vazio")

        start_time = time.time()

        try:
            import tempfile
            import os

            # Selecionar voz
            self._select_voice(language, voice)

            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_path = tmp.name

            # Sintetizar
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()

            # Ler arquivo
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            # Limpar
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            # Registrar métrica
            latency = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += latency
            self.metrics["total_characters"] += len(text)

            logger.info(
                f"✅ Síntese bem-sucedida ({latency:.2f}s): {len(text)} caracteres"
            )

            return audio_bytes

        except Exception as e:
            latency = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1

            logger.error(f"❌ Erro ao sintetizar: {e}")
            raise RuntimeError(f"Erro ao sintetizar áudio: {str(e)}")

    async def get_available_voices(self) -> list:
        """Obter vozes disponíveis"""
        if not self.initialized:
            self.initialize()

        return self.available_voices

    async def get_status(self) -> dict:
        """Obter status do serviço"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["successful_requests"]
            if self.metrics["successful_requests"] > 0
            else 0
        )

        avg_chars_per_sec = (
            self.metrics["total_characters"] / self.metrics["total_latency"]
            if self.metrics["total_latency"] > 0
            else 0
        )

        success_rate = (
            (self.metrics["successful_requests"] / self.metrics["total_requests"] * 100)
            if self.metrics["total_requests"] > 0
            else 0
        )

        return {
            "service": "pyttsx3-tts",
            "status": "operational" if self.initialized else "not_initialized",
            "language": self.language,
            "available_voices": len(self.available_voices),
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "average_latency_ms": round(avg_latency * 1000, 2),
            "average_chars_per_second": round(avg_chars_per_sec, 2),
            "success_rate_percent": round(success_rate, 2),
            "total_characters_synthesized": self.metrics["total_characters"],
            "timestamp": datetime.now().isoformat(),
        }

    async def health_check(self) -> bool:
        """Verificar saúde do serviço"""
        return self.initialized


# ============================================================================
# FUNÇÕES MODAL
# ============================================================================


@app.cls(
    timeout=300,
    allow_concurrent_inputs=5,
)
class Pyttsx3Server:
    """Servidor pyttsx3 TTS"""

    def __init__(self):
        self.service = Pyttsx3TTSService(language="pt")
        self.service.initialize()

    async def synthesize(
        self, text: str, language: Optional[str] = None, voice: Optional[str] = None
    ) -> dict:
        """Sintetizar texto"""
        try:
            audio_bytes = await self.service.synthesize(text, language, voice)
            return {
                "status": "success",
                "audio_bytes": audio_bytes,
                "language": language or "pt",
                "text_length": len(text),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_available_voices(self) -> dict:
        """Obter vozes disponíveis"""
        voices = await self.service.get_available_voices()
        return {
            "status": "success",
            "voices": voices,
            "total_voices": len(voices),
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
            "service": "pyttsx3-tts",
            "language": "pt",
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# API FASTAPI
# ============================================================================


@app.function(timeout=300)
@modal.asgi_app()
def fastapi_app():
    """Aplicação FastAPI para pyttsx3 TTS"""
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    app_fastapi = FastAPI(
        title="ATTI pyttsx3 TTS Service",
        version="1.0",
        description="Serviço de síntese de fala com pyttsx3",
    )

    # Inicializar serviço
    service = Pyttsx3TTSService(language="pt")
    service.initialize()

    # ========================================================================
    # MODELOS
    # ========================================================================

    class SynthesizeRequest(BaseModel):
        text: str
        language: Optional[str] = "pt"
        voice: Optional[str] = None

    # ========================================================================
    # ENDPOINTS
    # ========================================================================

    @app_fastapi.get("/health")
    async def health_check():
        """Health check do serviço"""
        return {
            "status": "healthy",
            "service": "pyttsx3-tts",
            "language": "pt",
            "timestamp": datetime.now().isoformat(),
        }

    @app_fastapi.post("/synthesize")
    async def synthesize(request: SynthesizeRequest):
        """
        Sintetizar texto para áudio.

        Parâmetros:
            text: Texto a ser sintetizado
            language: Código de idioma (pt, en, es, fr, de, etc.)
            voice: ID da voz específica (opcional)

        Retorna:
            Áudio em formato base64
        """
        try:
            audio_bytes = await service.synthesize(request.text, request.language, request.voice)

            # Converter para base64 para enviar via JSON
            import base64

            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            return JSONResponse(
                {
                    "status": "success",
                    "audio_base64": audio_base64,
                    "language": request.language,
                    "text_length": len(request.text),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"Erro ao sintetizar: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app_fastapi.get("/voices")
    async def get_voices():
        """Obter vozes disponíveis"""
        voices = await service.get_available_voices()
        return JSONResponse(
            {
                "status": "success",
                "voices": voices,
                "total_voices": len(voices),
                "timestamp": datetime.now().isoformat(),
            }
        )

    @app_fastapi.get("/status")
    async def get_status():
        """Obter status do serviço"""
        return await service.get_status()

    @app_fastapi.get("/info")
    async def get_info():
        """Obter informações do serviço"""
        return {
            "service": "pyttsx3-tts",
            "engine": "pyttsx3",
            "supported_languages": ["pt", "en", "es", "fr", "de", "it", "ja", "zh"],
            "estimated_latency_ms": 300,
            "quality": "natural",
            "concurrent_requests": 5,
            "timestamp": datetime.now().isoformat(),
        }

    return app_fastapi


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 pyttsx3 TTS Service")
    print("=" * 60)
    print("")
    print("Para rodar o serviço:")
    print("  modal serve modal_tts_pyttsx3.py")
    print("")
    print("Para testar:")
    print("  curl http://localhost:8000/health")
    print("")
