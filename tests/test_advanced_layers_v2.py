"""
Test Suite for Advanced Layers v2.0

Testa:
- Dynamic Update Engine
- Avatar Theme Engine
- Avatar Registry
- Scraping Integration
"""

import pytest
import logging
from pathlib import Path
import tempfile
import json
from datetime import datetime

# Importar módulos
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dynamic_updates.update_scheduler import UpdateScheduler
from dynamic_updates.delta_detector import DeltaDetector
from dynamic_updates.content_normalizer import ContentNormalizer
from dynamic_updates.update_promoter import UpdatePromoter
from avatar_theme_engine.theme_loader import ThemeLoader, Theme
from avatar_theme_engine.schema_validator import SchemaValidator
from avatar_registry.registry_manager import RegistryManager
from avatar_registry.avatar_validator import AvatarValidator
from scraping_integration.scraper_adapter import ScraperAdapter, ContentEnricher

logger = logging.getLogger(__name__)


class TestDynamicUpdateEngine:
    """Testa Dynamic Update Engine"""
    
    def test_update_scheduler_initialization(self):
        """Testa inicialização do scheduler"""
        scheduler = UpdateScheduler()
        assert scheduler is not None
        assert scheduler.get_health_status()["status"] == "healthy"
    
    def test_delta_detector_initialization(self):
        """Testa inicialização do detector"""
        detector = DeltaDetector()
        assert detector is not None
        assert detector.get_health_status()["status"] == "healthy"
    
    def test_content_normalizer_text_normalization(self):
        """Testa normalização de texto"""
        normalizer = ContentNormalizer()
        
        test_content = {
            "title": "  <b>Teste</b>  ",
            "content": "Conteúdo   com   espaços",
            "segment": "HOSPITAL",
            "tags": ["teste", "teste"]
        }
        
        normalized = normalizer.normalize(test_content)
        
        assert normalized["title"] == "Teste"
        assert "espaços" in normalized["content"]
        assert normalized["segment"] == "hospital"
        assert len(normalized["tags"]) == 1  # Duplicata removida
    
    def test_update_promoter_preview(self):
        """Testa preview de promoção"""
        promoter = UpdatePromoter()
        preview = promoter.preview_promotion()
        
        assert "status" in preview
        assert "problems" in preview
        assert "current_version" in preview


class TestAvatarThemeEngine:
    """Testa Avatar Theme Engine"""
    
    def test_theme_loader_initialization(self):
        """Testa inicialização do loader"""
        loader = ThemeLoader()
        assert loader is not None
        assert loader.default_theme is not None
    
    def test_theme_creation_and_validation(self):
        """Testa criação e validação de tema"""
        theme = Theme(
            id="test_theme",
            name="Test Theme",
            primary_color="#2563eb",
            secondary_color="#64748b",
            accent_color="#f59e0b",
            background_color="#ffffff",
            text_color="#1f2937",
            font_style="sans-serif",
            avatar_style="professional",
            border_radius="8px",
            shadow_intensity=0.5,
            animation_speed=1.0
        )
        
        valid, errors = theme.validate()
        assert valid
        assert len(errors) == 0
    
    def test_schema_validator_theme_validation(self):
        """Testa validação de schema de tema"""
        valid_theme = {
            "id": "test",
            "name": "Test",
            "primary_color": "#2563eb",
            "secondary_color": "#64748b",
            "accent_color": "#f59e0b",
            "background_color": "#ffffff",
            "text_color": "#1f2937",
            "font_style": "sans-serif",
            "avatar_style": "professional",
            "border_radius": "8px",
            "shadow_intensity": 0.5,
            "animation_speed": 1.0
        }
        
        valid, errors = SchemaValidator.validate_theme(valid_theme)
        assert valid
        assert len(errors) == 0
    
    def test_schema_validator_invalid_theme(self):
        """Testa validação com tema inválido"""
        invalid_theme = {
            "id": "test",
            # Faltam campos obrigatórios
        }
        
        valid, errors = SchemaValidator.validate_theme(invalid_theme)
        assert not valid
        assert len(errors) > 0


