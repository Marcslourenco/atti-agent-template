"""
Theme Loader - Carrega e aplica temas de avatar

Características:
- Carregar tema por avatar_id
- Permitir override por cliente
- Não alterar SoulX
- Desacoplamento total da lógica de conhecimento
- Validação de schema
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AvatarStyle(Enum):
    """Estilos de avatar disponíveis"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    PLAYFUL = "playful"
    MINIMALIST = "minimalist"
    REALISTIC = "realistic"


class FontStyle(Enum):
    """Estilos de fonte disponíveis"""
    SANS_SERIF = "sans-serif"
    SERIF = "serif"
    MONOSPACE = "monospace"
    ROUNDED = "rounded"


@dataclass
class Theme:
    """Definição de tema"""
    id: str
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_style: str
    avatar_style: str
    border_radius: str
    shadow_intensity: float
    animation_speed: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valida tema"""
        errors = []
        
        # Validar cores (formato hex)
        colors = [
            self.primary_color, self.secondary_color, self.accent_color,
            self.background_color, self.text_color
        ]
        
        for color in colors:
            if not self._is_valid_color(color):
                errors.append(f"Cor inválida: {color}")
        
        # Validar valores numéricos
        if not (0 <= self.shadow_intensity <= 1):
            errors.append("shadow_intensity deve estar entre 0 e 1")
        
        if not (0.5 <= self.animation_speed <= 2):
            errors.append("animation_speed deve estar entre 0.5 e 2")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Valida formato de cor"""
        import re
        # Aceita hex, rgb, rgba, named colors
        hex_pattern = r'^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$'
        rgb_pattern = r'^rgb\(\d+,\s*\d+,\s*\d+\)$'
        rgba_pattern = r'^rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)$'
        
        return bool(
            re.match(hex_pattern, color) or
            re.match(rgb_pattern, color) or
            re.match(rgba_pattern, color) or
            color.lower() in ['red', 'blue', 'green', 'white', 'black', 'gray']
        )


@dataclass
class Accessory:
    """Definição de acessório"""
    id: str
    name: str
    type: str  # cap, helmet, uniform, etc
    position: str  # head, body, hand, etc
    color: str
    compatible_styles: List[str]
    size: str  # small, medium, large
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)


