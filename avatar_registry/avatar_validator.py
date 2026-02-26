"""
Avatar Validator - Valida integridade de avatares

Características:
- Validação de estrutura
- Validação de dependências
- Validação de tema
- Validação de conhecimento
- Relatório detalhado
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AvatarValidator:
    """
    Valida integridade de avatares
    
    Verifica:
    - Estrutura básica
    - Dependências (tema, conhecimento)
    - Configuração
    - Compatibilidade
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa validator
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.themes_dir = self.base_path / "avatar_theme_engine" / "themes"
        self.knowledge_dir = self.base_path / "knowledge_packages"
        
        logger.info("AvatarValidator inicializado")
    
    def validate_avatar_entry(self, entry: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Valida entrada de avatar
        
        Args:
            entry: Dados do avatar
            
        Returns:
            (válido, erros, avisos)
        """
        errors = []
        warnings = []
        
        # Validar campos obrigatórios
        required_fields = ["id", "name", "segment", "theme_id", "version"]
        for field in required_fields:
            if field not in entry or not entry[field]:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar ID
        if "id" in entry:
            if not self._is_valid_id(entry["id"]):
                errors.append(f"ID inválido: {entry['id']}")
        
        # Validar versão
        if "version" in entry:
            if not self._is_valid_version(entry["version"]):
                errors.append(f"Versão inválida: {entry['version']}")
        
        # Validar status
        if "status" in entry:
            valid_statuses = ["active", "inactive", "archived"]
            if entry["status"] not in valid_statuses:
                errors.append(f"Status inválido: {entry['status']}")
        
        # Avisos
        if "description" not in entry or not entry.get("description"):
            warnings.append("Descrição vazia")
        
        return len(errors) == 0, errors, warnings
    
    def validate_theme_dependency(self, theme_id: str) -> Tuple[bool, str]:
        """
        Valida se tema existe
        
        Args:
            theme_id: ID do tema
            
        Returns:
            (existe, mensagem)
        """
        theme_file = self.themes_dir / f"{theme_id}.json"
        
        if theme_file.exists():
            return True, f"Tema encontrado: {theme_id}"
        else:
            return False, f"Tema não encontrado: {theme_id}"
    
    def validate_knowledge_dependency(self, segment: str) -> Tuple[bool, str]:
        """
        Valida se conhecimento do segmento existe
        
        Args:
            segment: Segmento de negócio
            
        Returns:
            (existe, mensagem)
        """
        knowledge_file = self.knowledge_dir / f"{segment.lower()}_*.json"
        
        # Procurar arquivo correspondente
        matching_files = list(self.knowledge_dir.glob(f"*{segment.lower()}*.json"))
        
        if matching_files:
            return True, f"Conhecimento encontrado para segmento: {segment}"
        else:
            return False, f"Conhecimento não encontrado para segmento: {segment}"
    
    def validate_full_avatar(
        self,
        avatar_id: str,
        entry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validação completa de avatar
        
        Args:
            avatar_id: ID do avatar
            entry: Dados do avatar
            
        Returns:
            Relatório de validação
        """
        report = {
            "avatar_id": avatar_id,
            "valid": True,
            "checks": {}
        }
        
        # 1. Validar estrutura
        struct_valid, struct_errors, struct_warnings = self.validate_avatar_entry(entry)
        report["checks"]["structure"] = {
            "valid": struct_valid,
            "errors": struct_errors,
            "warnings": struct_warnings
        }
        if not struct_valid:
            report["valid"] = False
        
        # 2. Validar tema
        theme_id = entry.get("theme_id", "")
        theme_valid, theme_msg = self.validate_theme_dependency(theme_id)
        report["checks"]["theme"] = {
            "valid": theme_valid,
            "message": theme_msg,
            "theme_id": theme_id
        }
        if not theme_valid:
            report["valid"] = False
        
        # 3. Validar conhecimento
        segment = entry.get("segment", "")
        knowledge_valid, knowledge_msg = self.validate_knowledge_dependency(segment)
        report["checks"]["knowledge"] = {
            "valid": knowledge_valid,
            "message": knowledge_msg,
            "segment": segment
        }
        if not knowledge_valid:
            report["valid"] = False
        
        # 4. Validar compatibilidade
        compat_issues = self._check_compatibility(entry)
        report["checks"]["compatibility"] = {
            "valid": len(compat_issues) == 0,
            "issues": compat_issues
        }
        if compat_issues:
            report["valid"] = False
        
        return report
    
    def _check_compatibility(self, entry: Dict[str, Any]) -> List[str]:
        """Verifica compatibilidade de configurações"""
        issues = []
        
        # Verificar se versão é compatível
        version = entry.get("version", "")
        if version and not version.startswith("1.") and not version.startswith("2."):
            issues.append(f"Versão pode não ser compatível: {version}")
        
        # Verificar se status é válido
        status = entry.get("status", "")
        if status == "archived":
            issues.append("Avatar está arquivado (não será usado)")
        
        return issues
    
    def validate_batch(self, entries: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Valida lote de avatares
        
        Args:
            entries: Lista de (avatar_id, dados)
            
        Returns:
            Relatório consolidado
        """
        reports = []
        valid_count = 0
        invalid_count = 0
        
        for avatar_id, entry in entries:
            report = self.validate_full_avatar(avatar_id, entry)
            reports.append(report)
            
            if report["valid"]:
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            "total": len(entries),
            "valid": valid_count,
            "invalid": invalid_count,
            "reports": reports,
            "summary": {
                "validation_rate": (valid_count / len(entries) * 100) if entries else 0,
                "status": "healthy" if invalid_count == 0 else "degraded"
            }
        }
    
    @staticmethod
    def _is_valid_id(avatar_id: str) -> bool:
        """Valida formato de ID"""
        import re
        # ID deve ser alfanumérico com underscores
        pattern = r'^[a-z0-9_]+$'
        return bool(re.match(pattern, avatar_id.lower()))
    
    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Valida formato de versão"""
        import re
        # Versão deve ser X.Y.Z
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Retorna relatório de validação geral"""
        return {
            "validator": "AvatarValidator",
            "themes_directory": str(self.themes_dir),
            "themes_available": len(list(self.themes_dir.glob("*.json"))) if self.themes_dir.exists() else 0,
            "knowledge_directory": str(self.knowledge_dir),
            "knowledge_packages": len(list(self.knowledge_dir.glob("*.json"))) if self.knowledge_dir.exists() else 0,
            "status": "ready"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    validator = AvatarValidator()
    
    # Teste
    test_entry = {
        "id": "avatar_001",
        "name": "Hospital Assistant",
        "version": "1.0.0",
        "segment": "hospital",
        "theme_id": "professional",
        "status": "active",
        "description": "Avatar para assistência hospitalar"
    }
    
    report = validator.validate_full_avatar("avatar_001", test_entry)
    print(f"\nRelatório: {report}")
    print(f"Validação: {validator.get_validation_report()}")
