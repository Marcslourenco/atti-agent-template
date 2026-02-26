"""
Scraper Adapter - Adapta saída de scraper para formato de knowledge

Características:
- Converter HTML/texto para blocos de conhecimento
- Validar e normalizar
- Enriquecer com metadata
- Integrar com update_sandbox
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ScraperAdapter:
    """
    Adapta saída de scraper para formato de knowledge
    
    Fluxo:
    1. Receber dados do scraper
    2. Validar estrutura
    3. Normalizar conteúdo
    4. Enriquecer com metadata
    5. Salvar em sandbox
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa adapter
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.sandbox_dir = self.base_path / "dynamic_updates" / "update_sandbox"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("ScraperAdapter inicializado")
    
    def adapt_scraped_content(
        self,
        scraped_data: Dict[str, Any],
        segment: str,
        source_url: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Adapta conteúdo do scraper para formato de knowledge
        
        Args:
            scraped_data: Dados do scraper
            segment: Segmento de negócio
            source_url: URL de origem
            
        Returns:
            (sucesso, conteúdo adaptado)
        """
        try:
            # Validar dados
            if not scraped_data:
                return False, {"error": "Dados vazios"}
            
            # Extrair campos
            title = scraped_data.get("title", "")
            content = scraped_data.get("content", "")
            
            if not title or not content:
                return False, {"error": "Title ou content ausentes"}
            
            # Normalizar
            title = self._normalize_text(title)
            content = self._normalize_text(content)
            
            # Enriquecer
            adapted = {
                "title": title,
                "content": content,
                "segment": segment.lower(),
                "category": scraped_data.get("category", "general"),
                "tags": self._extract_tags(scraped_data),
                "source": source_url or scraped_data.get("source", "scraper"),
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "original_url": source_url,
                    "scraper_version": "1.0",
                    "confidence": scraped_data.get("confidence", 0.8)
                }
            }
            
            logger.info(f"✓ Conteúdo adaptado ({len(content)} caracteres)")
            return True, adapted
            
        except Exception as e:
            logger.error(f"✗ Erro ao adaptar conteúdo: {e}")
            return False, {"error": str(e)}
    
    def adapt_batch(
        self,
        scraped_items: List[Dict[str, Any]],
        segment: str
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Adapta lote de itens
        
        Args:
            scraped_items: Lista de itens do scraper
            segment: Segmento
            
        Returns:
            (sucesso, falhas, itens adaptados)
        """
        success_count = 0
        fail_count = 0
        adapted_items = []
        
        for i, item in enumerate(scraped_items):
            success, adapted = self.adapt_scraped_content(
                item,
                segment,
                item.get("url")
            )
            
            if success:
                success_count += 1
                adapted_items.append(adapted)
            else:
                fail_count += 1
                logger.warning(f"Item {i} falhou: {adapted.get('error')}")
        
        logger.info(f"✓ Lote adaptado: {success_count} sucesso, {fail_count} falhas")
        return success_count, fail_count, adapted_items
    
    def save_to_sandbox(
        self,
        adapted_content: Dict[str, Any],
        file_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Salva conteúdo adaptado em sandbox
        
        Args:
            adapted_content: Conteúdo adaptado
            file_id: ID do arquivo (opcional, auto-gerado)
            
        Returns:
            (sucesso, caminho do arquivo)
        """
        try:
            # Gerar ID se não fornecido
            if not file_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_id = f"scraped_{timestamp}"
            
            # Salvar em sandbox
            file_path = self.sandbox_dir / f"{file_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(adapted_content, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Salvo em sandbox: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            logger.error(f"✗ Erro ao salvar em sandbox: {e}")
            return False, str(e)
    
    def save_batch_to_sandbox(
        self,
        adapted_items: List[Dict[str, Any]],
        batch_id: Optional[str] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Salva lote em sandbox
        
        Args:
            adapted_items: Itens adaptados
            batch_id: ID do lote (opcional)
            
        Returns:
            (salvo, falhas, caminhos)
        """
        saved_count = 0
        fail_count = 0
        file_paths = []
        
        for i, item in enumerate(adapted_items):
            file_id = f"{batch_id or 'batch'}_{i}" if batch_id else None
            success, path = self.save_to_sandbox(item, file_id)
            
            if success:
                saved_count += 1
                file_paths.append(path)
            else:
                fail_count += 1
        
        logger.info(f"✓ Lote salvo: {saved_count} arquivos, {fail_count} falhas")
        return saved_count, fail_count, file_paths
    
    def get_sandbox_status(self) -> Dict[str, Any]:
        """Retorna status do sandbox"""
        files = list(self.sandbox_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        
        return {
            "sandbox_path": str(self.sandbox_dir),
            "files_count": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "status": "ready" if files else "empty"
        }
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normaliza texto"""
        if not text:
            return ""
        
        import re
        import unicodedata
        
        # Remover HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalizar Unicode
        text = unicodedata.normalize('NFC', text)
        
        # Limpar espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def _extract_tags(data: Dict[str, Any]) -> List[str]:
        """Extrai tags do conteúdo"""
        tags = []
        
        # Tags fornecidas
        if "tags" in data:
            if isinstance(data["tags"], list):
                tags.extend(data["tags"])
            elif isinstance(data["tags"], str):
                tags.extend(data["tags"].split(","))
        
        # Extrair de categoria
        if "category" in data:
            category = str(data["category"]).lower().strip()
            if category:
                tags.append(category)
        
        # Remover duplicatas e limpar
        tags = list(set(t.lower().strip() for t in tags if t))
        
        return tags[:10]  # Limitar a 10 tags


class ContentEnricher:
    """
    Enriquece conteúdo adaptado com metadata adicional
    
    Adiciona:
    - Relevância
    - Palavras-chave
    - Relacionamentos
    - Qualidade
    """
    
    def __init__(self):
        """Inicializa enriquecedor"""
        logger.info("ContentEnricher inicializado")
    
    def enrich(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece conteúdo
        
        Args:
            content: Conteúdo adaptado
            
        Returns:
            Conteúdo enriquecido
        """
        enriched = {
            **content,
            "enrichment": {
                "keywords": self._extract_keywords(content.get("content", "")),
                "relevance_score": self._calculate_relevance(content),
                "quality_score": self._calculate_quality(content),
                "reading_time_minutes": self._estimate_reading_time(content.get("content", "")),
                "complexity": self._estimate_complexity(content)
            }
        }
        
        return enriched
    
    @staticmethod
    def _extract_keywords(text: str, limit: int = 10) -> List[str]:
        """Extrai palavras-chave"""
        import re
        
        # Palavras comuns a ignorar
        stopwords = {
            "o", "a", "de", "do", "da", "em", "para", "com", "por", "que",
            "é", "são", "foi", "foram", "e", "ou", "não", "um", "uma"
        }
        
        # Extrair palavras
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Filtrar stopwords e contar frequência
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Retornar top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:limit]]
    
    @staticmethod
    def _calculate_relevance(content: Dict[str, Any]) -> float:
        """Calcula score de relevância (0-1)"""
        score = 0.5  # Base
        
        # Aumentar se tem título
        if content.get("title"):
            score += 0.2
        
        # Aumentar se tem conteúdo suficiente
        if len(content.get("content", "")) > 100:
            score += 0.2
        
        # Aumentar se tem tags
        if content.get("tags"):
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def _calculate_quality(content: Dict[str, Any]) -> float:
        """Calcula score de qualidade (0-1)"""
        score = 0.5  # Base
        
        # Aumentar se tem metadata
        if content.get("metadata"):
            score += 0.2
        
        # Aumentar se tem source
        if content.get("source"):
            score += 0.15
        
        # Aumentar se tem categoria
        if content.get("category"):
            score += 0.15
        
        return min(score, 1.0)
    
    @staticmethod
    def _estimate_reading_time(text: str) -> int:
        """Estima tempo de leitura em minutos"""
        words = len(text.split())
        # Média de 200 palavras por minuto
        return max(1, words // 200)
    
    @staticmethod
    def _estimate_complexity(content: Dict[str, Any]) -> str:
        """Estima complexidade do conteúdo"""
        content_len = len(content.get("content", ""))
        
        if content_len < 200:
            return "simple"
        elif content_len < 1000:
            return "intermediate"
        else:
            return "advanced"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    adapter = ScraperAdapter()
    
    # Teste
    test_data = {
        "title": "Teste de Scraping",
        "content": "Este é um conteúdo de teste com informações importantes.",
        "category": "hospital",
        "tags": ["teste", "scraping"]
    }
    
    success, adapted = adapter.adapt_scraped_content(test_data, "hospital")
    print(f"\nAdaptado: {adapted}")
    
    if success:
        saved, path = adapter.save_to_sandbox(adapted)
        print(f"Salvo: {path}")
