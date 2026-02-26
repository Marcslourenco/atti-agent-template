"""
Schema Validator - Valida schemas de temas e acessórios

Características:
- Validação de estrutura JSON
- Validação de tipos
- Validação de valores permitidos
- Mensagens de erro claras
"""

import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Valida schemas de temas e acessórios"""
    
    # Schema para Theme
    THEME_SCHEMA = {
        "type": "object",
        "required": [
            "id", "name", "primary_color", "secondary_color", "accent_color",
            "background_color", "text_color", "font_style", "avatar_style",
            "border_radius", "shadow_intensity", "animation_speed"
        ],
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "primary_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "secondary_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "accent_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "background_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "text_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "font_style": {"type": "string", "enum": ["sans-serif", "serif", "monospace", "rounded"]},
            "avatar_style": {"type": "string", "enum": ["professional", "casual", "playful", "minimalist", "realistic"]},
            "border_radius": {"type": "string"},
            "shadow_intensity": {"type": "number", "minimum": 0, "maximum": 1},
            "animation_speed": {"type": "number", "minimum": 0.5, "maximum": 2}
        }
    }
    
    # Schema para Accessory
    ACCESSORY_SCHEMA = {
        "type": "object",
        "required": [
            "id", "name", "type", "position", "color", "compatible_styles", "size"
        ],
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "type": {"type": "string", "enum": ["cap", "helmet", "uniform", "glasses", "hat", "scarf"]},
            "position": {"type": "string", "enum": ["head", "body", "hand", "foot", "neck"]},
            "color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$|^rgb.*$|^rgba.*$"},
            "compatible_styles": {"type": "array", "items": {"type": "string"}},
            "size": {"type": "string", "enum": ["small", "medium", "large"]}
        }
    }
    
    @staticmethod
    def validate_theme(theme_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de tema
        
        Args:
            theme_data: Dados do tema
            
        Returns:
            (válido, lista de erros)
        """
        errors = []
        
        # Validar campos obrigatórios
        required = SchemaValidator.THEME_SCHEMA["required"]
        for field in required:
            if field not in theme_data:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar tipos
        if "id" in theme_data and not isinstance(theme_data["id"], str):
            errors.append("id deve ser string")
        
        if "name" in theme_data and not isinstance(theme_data["name"], str):
            errors.append("name deve ser string")
        
        # Validar cores
        colors = ["primary_color", "secondary_color", "accent_color", "background_color", "text_color"]
        for color_field in colors:
            if color_field in theme_data:
                if not SchemaValidator._is_valid_color(theme_data[color_field]):
                    errors.append(f"{color_field} inválido: {theme_data[color_field]}")
        
        # Validar enums
        if "font_style" in theme_data:
            valid_fonts = ["sans-serif", "serif", "monospace", "rounded"]
            if theme_data["font_style"] not in valid_fonts:
                errors.append(f"font_style inválido: {theme_data['font_style']}")
        
        if "avatar_style" in theme_data:
            valid_styles = ["professional", "casual", "playful", "minimalist", "realistic"]
            if theme_data["avatar_style"] not in valid_styles:
                errors.append(f"avatar_style inválido: {theme_data['avatar_style']}")
        
        # Validar números
        if "shadow_intensity" in theme_data:
            val = theme_data["shadow_intensity"]
            if not isinstance(val, (int, float)) or not (0 <= val <= 1):
                errors.append(f"shadow_intensity deve estar entre 0 e 1: {val}")
        
        if "animation_speed" in theme_data:
            val = theme_data["animation_speed"]
            if not isinstance(val, (int, float)) or not (0.5 <= val <= 2):
                errors.append(f"animation_speed deve estar entre 0.5 e 2: {val}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_accessory(accessory_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de acessório
        
        Args:
            accessory_data: Dados do acessório
            
        Returns:
            (válido, lista de erros)
        """
        errors = []
        
        # Validar campos obrigatórios
        required = SchemaValidator.ACCESSORY_SCHEMA["required"]
        for field in required:
            if field not in accessory_data:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar tipos
        if "id" in accessory_data and not isinstance(accessory_data["id"], str):
            errors.append("id deve ser string")
        
        if "name" in accessory_data and not isinstance(accessory_data["name"], str):
            errors.append("name deve ser string")
        
        # Validar cor
        if "color" in accessory_data:
            if not SchemaValidator._is_valid_color(accessory_data["color"]):
                errors.append(f"color inválido: {accessory_data['color']}")
        
        # Validar enums
        if "type" in accessory_data:
            valid_types = ["cap", "helmet", "uniform", "glasses", "hat", "scarf"]
            if accessory_data["type"] not in valid_types:
                errors.append(f"type inválido: {accessory_data['type']}")
        
        if "position" in accessory_data:
            valid_positions = ["head", "body", "hand", "foot", "neck"]
            if accessory_data["position"] not in valid_positions:
                errors.append(f"position inválido: {accessory_data['position']}")
        
        if "size" in accessory_data:
            valid_sizes = ["small", "medium", "large"]
            if accessory_data["size"] not in valid_sizes:
                errors.append(f"size inválido: {accessory_data['size']}")
        
        # Validar compatible_styles
        if "compatible_styles" in accessory_data:
            if not isinstance(accessory_data["compatible_styles"], list):
                errors.append("compatible_styles deve ser array")
            elif len(accessory_data["compatible_styles"]) == 0:
                errors.append("compatible_styles não pode estar vazio")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_theme_file(file_path: str) -> Tuple[bool, List[str]]:
        """Valida arquivo de tema"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SchemaValidator.validate_theme(data)
        except json.JSONDecodeError as e:
            return False, [f"JSON inválido: {e}"]
        except Exception as e:
            return False, [f"Erro ao ler arquivo: {e}"]
    
    @staticmethod
    def validate_accessory_file(file_path: str) -> Tuple[bool, List[str]]:
        """Valida arquivo de acessório"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SchemaValidator.validate_accessory(data)
        except json.JSONDecodeError as e:
            return False, [f"JSON inválido: {e}"]
        except Exception as e:
            return False, [f"Erro ao ler arquivo: {e}"]
    
    @staticmethod
    def validate_directory(directory: str, file_type: str = "theme") -> Dict[str, Tuple[bool, List[str]]]:
        """
        Valida todos os arquivos em um diretório
        
        Args:
            directory: Caminho do diretório
            file_type: "theme" ou "accessory"
            
        Returns:
            Dicionário com resultados por arquivo
        """
        results = {}
        path = Path(directory)
        
        if not path.exists():
            logger.warning(f"Diretório não existe: {directory}")
            return results
        
        validator = SchemaValidator.validate_theme_file if file_type == "theme" else SchemaValidator.validate_accessory_file
        
        for file in path.glob("*.json"):
            try:
                results[file.name] = validator(str(file))
            except Exception as e:
                results[file.name] = (False, [str(e)])
        
        return results
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Valida formato de cor"""
        import re
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        rgb_pattern = r'^rgb\(\d+,\s*\d+,\s*\d+\)$'
        rgba_pattern = r'^rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)$'
        
        return bool(
            re.match(hex_pattern, color) or
            re.match(rgb_pattern, color) or
            re.match(rgba_pattern, color)
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Teste
    test_theme = {
        "id": "test",
        "name": "Test Theme",
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
    
    valid, errors = SchemaValidator.validate_theme(test_theme)
    print(f"Theme válido: {valid}")
    if errors:
        print(f"Erros: {errors}")