class ThemeLoader:
    """
    Carrega e aplica temas de avatar
    
    Características:
    - Carregar tema por avatar_id
    - Permitir override por cliente
    - Desacoplado de SoulX
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa loader
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.themes_dir = self.base_path / "avatar_theme_engine" / "themes"
        self.accessories_dir = self.base_path / "avatar_theme_engine" / "accessories"
        
        # Criar diretórios se não existirem
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.accessories_dir.mkdir(parents=True, exist_ok=True)
        
        self.themes = self._load_themes()
        self.accessories = self._load_accessories()
        self.default_theme = self._create_default_theme()
        
        logger.info(f"ThemeLoader inicializado ({len(self.themes)} temas, {len(self.accessories)} acessórios)")
    
    def _load_themes(self) -> Dict[str, Theme]:
        """Carrega temas do diretório"""
        themes = {}
        
        try:
            for file in self.themes_dir.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        theme = Theme(**data)
                        themes[theme.id] = theme
                except Exception as e:
                    logger.warning(f"Erro ao carregar tema {file}: {e}")
        except Exception as e:
            logger.warning(f"Erro ao listar temas: {e}")
        
        return themes
    
    def _load_accessories(self) -> Dict[str, Accessory]:
        """Carrega acessórios do diretório"""
        accessories = {}
        
        try:
            for file in self.accessories_dir.glob("*.json"):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        accessory = Accessory(**data)
                        accessories[accessory.id] = accessory
                except Exception as e:
                    logger.warning(f"Erro ao carregar acessório {file}: {e}")
        except Exception as e:
            logger.warning(f"Erro ao listar acessórios: {e}")
        
        return accessories
    
    def _create_default_theme(self) -> Theme:
        """Cria tema padrão"""
        return Theme(
            id="default",
            name="Default Theme",
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
    
    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """
        Obtém tema por ID
        
        Args:
            theme_id: ID do tema
            
        Returns:
            Tema ou None se não encontrado
        """
        return self.themes.get(theme_id, None)
    
    def get_theme_for_avatar(self, avatar_id: str) -> Theme:
        """
        Obtém tema para um avatar
        
        Estratégia:
        1. Procurar tema específico do avatar
        2. Usar tema padrão
        
        Args:
            avatar_id: ID do avatar
            
        Returns:
            Tema (nunca None)
        """
        # Procurar tema específico
        theme = self.themes.get(avatar_id, None)
        
        if theme:
            logger.info(f"✓ Tema específico encontrado: {avatar_id}")
            return theme
        
        logger.info(f"ℹ Usando tema padrão para: {avatar_id}")
        return self.default_theme
    
    def apply_theme(
        self,
        avatar_config: Dict[str, Any],
        theme_id: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aplica tema a configuração de avatar
        
        Args:
            avatar_config: Configuração do avatar
            theme_id: ID do tema (None = usar padrão)
            overrides: Overrides de cliente
            
        Returns:
            Configuração com tema aplicado
        """
        # Obter tema
        if theme_id:
            theme = self.get_theme(theme_id)
            if not theme:
                logger.warning(f"Tema {theme_id} não encontrado, usando padrão")
                theme = self.default_theme
        else:
            avatar_id = avatar_config.get("id", "")
            theme = self.get_theme_for_avatar(avatar_id)
        
        # Aplicar tema
        themed_config = {
            **avatar_config,
            "theme": {
                "id": theme.id,
                "name": theme.name,
                "colors": {
                    "primary": theme.primary_color,
                    "secondary": theme.secondary_color,
                    "accent": theme.accent_color,
                    "background": theme.background_color,
                    "text": theme.text_color
                },
                "typography": {
                    "font_style": theme.font_style
                },
                "appearance": {
                    "avatar_style": theme.avatar_style,
                    "border_radius": theme.border_radius,
                    "shadow_intensity": theme.shadow_intensity,
                    "animation_speed": theme.animation_speed
                }
            }
        }
        
        # Aplicar overrides
        if overrides:
            if "theme" in overrides:
                themed_config["theme"].update(overrides["theme"])
        
        logger.info(f"✓ Tema aplicado: {theme.id}")
        return themed_config
    
    def get_compatible_accessories(
        self,
        avatar_style: str,
        position: Optional[str] = None
    ) -> List[Accessory]:
        """
        Obtém acessórios compatíveis
        
        Args:
            avatar_style: Estilo do avatar
            position: Posição específica (opcional)
            
        Returns:
            Lista de acessórios compatíveis
        """
        compatible = []
        
        for accessory in self.accessories.values():
            # Verificar compatibilidade de estilo
            if avatar_style not in accessory.compatible_styles:
                continue
            
            # Verificar posição se especificada
            if position and accessory.position != position:
                continue
            
            compatible.append(accessory)
        
        return compatible
    
    def list_themes(self) -> List[Dict[str, Any]]:
        """Lista todos os temas disponíveis"""
        return [
            {
                "id": theme.id,
                "name": theme.name,
                "avatar_style": theme.avatar_style,
                "primary_color": theme.primary_color
            }
            for theme in self.themes.values()
        ]
    
    def list_accessories(self) -> List[Dict[str, Any]]:
        """Lista todos os acessórios disponíveis"""
        return [
            {
                "id": acc.id,
                "name": acc.name,
                "type": acc.type,
                "position": acc.position
            }
            for acc in self.accessories.values()
        ]
    
    def save_theme(self, theme: Theme) -> bool:
        """Salva tema em arquivo"""
        try:
            file = self.themes_dir / f"{theme.id}.json"
            
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.themes[theme.id] = theme
            logger.info(f"✓ Tema salvo: {theme.id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao salvar tema: {e}")
            return False
    
    def save_accessory(self, accessory: Accessory) -> bool:
        """Salva acessório em arquivo"""
        try:
            file = self.accessories_dir / f"{accessory.id}.json"
            
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(accessory.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.accessories[accessory.id] = accessory
            logger.info(f"✓ Acessório salvo: {accessory.id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao salvar acessório: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde"""
        return {
            "loader": "ThemeLoader",
            "themes_loaded": len(self.themes),
            "accessories_loaded": len(self.accessories),
            "default_theme_valid": self.default_theme is not None,
            "status": "healthy"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    loader = ThemeLoader()
    print(f"\nStatus: {loader.get_health_status()}")
    print(f"Temas: {loader.list_themes()}")
    print(f"Acessórios: {loader.list_accessories()}")
