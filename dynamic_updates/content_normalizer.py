"""
Content Normalizer - Limpa HTML, normaliza encoding, prepara para classificação

Características:
- Remoção de HTML/tags
- Normalização de encoding
- Limpeza de espaços em branco
- Validação de estrutura
- Preparação para classificação futura
"""

import re
import logging
from typing import Dict, Any, Optional, List
from html.parser import HTMLParser
import unicodedata

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    """Remove tags HTML mantendo conteúdo"""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, d):
        self.text.append(d)
    
    def get_data(self):
        return ''.join(self.text)


class ContentNormalizer:
    """
    Normaliza conteúdo para padrão de conhecimento
    
    Fluxo:
    1. Detectar encoding
    2. Remover HTML
    3. Normalizar Unicode
    4. Limpar espaços
    5. Validar estrutura
    """
    
    def __init__(self):
        """Inicializa normalizador"""
        self.html_stripper = HTMLStripper()
        logger.info("ContentNormalizer inicializado")
    
    def normalize(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza conteúdo completo
        
        Args:
            content: Conteúdo bruto
            
        Returns:
            Conteúdo normalizado
        """
        try:
            normalized = {
                "title": self._normalize_text(content.get("title", "")),
                "content": self._normalize_text(content.get("content", "")),
                "segment": self._normalize_segment(content.get("segment", "")),
                "category": self._normalize_category(content.get("category", "")),
                "tags": self._normalize_tags(content.get("tags", [])),
                "metadata": self._normalize_metadata(content.get("metadata", {})),
                "source": content.get("source", "unknown"),
                "language": self._detect_language(content.get("content", "")),
                "encoding": "utf-8"
            }
            
            # Validar estrutura
            if not self._validate_structure(normalized):
                logger.warning("⚠ Conteúdo normalizado não passou na validação")
            
            logger.info(f"✓ Conteúdo normalizado ({len(normalized['content'])} caracteres)")
            return normalized
            
        except Exception as e:
            logger.error(f"✗ Erro ao normalizar conteúdo: {e}")
            return content
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto
        
        Passos:
        1. Converter para string
        2. Remover HTML
        3. Normalizar Unicode
        4. Limpar espaços
        """
        if not isinstance(text, str):
            text = str(text)
        
        try:
            # 1. Remover HTML
            text = self._strip_html(text)
            
            # 2. Normalizar Unicode (NFC)
            text = unicodedata.normalize('NFC', text)
            
            # 3. Remover caracteres de controle
            text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\r\t')
            
            # 4. Limpar espaços múltiplos
            text = re.sub(r'\s+', ' ', text)
            
            # 5. Remover espaços nas extremidades
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Erro ao normalizar texto: {e}")
            return text
    
    def _normalize_segment(self, segment: str) -> str:
        """Normaliza nome do segmento"""
        if not segment:
            return "general"
        
        # Converter para snake_case
        segment = segment.lower().strip()
        segment = re.sub(r'[^a-z0-9_]', '_', segment)
        segment = re.sub(r'_+', '_', segment)
        
        return segment
    
    def _normalize_category(self, category: str) -> str:
        """Normaliza categoria"""
        if not category:
            return "uncategorized"
        
        return category.lower().strip()
    
    def _normalize_tags(self, tags: Any) -> List[str]:
        """Normaliza tags"""
        if not tags:
            return []
        
        if isinstance(tags, str):
            tags = [tags]
        
        if not isinstance(tags, list):
            tags = [str(tags)]
        
        # Normalizar cada tag
        normalized = []
        for tag in tags:
            tag = str(tag).lower().strip()
            if tag and len(tag) > 2:
                normalized.append(tag)
        
        return list(set(normalized))  # Remover duplicatas
    
    def _normalize_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Normaliza metadata"""
        if not isinstance(metadata, dict):
            return {}
        
        normalized = {}
        
        for key, value in metadata.items():
            # Apenas manter metadata válida
            if isinstance(value, (str, int, float, bool, list, dict)):
                normalized[key] = value
        
        return normalized
    
    def _detect_language(self, text: str) -> str:
        """
        Detecta idioma do texto (simples)
        
        Estratégia: contar palavras em português vs inglês
        """
        if not text:
            return "unknown"
        
        # Palavras comuns em português
        pt_words = {"o", "a", "de", "do", "da", "em", "para", "com", "por", "que", "é", "são"}
        
        # Palavras comuns em inglês
        en_words = {"the", "is", "at", "which", "on", "and", "or", "an", "as", "are"}
        
        words = text.lower().split()
        
        pt_count = sum(1 for w in words if w in pt_words)
        en_count = sum(1 for w in words if w in en_words)
        
        if pt_count > en_count:
            return "pt-BR"
        elif en_count > pt_count:
            return "en"
        else:
            return "unknown"
    
    def _validate_structure(self, content: Dict[str, Any]) -> bool:
        """
        Valida estrutura do conteúdo normalizado
        
        Requisitos:
        - title: não vazio
        - content: não vazio
        - segment: válido
        """
        try:
            # Validar campos obrigatórios
            if not content.get("title"):
                logger.warning("⚠ Title vazio")
                return False
            
            if not content.get("content"):
                logger.warning("⚠ Content vazio")
                return False
            
            if len(content.get("title", "")) < 3:
                logger.warning("⚠ Title muito curto")
                return False
            
            if len(content.get("content", "")) < 10:
                logger.warning("⚠ Content muito curto")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro na validação: {e}")
            return False
    
    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove tags HTML do texto"""
        try:
            stripper = HTMLStripper()
            stripper.feed(text)
            return stripper.get_data()
        except Exception as e:
            logger.warning(f"Erro ao remover HTML: {e}")
            return text
    
    def normalize_batch(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza lote de conteúdos
        
        Args:
            contents: Lista de conteúdos
            
        Returns:
            Lista de conteúdos normalizados
        """
        normalized = []
        
        for i, content in enumerate(contents):
            try:
                normalized.append(self.normalize(content))
            except Exception as e:
                logger.error(f"Erro ao normalizar item {i}: {e}")
        
        logger.info(f"✓ {len(normalized)}/{len(contents)} itens normalizados com sucesso")
        return normalized
    
    def get_statistics(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Retorna estatísticas do conteúdo"""
        return {
            "title_length": len(content.get("title", "")),
            "content_length": len(content.get("content", "")),
            "tags_count": len(content.get("tags", [])),
            "segment": content.get("segment", "unknown"),
            "language": content.get("language", "unknown"),
            "has_metadata": bool(content.get("metadata")),
            "encoding": content.get("encoding", "unknown")
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    normalizer = ContentNormalizer()
    
    # Teste
    test_content = {
        "title": "  <b>Teste de Normalização</b>  ",
        "content": "Este é um <p>conteúdo</p> de teste com   espaços múltiplos.",
        "segment": "HOSPITAL-PRIVADO",
        "tags": ["teste", "normalização", "teste"],
        "metadata": {"source": "web"}
    }
    
    normalized = normalizer.normalize(test_content)
    print(f"\nNormalizado: {normalized}")
    print(f"Estatísticas: {normalizer.get_statistics(normalized)}")
