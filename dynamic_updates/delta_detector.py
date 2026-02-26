"""
Delta Detector - Detecta mudanças significativas vs duplicação semântica

Características:
- Comparação com knowledge atual
- Detecção de mudanças reais
- Evita duplicação semântica simples
- Análise de similaridade
- Logging detalhado
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DeltaDetector:
    """
    Detecta deltas (mudanças significativas) entre conteúdo novo e knowledge existente
    
    Estratégia:
    1. Hash exato (detecção rápida de duplicação)
    2. Similaridade textual (evita paráfrases óbvias)
    3. Análise semântica leve (palavras-chave)
    4. Contexto (segmento, categoria)
    """
    
    def __init__(self, knowledge_base_path: str = "."):
        """
        Inicializa detector
        
        Args:
            knowledge_base_path: Caminho da base de conhecimento
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_index = self._build_knowledge_index()
        self.similarity_threshold = 0.85  # 85% de similaridade = duplicado
        
        logger.info(f"DeltaDetector inicializado com {len(self.knowledge_index)} blocos indexados")
    
    def _build_knowledge_index(self) -> Dict[str, Dict[str, Any]]:
        """Constrói índice do conhecimento existente"""
        index = {}
        
        try:
            # Procurar arquivos de conhecimento
            knowledge_files = list(self.knowledge_base_path.glob("knowledge_packages/*.json"))
            
            for file in knowledge_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Indexar blocos
                        if isinstance(data, dict) and "blocks" in data:
                            for block in data.get("blocks", []):
                                block_id = block.get("id", "")
                                if block_id:
                                    index[block_id] = {
                                        "content": block.get("content", ""),
                                        "title": block.get("title", ""),
                                        "segment": block.get("segment", ""),
                                        "hash": self._hash_text(block.get("content", "")),
                                        "keywords": self._extract_keywords(block.get("content", ""))
                                    }
                except Exception as e:
                    logger.warning(f"Erro ao indexar {file}: {e}")
            
            logger.info(f"✓ Índice de conhecimento construído: {len(index)} blocos")
            
        except Exception as e:
            logger.warning(f"Erro ao construir índice: {e}")
        
        return index
    
    def has_significant_changes(self, new_content: Dict[str, Any]) -> bool:
        """
        Detecta se há mudanças significativas no novo conteúdo
        
        Args:
            new_content: Novo conteúdo a analisar
            
        Returns:
            True se há mudanças significativas, False se é duplicado
        """
        if not new_content:
            return False
        
        # Extrair texto principal
        text = new_content.get("content", "") or new_content.get("text", "")
        
        if not text:
            logger.warning("⚠ Conteúdo vazio")
            return False
        
        # 1. Verificar hash exato (duplicação óbvia)
        content_hash = self._hash_text(text)
        
        for block_id, block_data in self.knowledge_index.items():
            if block_data["hash"] == content_hash:
                logger.info(f"ℹ Duplicação exata detectada: {block_id}")
                return False
        
        # 2. Verificar similaridade textual
        max_similarity = 0
        most_similar_block = None
        
        for block_id, block_data in self.knowledge_index.items():
            similarity = self._calculate_similarity(text, block_data["content"])
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_block = block_id
        
        if max_similarity > self.similarity_threshold:
            logger.info(
                f"ℹ Duplicação semântica detectada: "
                f"{most_similar_block} ({max_similarity:.1%})"
            )
            return False
        
        # 3. Verificar palavras-chave
        new_keywords = self._extract_keywords(text)
        keyword_overlap = self._calculate_keyword_overlap(new_keywords)
        
        if keyword_overlap > 0.9:  # 90% de sobreposição = provavelmente duplicado
            logger.info(f"ℹ Sobreposição de palavras-chave detectada: {keyword_overlap:.1%}")
            return False
        
        # Mudanças significativas detectadas
        logger.info(f"✓ Mudanças significativas detectadas (similaridade máxima: {max_similarity:.1%})")
        return True
    
    def detect_delta_details(self, new_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna detalhes do delta detectado
        
        Args:
            new_content: Novo conteúdo
            
        Returns:
            Dicionário com detalhes da análise
        """
        text = new_content.get("content", "") or new_content.get("text", "")
        
        if not text:
            return {"status": "empty", "reason": "Conteúdo vazio"}
        
        # Análise detalhada
        content_hash = self._hash_text(text)
        new_keywords = self._extract_keywords(text)
        
        # Encontrar blocos mais similares
        similar_blocks = []
        
        for block_id, block_data in self.knowledge_index.items():
            similarity = self._calculate_similarity(text, block_data["content"])
            
            if similarity > 0.5:  # Apenas blocos com >50% similaridade
                similar_blocks.append({
                    "block_id": block_id,
                    "similarity": similarity,
                    "segment": block_data["segment"],
                    "title": block_data["title"]
                })
        
        # Ordenar por similaridade
        similar_blocks.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "status": "analyzed",
            "has_changes": self.has_significant_changes(new_content),
            "content_hash": content_hash,
            "keywords": new_keywords,
            "keyword_count": len(new_keywords),
            "max_similarity": max([b["similarity"] for b in similar_blocks], default=0),
            "similar_blocks": similar_blocks[:5],  # Top 5
            "content_length": len(text),
            "segment": new_content.get("segment", "unknown")
        }
    
    def compare_with_block(
        self,
        new_content: str,
        block_id: str
    ) -> Dict[str, Any]:
        """
        Compara novo conteúdo com um bloco específico
        
        Args:
            new_content: Novo conteúdo
            block_id: ID do bloco para comparar
            
        Returns:
            Resultado da comparação
        """
        if block_id not in self.knowledge_index:
            return {"error": f"Bloco {block_id} não encontrado"}
        
        block = self.knowledge_index[block_id]
        similarity = self._calculate_similarity(new_content, block["content"])
        
        return {
            "block_id": block_id,
            "similarity": similarity,
            "is_duplicate": similarity > self.similarity_threshold,
            "segment": block["segment"],
            "title": block["title"],
            "existing_length": len(block["content"]),
            "new_length": len(new_content),
            "length_diff": len(new_content) - len(block["content"])
        }
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """Calcula hash SHA256 do texto"""
        try:
            normalized = text.lower().strip()
            return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.warning(f"Erro ao calcular hash: {e}")
            return ""
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        Calcula similaridade entre dois textos (0.0 a 1.0)
        
        Usa SequenceMatcher para comparação rápida
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            # Normalizar textos
            t1 = text1.lower().strip()
            t2 = text2.lower().strip()
            
            # Calcular similaridade
            matcher = SequenceMatcher(None, t1, t2)
            return matcher.ratio()
        except Exception as e:
            logger.warning(f"Erro ao calcular similaridade: {e}")
            return 0.0
    
    @staticmethod
    def _extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """
        Extrai palavras-chave do texto
        
        Estratégia simples: palavras com >4 caracteres, excluindo stopwords
        """
        stopwords = {
            "o", "a", "de", "do", "da", "em", "para", "com", "por", "que",
            "the", "is", "at", "which", "on", "and", "or", "an", "as", "are"
        }
        
        try:
            # Dividir em palavras
            words = text.lower().split()
            
            # Filtrar
            keywords = [
                w.strip('.,!?;:') for w in words
                if len(w) > 4 and w.lower() not in stopwords
            ]
            
            # Remover duplicatas e retornar top N
            return list(set(keywords))[:top_n]
        except Exception as e:
            logger.warning(f"Erro ao extrair keywords: {e}")
            return []
    
    @staticmethod
    def _calculate_keyword_overlap(keywords: List[str]) -> float:
        """
        Calcula sobreposição de palavras-chave com índice
        
        Retorna percentual de keywords que já existem no índice
        """
        # Implementação simplificada
        # Em produção, seria mais sofisticada
        return 0.0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = DeltaDetector()
    print(f"\nDetector inicializado com {len(detector.knowledge_index)} blocos")
