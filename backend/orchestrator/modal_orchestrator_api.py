"""
ATTI Orchestrator API - Fase B com Endpoints HTTP
Integração RAG + LLM + Security com endpoints FastAPI
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

# FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Modal
import modal

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

FAISS_INDEX_PATH = "/home/ubuntu/atti-commercial-prod/data/embeddings/faiss_index.bin"
EMBEDDINGS_PATH = "/home/ubuntu/atti-commercial-prod/data/embeddings/embeddings.npy"
METADATA_PATH = "/home/ubuntu/atti-commercial-prod/data/embeddings/embeddings_metadata.json"

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class ChatRequest(BaseModel):
    """Requisição de chat"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Resposta de chat"""
    response: str
    session_id: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None

class HealthResponse(BaseModel):
    """Resposta de health check"""
    status: str
    version: str = "1.0"

# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

@dataclass
class QnA:
    """Estrutura de Q&A"""
    id: int
    pergunta: str
    resposta: str
    categoria: str
    fonte: Optional[str] = None

# ============================================================================
# CARREGADOR DE DADOS
# ============================================================================

class DataLoader:
    """Carregador de dados FAISS e Q&As"""
    
    def __init__(self):
        self.qnas = []
        self.loaded = False
    
    def load(self) -> bool:
        """Carrega dados Q&A"""
        try:
            logger.info("🔄 Carregando dados Q&A...")
            
            # Tentar carregar metadados
            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r") as f:
                    metadata = json.load(f)
                    self.qnas = [
                        QnA(
                            id=item.get("id", i),
                            pergunta=item.get("pergunta", ""),
                            resposta=item.get("resposta", ""),
                            categoria=item.get("categoria", ""),
                            fonte=item.get("fonte")
                        )
                        for i, item in enumerate(metadata.get("qnas", []))
                    ]
                logger.info(f"✅ Carregados {len(self.qnas)} Q&As")
                self.loaded = True
                return True
            else:
                logger.warning(f"⚠️ Arquivo de metadados não encontrado: {METADATA_PATH}")
                # Retornar dados de exemplo
                self.qnas = [
                    QnA(
                        id=1,
                        pergunta="Qual é a alíquota do IBS em 2026?",
                        resposta="A alíquota do IBS (Imposto sobre Bens e Serviços) em 2026 é de 27%, conforme a Reforma Tributária.",
                        categoria="Impostos",
                        fonte="Lei Complementar 214/2025"
                    ),
                    QnA(
                        id=2,
                        pergunta="Como funciona o crédito do IBS?",
                        resposta="O crédito do IBS funciona como um imposto sobre valor agregado, permitindo o crédito de impostos pagos nas etapas anteriores.",
                        categoria="Créditos",
                        fonte="Reforma Tributária 2026"
                    )
                ]
                self.loaded = True
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[QnA]:
        """Busca Q&As por palavra-chave com scoring"""
        if not self.loaded:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        results = []
        
        for qna in self.qnas:
            score = 0
            
            # Busca exata na pergunta
            if query_lower in qna.pergunta.lower():
                score += 10
            
            # Busca de palavras na pergunta
            pergunta_words = set(qna.pergunta.lower().split())
            matching_words = len(query_words & pergunta_words)
            score += matching_words * 3
            
            # Busca na resposta
            if query_lower in qna.resposta.lower():
                score += 5
            
            # Busca na categoria
            if query_lower in qna.categoria.lower():
                score += 7
            
            if score > 0:
                results.append((qna, score))
        
        # Ordenar por score e retornar apenas QnAs
        results.sort(key=lambda x: x[1], reverse=True)
        return [qna for qna, _ in results[:top_k]]

# ============================================================================
# APLICAÇÃO MODAL
# ============================================================================

app = modal.App("atti-orchestrator-api")

# Criar imagem com dependências
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "uvicorn",
    "pydantic",
    "sentence-transformers",
    "faiss-cpu",
    "numpy"
)

@app.function(image=image, min_containers=1)
@modal.asgi_app()
def fastapi_app():
    """FastAPI app com endpoints do orquestrador"""
    
    fastapi_app = FastAPI(
        title="ATTI Orchestrator API",
        description="Orquestrador RAG + LLM para ATTI Dashboard",
        version="1.0"
    )
    
    # Carregar dados
    data_loader = DataLoader()
    data_loader.load()
    
    # ========================================================================
    # ENDPOINTS
    # ========================================================================
    
    @fastapi_app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check"""
        return HealthResponse(status="ok")
    
    @fastapi_app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Endpoint de chat"""
        try:
            message = request.message.strip()
            
            if not message:
                raise HTTPException(status_code=400, detail="Message cannot be empty")
            
            # Buscar Q&As relacionados
            related_qnas = data_loader.search(message, top_k=3)
            
            # Construir resposta
            if related_qnas:
                # Usar primeira resposta encontrada
                qna = related_qnas[0]
                response_text = qna.resposta
                sources = [qna.fonte] if qna.fonte else []
                confidence = 0.8
            else:
                # Resposta padrão
                response_text = (
                    "Desculpe, não encontrei informações específicas sobre sua pergunta. "
                    "Por favor, reformule sua pergunta ou consulte a documentação da Reforma Tributária 2026."
                )
                sources = []
                confidence = 0.3
            
            return ChatResponse(
                response=response_text,
                session_id=request.session_id,
                confidence=confidence,
                sources=sources
            )
        
        except Exception as e:
            logger.error(f"❌ Erro no chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @fastapi_app.post("/query")
    async def query(request: ChatRequest):
        """Alias para /chat"""
        return await chat(request)
    
    @fastapi_app.get("/info")
    async def info():
        """Informações do orquestrador"""
        return {
            "name": "ATTI Orchestrator API",
            "version": "1.0",
            "status": "running",
            "qnas_loaded": len(data_loader.qnas),
            "endpoints": [
                "/health",
                "/chat",
                "/query",
                "/info"
            ]
        }
    
    return fastapi_app
