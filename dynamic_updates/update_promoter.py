"""
Update Promoter - Promove sandbox para nova versão de knowledge

Características:
- Promove sandbox para nova versão knowledge
- Gera knowledge v2.1.x
- Atualiza manifest
- Recalcula SHA256
- Sem promoção automática (apenas estrutura)
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
import shutil

logger = logging.getLogger(__name__)


class UpdatePromoter:
    """
    Promove atualizações de sandbox para nova versão de knowledge
    
    Fluxo:
    1. Validar conteúdo em sandbox
    2. Mesclar com knowledge existente
    3. Gerar nova versão (v2.1.x)
    4. Atualizar manifest
    5. Recalcular hashes
    6. Criar backup
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa promoter
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.sandbox_dir = self.base_path / "dynamic_updates" / "update_sandbox"
        self.knowledge_dir = self.base_path / "knowledge_packages"
        self.manifest_file = self.base_path / "knowledge_manifest_v2_1_0.json"
        
        self.current_version = self._get_current_version()
        
        logger.info(f"UpdatePromoter inicializado (versão atual: {self.current_version})")
    
    def _get_current_version(self) -> str:
        """Obtém versão atual do knowledge"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    return manifest.get("version", "2.1.0")
            except Exception as e:
                logger.warning(f"Erro ao obter versão: {e}")
        
        return "2.1.0"
    
    def _increment_version(self, version: str) -> str:
        """
        Incrementa versão patch (2.1.0 → 2.1.1)
        
        Args:
            version: Versão atual
            
        Returns:
            Versão incrementada
        """
        try:
            parts = version.split('.')
            if len(parts) >= 3:
                parts[2] = str(int(parts[2]) + 1)
                return '.'.join(parts)
        except Exception as e:
            logger.warning(f"Erro ao incrementar versão: {e}")
        
        return version
    
    def validate_sandbox(self) -> Tuple[bool, List[str]]:
        """
        Valida conteúdo em sandbox
        
        Returns:
            (válido, lista de problemas)
        """
        problems = []
        
        if not self.sandbox_dir.exists():
            problems.append("Diretório sandbox não existe")
            return False, problems
        
        sandbox_files = list(self.sandbox_dir.glob("*.json"))
        
        if not sandbox_files:
            problems.append("Nenhum arquivo em sandbox")
            return False, problems
        
        # Validar cada arquivo
        for file in sandbox_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                    # Validações básicas
                    if not content.get("title"):
                        problems.append(f"{file.name}: title vazio")
                    
                    if not content.get("content"):
                        problems.append(f"{file.name}: content vazio")
                    
                    if not content.get("segment"):
                        problems.append(f"{file.name}: segment vazio")
                    
            except json.JSONDecodeError as e:
                problems.append(f"{file.name}: JSON inválido ({e})")
            except Exception as e:
                problems.append(f"{file.name}: Erro ({e})")
        
        is_valid = len(problems) == 0
        
        if is_valid:
            logger.info(f"✓ Sandbox validado ({len(sandbox_files)} arquivos)")
        else:
            logger.warning(f"⚠ Sandbox com problemas: {len(problems)} erros")
        
        return is_valid, problems
    
    def get_sandbox_content(self) -> List[Dict[str, Any]]:
        """Retorna conteúdo do sandbox"""
        content = []
        
        try:
            for file in self.sandbox_dir.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    content.append(json.load(f))
        except Exception as e:
            logger.error(f"Erro ao ler sandbox: {e}")
        
        return content
    
    def preview_promotion(self) -> Dict[str, Any]:
        """
        Mostra preview do que seria promovido
        
        Returns:
            Dicionário com preview
        """
        valid, problems = self.validate_sandbox()
        sandbox_content = self.get_sandbox_content()
        new_version = self._increment_version(self.current_version)
        
        return {
            "status": "ready" if valid else "invalid",
            "problems": problems,
            "current_version": self.current_version,
            "new_version": new_version,
            "sandbox_files": len(list(self.sandbox_dir.glob("*.json"))),
            "sandbox_content_count": len(sandbox_content),
            "total_blocks_after": self._count_total_blocks() + len(sandbox_content),
            "timestamp": datetime.now().isoformat()
        }
    
    def promote_to_knowledge(
        self,
        segment: Optional[str] = None,
        create_backup: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Promove sandbox para nova versão de knowledge
        
        ⚠️ OPERAÇÃO DESTRUTIVA - Sem promoção automática
        
        Args:
            segment: Segmento específico (None = todos)
            create_backup: Criar backup antes de promover
            
        Returns:
            (sucesso, resultado)
        """
        logger.warning("⚠️ Promoção de sandbox não está ativada automaticamente")
        logger.warning("Use preview_promotion() para ver o que seria promovido")
        
        result = {
            "status": "blocked",
            "reason": "Promoção automática desativada",
            "message": "Use preview_promotion() para validar antes de promover manualmente",
            "preview": self.preview_promotion()
        }
        
        return False, result
    
    def _count_total_blocks(self) -> int:
        """Conta total de blocos no knowledge atual"""
        total = 0
        
        try:
            for file in self.knowledge_dir.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total += len(data.get("blocks", []))
        except Exception as e:
            logger.warning(f"Erro ao contar blocos: {e}")
        
        return total
    
    def calculate_promotion_impact(self) -> Dict[str, Any]:
        """Calcula impacto da promoção"""
        sandbox_content = self.get_sandbox_content()
        current_blocks = self._count_total_blocks()
        new_blocks = len(sandbox_content)
        
        # Estimar por segmento
        segments = {}
        for content in sandbox_content:
            segment = content.get("segment", "unknown")
            segments[segment] = segments.get(segment, 0) + 1
        
        return {
            "current_total_blocks": current_blocks,
            "new_blocks_to_add": new_blocks,
            "total_after_promotion": current_blocks + new_blocks,
            "growth_percentage": (new_blocks / current_blocks * 100) if current_blocks > 0 else 0,
            "new_blocks_by_segment": segments,
            "version_change": f"{self.current_version} → {self._increment_version(self.current_version)}"
        }
    
    def rollback_sandbox(self, keep_backup: bool = True) -> bool:
        """
        Limpa sandbox (rollback)
        
        Args:
            keep_backup: Manter backup antes de limpar
            
        Returns:
            True se sucesso
        """
        try:
            files = list(self.sandbox_dir.glob("*.json"))
            
            if keep_backup and files:
                # Criar backup
                backup_dir = self.base_path / "dynamic_updates" / "sandbox_backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_subdir = backup_dir / f"backup_{timestamp}"
                backup_subdir.mkdir(exist_ok=True)
                
                for file in files:
                    shutil.copy2(file, backup_subdir / file.name)
                
                logger.info(f"✓ Backup criado: {backup_subdir}")
            
            # Limpar sandbox
            for file in files:
                file.unlink()
            
            logger.info("✓ Sandbox limpo")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao limpar sandbox: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do promoter"""
        valid, problems = self.validate_sandbox()
        
        return {
            "promoter": "UpdatePromoter",
            "current_version": self.current_version,
            "sandbox_valid": valid,
            "sandbox_problems": len(problems),
            "sandbox_files": len(list(self.sandbox_dir.glob("*.json"))),
            "promotion_ready": valid and len(list(self.sandbox_dir.glob("*.json"))) > 0,
            "status": "healthy" if not problems else "degraded"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    promoter = UpdatePromoter()
    
    print(f"\nPreview: {promoter.preview_promotion()}")
    print(f"\nImpacto: {promoter.calculate_promotion_impact()}")
    print(f"\nStatus: {promoter.get_health_status()}")
