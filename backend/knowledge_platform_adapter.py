"""
Knowledge Platform Adapter v2.1.0
Integração leve entre knowledge_loader_v2_1_0 e platform_connector

Características:
- Auto-detecção do manifest v2.1.0
- Fallback para loader anterior se v2.1.0 não existir
- Sincronização com Digital Worker Platform
- Zero impacto em funcionalidades existentes
- Backward compatibility 100%
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeManifestDetector:
    """Detecta qual versão do knowledge manifest está disponível"""
    
    @staticmethod
    def detect_manifest_version(base_path: str = ".") -> Optional[str]:
        """
        Detecta versão do manifest disponível
        
        Prioridade:
        1. knowledge_manifest_v2_1_0.json (novo)
        2. knowledge_manifest.json (legado)
        3. Nenhum
        
        Returns:
            "v2.1.0", "legacy", ou None
        """
        base = Path(base_path)
        
        # Verificar v2.1.0
        if (base / "knowledge_manifest_v2_1_0.json").exists():
            logger.info("✓ Knowledge manifest v2.1.0 detectado")
            return "v2.1.0"
        
        # Verificar legado
        if (base / "knowledge_manifest.json").exists():
            logger.info("✓ Knowledge manifest legado detectado")
            return "legacy"
        
        logger.warning("⚠ Nenhum knowledge manifest detectado")
        return None


class KnowledgeLoaderFactory:
    """Factory para carregar versão apropriada do loader"""
    
    @staticmethod
    def create_loader(base_path: str = "."):
        """
        Cria loader apropriado baseado no manifest disponível
        
        Args:
            base_path: Caminho base do projeto
            
        Returns:
            Instância do loader (v2.1.0 ou legado)
        """
        version = KnowledgeManifestDetector.detect_manifest_version(base_path)
        
        if version == "v2.1.0":
            try:
                from knowledge_loader_v2_1_0 import KnowledgeLoader
                logger.info("✓ Usando KnowledgeLoader v2.1.0")
                return KnowledgeLoader(base_path=base_path, auto_load=False)
            except ImportError:
                logger.warning("⚠ KnowledgeLoader v2.1.0 não disponível, usando fallback")
                return None
        
        elif version == "legacy":
            logger.info("✓ Usando loader legado")
            # Importar loader legado se existir
            try:
                from knowledge_loader import KnowledgeLoader as LegacyLoader
                return LegacyLoader(base_path=base_path)
            except ImportError:
                logger.warning("⚠ Loader legado não disponível")
                return None
        
        logger.warning("⚠ Nenhum loader disponível")
        return None


class KnowledgePlatformAdapter:
    """
    Adapter que conecta knowledge_loader com platform_connector
    
    Funcionalidades:
    - Auto-load do manifest v2.1.0
    - Sincronização com plataforma
    - Fallback gracioso
    - Backward compatibility
    """
    
    def __init__(self, base_path: str = ".", platform_connector=None):
        """
        Inicializa o adapter
        
        Args:
            base_path: Caminho base do projeto
            platform_connector: Instância de PlatformConnector (opcional)
        """
        self.base_path = base_path
        self.platform_connector = platform_connector
        self.loader = KnowledgeLoaderFactory.create_loader(base_path)
        self.manifest_version = KnowledgeManifestDetector.detect_manifest_version(base_path)
        
        logger.info(
            f"KnowledgePlatformAdapter inicializado "
            f"(manifest={self.manifest_version}, "
            f"platform={'enabled' if platform_connector else 'disabled'})"
        )
    
    def load_knowledge(self) -> bool:
        """
        Carrega pacotes de conhecimento
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.loader:
            logger.warning("⚠ Loader não disponível")
            return False
        
        try:
            self.loader.load_all_packages()
            logger.info("✓ Pacotes de conhecimento carregados")
            return True
        except Exception as e:
            logger.error(f"✗ Erro ao carregar pacotes: {e}")
            return False
    
    def sync_with_platform(self) -> bool:
        """
        Sincroniza conhecimento com plataforma
        
        Returns:
            True se sucesso ou plataforma desativada
        """
        if not self.platform_connector:
            logger.info("ℹ Platform connector não disponível")
            return True
        
        if not self.loader:
            logger.warning("⚠ Loader não disponível para sincronização")
            return False
        
        try:
            # Obter estatísticas do conhecimento
            stats = self._get_knowledge_stats()
            
            # Enviar para plataforma
            result = self.platform_connector.upload_document(
                document_content=json.dumps(stats),
                document_type="knowledge_metadata"
            )
            
            if result and result.get("success"):
                logger.info("✓ Sincronização com plataforma concluída")
                return True
            else:
                logger.warning("⚠ Sincronização com plataforma falhou (fallback ativo)")
                return True  # Não é falha crítica
                
        except Exception as e:
            logger.warning(f"⚠ Erro ao sincronizar com plataforma: {e} (fallback ativo)")
            return True  # Fallback gracioso
    
    def _get_knowledge_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do conhecimento carregado"""
        if not self.loader:
            return {}
        
        try:
            # Para v2.1.0
            if hasattr(self.loader, 'get_statistics'):
                return self.loader.get_statistics()
            
            # Fallback: contar blocos
            segments = self.loader.list_segments() if hasattr(self.loader, 'list_segments') else []
            total_blocks = 0
            
            for segment in segments:
                try:
                    blocks = self.loader.get_blocks_by_segment(segment)
                    total_blocks += len(blocks)
                except:
                    pass
            
            return {
                "manifest_version": self.manifest_version,
                "total_segments": len(segments),
                "total_blocks": total_blocks,
                "segments": segments
            }
        except Exception as e:
            logger.warning(f"⚠ Erro ao obter estatísticas: {e}")
            return {"error": str(e)}
    
    def query_knowledge(self, query: str, segment: Optional[str] = None) -> List[Dict]:
        """
        Consulta base de conhecimento
        
        Args:
            query: Texto da consulta
            segment: Segmento específico (opcional)
            
        Returns:
            Lista de blocos de conhecimento relevantes
        """
        if not self.loader:
            logger.warning("⚠ Loader não disponível")
            return []
        
        try:
            # Para v2.1.0 com busca
            if hasattr(self.loader, 'search_blocks'):
                return self.loader.search_blocks(query, segment)
            
            # Fallback: retornar blocos do segmento
            if segment and hasattr(self.loader, 'get_blocks_by_segment'):
                return self.loader.get_blocks_by_segment(segment)
            
            logger.warning("⚠ Método de busca não disponível")
            return []
            
        except Exception as e:
            logger.error(f"✗ Erro ao consultar conhecimento: {e}")
            return []
    
    def get_regulatory_blocks(self, segment: Optional[str] = None) -> List[Dict]:
        """
        Obtém blocos regulatórios
        
        Args:
            segment: Segmento específico (opcional)
            
        Returns:
            Lista de blocos regulatórios
        """
        if not self.loader:
            return []
        
        try:
            if hasattr(self.loader, 'get_regulatory_blocks'):
                return self.loader.get_regulatory_blocks(segment)
            return []
        except Exception as e:
            logger.error(f"✗ Erro ao obter blocos regulatórios: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do adapter"""
        return {
            "adapter": "KnowledgePlatformAdapter",
            "manifest_version": self.manifest_version,
            "loader_available": self.loader is not None,
            "platform_connected": (
                self.platform_connector is not None and 
                self.platform_connector.status.value == "connected"
            ),
            "status": "healthy" if self.loader else "degraded"
        }


# Função de conveniência para inicialização
def initialize_knowledge_adapter(
    base_path: str = ".",
    platform_connector=None
) -> KnowledgePlatformAdapter:
    """
    Inicializa adapter de conhecimento com integração de plataforma
    
    Args:
        base_path: Caminho base do projeto
        platform_connector: Instância de PlatformConnector (opcional)
        
    Returns:
        Instância configurada de KnowledgePlatformAdapter
    """
    adapter = KnowledgePlatformAdapter(base_path, platform_connector)
    
    # Carregar conhecimento
    adapter.load_knowledge()
    
    # Sincronizar com plataforma
    adapter.sync_with_platform()
    
    return adapter


if __name__ == "__main__":
    # Teste local
    logging.basicConfig(level=logging.INFO)
    
    adapter = initialize_knowledge_adapter()
    print(f"\nStatus: {adapter.get_health_status()}")
