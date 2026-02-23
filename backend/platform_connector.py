"""
Platform Connector Module

Permite que o template reutilizável se conecte opcionalmente à plataforma
Digital Worker Platform via API REST.

Características:
- Comunicação exclusiva via HTTP REST
- Autenticação via API Key
- Fallback gracioso se plataforma não estiver disponível
- Métodos: query_worker(), upload_document()
- Zero dependência de código da plataforma
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import httpx
from enum import Enum

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlatformStatus(Enum):
    """Status de conexão com a plataforma"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class PlatformConfig:
    """Configuração de conexão com a plataforma"""
    endpoint: str
    api_key: str
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "PlatformConfig":
        """Carrega configuração das variáveis de ambiente"""
        return cls(
            endpoint=os.getenv("PLATFORM_ENDPOINT", ""),
            api_key=os.getenv("PLATFORM_API_KEY", ""),
            timeout=int(os.getenv("PLATFORM_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("PLATFORM_RETRY_ATTEMPTS", "3")),
            enabled=os.getenv("PLATFORM_ENABLED", "false").lower() == "true"
        )


class PlatformConnector:
    """
    Conector para integração com Digital Worker Platform.
    
    Funciona como cliente HTTP REST da plataforma, permitindo:
    - Consultar dados de workers
    - Enviar documentos para processamento
    - Recuperar resultados de análises
    
    O sistema funciona normalmente mesmo se a plataforma não estiver disponível.
    """

    def __init__(self, config: Optional[PlatformConfig] = None):
        """
        Inicializa o conector.
        
        Args:
            config: Configuração de conexão. Se None, carrega de variáveis de ambiente.
        """
        self.config = config or PlatformConfig.from_env()
        self.status = PlatformStatus.DISCONNECTED
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Inicializa cliente HTTP com headers de autenticação"""
        if not self.config.enabled:
            logger.info("Platform connector desativado (PLATFORM_ENABLED=false)")
            return

        if not self.config.endpoint or not self.config.api_key:
            logger.warning(
                "Platform connector não configurado. "
                "Defina PLATFORM_ENDPOINT e PLATFORM_API_KEY"
            )
            return

        try:
            self.client = httpx.Client(
                base_url=self.config.endpoint,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "atti-agent-template/1.0"
                },
                timeout=self.config.timeout
            )
            self._check_health()
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente HTTP: {e}")
            self.status = PlatformStatus.ERROR

    def _check_health(self) -> bool:
        """Verifica saúde da conexão com a plataforma"""
        if not self.client:
            return False

        try:
            response = self.client.get(
                "/api/v1/health",
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                self.status = PlatformStatus.CONNECTED
                logger.info("✅ Conectado à plataforma Digital Worker")
                return True
            else:
                self.status = PlatformStatus.ERROR
                logger.warning(f"Plataforma retornou status {response.status_code}")
                return False
        except httpx.ConnectError:
            self.status = PlatformStatus.DISCONNECTED
            logger.warning("❌ Plataforma indisponível (ConnectError)")
            return False
        except httpx.TimeoutException:
            self.status = PlatformStatus.ERROR
            logger.warning("❌ Timeout ao conectar à plataforma")
            return False
        except Exception as e:
            self.status = PlatformStatus.ERROR
            logger.error(f"Erro ao verificar saúde da plataforma: {e}")
            return False

    async def query_worker(
        self,
        query: str,
        worker_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Consulta um worker na plataforma.
        
        Args:
            query: Pergunta ou comando para o worker
            worker_id: ID do worker (opcional, usa padrão se não fornecido)
            context: Contexto adicional (opcional)
            timeout: Timeout customizado (opcional)
            
        Returns:
            Resposta do worker ou fallback se plataforma indisponível
            
        Exemplo:
            response = await connector.query_worker(
                query="Qual é a alíquota de IPI?",
                worker_id="tax-expert",
                context={"domain": "tax"}
            )
        """
        if not self.client or self.status == PlatformStatus.DISCONNECTED:
            logger.info("Plataforma indisponível. Retornando fallback.")
            return self._get_fallback_response(query)

        payload = {
            "query": query,
            "worker_id": worker_id or "default",
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = self.client.post(
                    "/api/v1/workers/query",
                    json=payload,
                    timeout=timeout or self.config.timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Query ao worker bem-sucedida: {worker_id}")
                    return result
                elif response.status_code == 401:
                    logger.error("❌ Autenticação falhou (API Key inválida)")
                    return self._get_fallback_response(query)
                elif response.status_code == 404:
                    logger.warning(f"❌ Worker não encontrado: {worker_id}")
                    return self._get_fallback_response(query)
                else:
                    logger.warning(
                        f"Tentativa {attempt + 1}/{self.config.retry_attempts}: "
                        f"Status {response.status_code}"
                    )

            except httpx.TimeoutException:
                logger.warning(
                    f"Tentativa {attempt + 1}/{self.config.retry_attempts}: Timeout"
                )
                if attempt == self.config.retry_attempts - 1:
                    return self._get_fallback_response(query)

            except Exception as e:
                logger.error(
                    f"Tentativa {attempt + 1}/{self.config.retry_attempts}: {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    return self._get_fallback_response(query)

        return self._get_fallback_response(query)

    async def upload_document(
        self,
        document_content: str,
        document_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Envia um documento para a plataforma processar.
        
        Args:
            document_content: Conteúdo do documento
            document_type: Tipo do documento (text, pdf, docx, etc.)
            metadata: Metadados adicionais (opcional)
            timeout: Timeout customizado (opcional)
            
        Returns:
            Resposta da plataforma com ID do documento ou fallback
            
        Exemplo:
            response = await connector.upload_document(
                document_content="Texto da legislação...",
                document_type="text",
                metadata={"source": "DOU", "date": "2026-02-23"}
            )
        """
        if not self.client or self.status == PlatformStatus.DISCONNECTED:
            logger.info("Plataforma indisponível. Retornando fallback.")
            return self._get_fallback_upload_response()

        payload = {
            "content": document_content,
            "type": document_type,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = self.client.post(
                    "/api/v1/documents/upload",
                    json=payload,
                    timeout=timeout or self.config.timeout
                )

                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"✅ Documento enviado com sucesso: {result.get('id')}")
                    return result
                elif response.status_code == 401:
                    logger.error("❌ Autenticação falhou (API Key inválida)")
                    return self._get_fallback_upload_response()
                elif response.status_code == 413:
                    logger.error("❌ Documento muito grande")
                    return {
                        "success": False,
                        "error": "document_too_large",
                        "fallback": True
                    }
                else:
                    logger.warning(
                        f"Tentativa {attempt + 1}/{self.config.retry_attempts}: "
                        f"Status {response.status_code}"
                    )

            except httpx.TimeoutException:
                logger.warning(
                    f"Tentativa {attempt + 1}/{self.config.retry_attempts}: Timeout"
                )
                if attempt == self.config.retry_attempts - 1:
                    return self._get_fallback_upload_response()

            except Exception as e:
                logger.error(
                    f"Tentativa {attempt + 1}/{self.config.retry_attempts}: {e}"
                )
                if attempt == self.config.retry_attempts - 1:
                    return self._get_fallback_upload_response()

        return self._get_fallback_upload_response()

    async def get_worker_status(self, worker_id: str) -> Dict[str, Any]:
        """
        Obtém status de um worker.
        
        Args:
            worker_id: ID do worker
            
        Returns:
            Status do worker ou fallback se indisponível
        """
        if not self.client or self.status == PlatformStatus.DISCONNECTED:
            return {"status": "unknown", "fallback": True}

        try:
            response = self.client.get(
                f"/api/v1/workers/{worker_id}/status",
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Erro ao obter status do worker: {e}")

        return {"status": "unknown", "fallback": True}

    async def list_workers(self) -> List[Dict[str, Any]]:
        """
        Lista workers disponíveis na plataforma.
        
        Returns:
            Lista de workers ou lista vazia se indisponível
        """
        if not self.client or self.status == PlatformStatus.DISCONNECTED:
            return []

        try:
            response = self.client.get(
                "/api/v1/workers",
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                return response.json().get("workers", [])
        except Exception as e:
            logger.warning(f"Erro ao listar workers: {e}")

        return []

    def get_status(self) -> str:
        """Retorna status atual da conexão"""
        return self.status.value

    def is_connected(self) -> bool:
        """Verifica se está conectado à plataforma"""
        return self.status == PlatformStatus.CONNECTED

    def close(self) -> None:
        """Fecha conexão com a plataforma"""
        if self.client:
            self.client.close()
            logger.info("Conexão com plataforma fechada")

    @staticmethod
    def _get_fallback_response(query: str) -> Dict[str, Any]:
        """Retorna resposta fallback quando plataforma não está disponível"""
        return {
            "success": False,
            "query": query,
            "response": "Plataforma indisponível. Usando modo offline.",
            "fallback": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def _get_fallback_upload_response() -> Dict[str, Any]:
        """Retorna resposta fallback para upload quando plataforma não está disponível"""
        return {
            "success": False,
            "error": "platform_unavailable",
            "message": "Plataforma indisponível. Documento não foi enviado.",
            "fallback": True,
            "timestamp": datetime.utcnow().isoformat()
        }


# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    async def main():
        # Inicializar conector
        connector = PlatformConnector()

        # Verificar status
        print(f"Status: {connector.get_status()}")
        print(f"Conectado: {connector.is_connected()}")

        # Consultar worker
        response = await connector.query_worker(
            query="Qual é a alíquota de IPI?",
            worker_id="tax-expert"
        )
        print(f"Resposta: {json.dumps(response, indent=2)}")

        # Enviar documento
        doc_response = await connector.upload_document(
            document_content="Conteúdo do documento...",
            document_type="text",
            metadata={"source": "test"}
        )
        print(f"Upload: {json.dumps(doc_response, indent=2)}")

        # Fechar conexão
        connector.close()

    asyncio.run(main())