class TestAvatarRegistry:
    """Testa Avatar Registry"""
    
    def test_registry_manager_initialization(self):
        """Testa inicialização do manager"""
        manager = RegistryManager()
        assert manager is not None
        assert manager.get_health_status()["status"] == "healthy"
    
    def test_register_avatar(self):
        """Testa registro de avatar"""
        manager = RegistryManager()
        
        success, msg = manager.register_avatar(
            "test_avatar",
            "Test Avatar",
            "hospital",
            "professional",
            "Test description"
        )
        
        assert success
        assert "test_avatar" in manager.registry
    
    def test_avatar_validator_initialization(self):
        """Testa inicialização do validador"""
        validator = AvatarValidator()
        assert validator is not None
        report = validator.get_validation_report()
        assert report["status"] == "ready"
    
    def test_avatar_entry_validation(self):
        """Testa validação de entrada de avatar"""
        validator = AvatarValidator()
        
        entry = {
            "id": "avatar_001",
            "name": "Test Avatar",
            "version": "1.0.0",
            "segment": "hospital",
            "theme_id": "professional",
            "status": "active",
            "description": "Test"
        }
        
        valid, errors, warnings = validator.validate_avatar_entry(entry)
        assert valid
        assert len(errors) == 0


class TestScrapingIntegration:
    """Testa Scraping Integration"""
    
    def test_scraper_adapter_initialization(self):
        """Testa inicialização do adapter"""
        adapter = ScraperAdapter()
        assert adapter is not None
        status = adapter.get_sandbox_status()
        assert "sandbox_path" in status
    
    def test_adapt_scraped_content(self):
        """Testa adaptação de conteúdo"""
        adapter = ScraperAdapter()
        
        test_data = {
            "title": "Test Content",
            "content": "This is test content with information.",
            "category": "hospital",
            "tags": ["test"]
        }
        
        success, adapted = adapter.adapt_scraped_content(test_data, "hospital")
        
        assert success
        assert adapted["title"] == "Test Content"
        assert adapted["segment"] == "hospital"
        assert "metadata" in adapted
    
    def test_content_enricher(self):
        """Testa enriquecimento de conteúdo"""
        enricher = ContentEnricher()
        
        content = {
            "title": "Test",
            "content": "This is a test content with multiple words to extract keywords.",
            "segment": "hospital"
        }
        
        enriched = enricher.enrich(content)
        
        assert "enrichment" in enriched
        assert "keywords" in enriched["enrichment"]
        assert "relevance_score" in enriched["enrichment"]
        assert "quality_score" in enriched["enrichment"]


class TestIntegration:
    """Testes de integração entre módulos"""
    
    def test_full_workflow(self):
        """Testa workflow completo"""
        # 1. Adaptar conteúdo
        adapter = ScraperAdapter()
        test_data = {
            "title": "Hospital Content",
            "content": "Important hospital information.",
            "category": "hospital"
        }
        
        success, adapted = adapter.adapt_scraped_content(test_data, "hospital")
        assert success
        
        # 2. Enriquecer
        enricher = ContentEnricher()
        enriched = enricher.enrich(adapted)
        assert "enrichment" in enriched
        
        # 3. Salvar em sandbox
        saved, path = adapter.save_to_sandbox(enriched)
        assert saved
        
        # 4. Registrar avatar
        manager = RegistryManager()
        success, msg = manager.register_avatar(
            "hospital_avatar",
            "Hospital Assistant",
            "hospital",
            "professional"
        )
        assert success
        
        # 5. Validar avatar
        validator = AvatarValidator()
        entry = manager.get_avatar("hospital_avatar")
        report = validator.validate_full_avatar("hospital_avatar", entry.to_dict())
        assert report is not None


class TestBackwardCompatibility:
    """Testa backward compatibility"""
    
    def test_no_breaking_changes(self):
        """Verifica que não há breaking changes"""
        # Todos os módulos devem inicializar sem erro
        modules = [
            UpdateScheduler(),
            DeltaDetector(),
            ContentNormalizer(),
            UpdatePromoter(),
            ThemeLoader(),
            RegistryManager(),
            AvatarValidator(),
            ScraperAdapter(),
            ContentEnricher()
        ]
        
        assert len(modules) == 9
        for module in modules:
            assert module is not None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v"])
