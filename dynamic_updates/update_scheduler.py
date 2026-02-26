"""
Update Scheduler - Controla execução de atualizações dinâmicas

Características:
- Execução manual ou futura via cron
- Integração com Skill de Scraping
- Sem execução automática ainda (apenas estrutura)
- Logging detalhado
- Health checks
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class UpdateStatus(Enum):
    """Status de uma atualização"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class UpdateScheduler:
    """
    Gerencia agendamento e execução de atualizações dinâmicas
    
    Fluxo:
    1. Receber conteúdo (manual ou via Skill)
    2. Normalizar (content_normalizer)
    3. Detectar deltas (delta_detector)
    4. Armazenar em sandbox (update_sandbox)
    5. Aguardar promoção manual (update_promoter)
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa scheduler
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.live_content_dir = self.base_path / "dynamic_updates" / "live_content"
        self.update_sandbox_dir = self.base_path / "dynamic_updates" / "update_sandbox"
        self.schedule_file = self.base_path / "dynamic_updates" / "schedule.json"
        
        # Criar diretórios se não existirem
        self.live_content_dir.mkdir(parents=True, exist_ok=True)
        self.update_sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        self.schedule = self._load_schedule()
        logger.info("UpdateScheduler inicializado")
    
    def _load_schedule(self) -> Dict[str, Any]:
        """Carrega agendamento do arquivo"""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar schedule: {e}")
        
        return {"updates": [], "last_run": None, "next_scheduled": None}
    
    def _save_schedule(self) -> None:
        """Salva agendamento em arquivo"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedule, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar schedule: {e}")
    
    def schedule_update(
        self,
        update_id: str,
        content: Dict[str, Any],
        scheduled_for: Optional[datetime] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Agenda uma atualização
        
        Args:
            update_id: ID único da atualização
            content: Conteúdo a atualizar
            scheduled_for: Data/hora para execução (None = imediato)
            priority: "low", "normal", "high"
            
        Returns:
            True se agendado com sucesso
        """
        try:
            update_entry = {
                "id": update_id,
                "status": UpdateStatus.SCHEDULED.value if scheduled_for else UpdateStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
                "priority": priority,
                "content_hash": self._hash_content(content),
                "source": "manual"
            }
            
            self.schedule["updates"].append(update_entry)
            self._save_schedule()
            
            logger.info(f"✓ Atualização agendada: {update_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao agendar atualização: {e}")
            return False
    
    def execute_update(
        self,
        update_id: str,
        content: Dict[str, Any],
        normalizer=None,
        delta_detector=None
    ) -> bool:
        """
        Executa uma atualização
        
        Args:
            update_id: ID da atualização
            content: Conteúdo a processar
            normalizer: Instância de ContentNormalizer
            delta_detector: Instância de DeltaDetector
            
        Returns:
            True se executado com sucesso
        """
        try:
            # 1. Normalizar conteúdo
            if normalizer:
                normalized = normalizer.normalize(content)
            else:
                normalized = content
            
            # 2. Detectar deltas
            has_changes = True
            if delta_detector:
                has_changes = delta_detector.has_significant_changes(normalized)
            
            if not has_changes:
                logger.info(f"ℹ Nenhuma mudança significativa detectada em {update_id}")
                return True
            
            # 3. Salvar em sandbox
            sandbox_file = self.update_sandbox_dir / f"{update_id}.json"
            with open(sandbox_file, 'w', encoding='utf-8') as f:
                json.dump(normalized, f, indent=2, ensure_ascii=False)
            
            # 4. Atualizar schedule
            for update in self.schedule["updates"]:
                if update["id"] == update_id:
                    update["status"] = UpdateStatus.COMPLETED.value
                    update["completed_at"] = datetime.now().isoformat()
                    break
            
            self.schedule["last_run"] = datetime.now().isoformat()
            self._save_schedule()
            
            logger.info(f"✓ Atualização executada: {update_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao executar atualização: {e}")
            
            # Marcar como falha
            for update in self.schedule["updates"]:
                if update["id"] == update_id:
                    update["status"] = UpdateStatus.FAILED.value
                    update["error"] = str(e)
                    break
            
            self._save_schedule()
            return False
    
    def get_pending_updates(self) -> List[Dict[str, Any]]:
        """Retorna atualizações pendentes"""
        return [
            u for u in self.schedule.get("updates", [])
            if u["status"] in [UpdateStatus.PENDING.value, UpdateStatus.SCHEDULED.value]
        ]
    
    def get_sandbox_updates(self) -> List[Dict[str, Any]]:
        """Retorna atualizações em sandbox"""
        updates = []
        try:
            for file in self.update_sandbox_dir.glob("*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    updates.append({
                        "id": file.stem,
                        "file": str(file),
                        "size": file.stat().st_size,
                        "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
        except Exception as e:
            logger.error(f"Erro ao listar sandbox: {e}")
        
        return updates
    
    def get_live_content(self) -> Dict[str, Any]:
        """Retorna conteúdo live atual"""
        live_file = self.live_content_dir / "current.json"
        
        if live_file.exists():
            try:
                with open(live_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar live_content: {e}")
        
        return {}
    
    def update_live_content(self, content: Dict[str, Any]) -> bool:
        """
        Atualiza conteúdo live (sobrescreve)
        
        Args:
            content: Novo conteúdo
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            live_file = self.live_content_dir / "current.json"
            
            # Backup anterior
            if live_file.exists():
                backup_file = self.live_content_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                live_file.rename(backup_file)
            
            # Salvar novo
            with open(live_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            logger.info("✓ Live content atualizado")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao atualizar live_content: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do scheduler"""
        pending = self.get_pending_updates()
        sandbox = self.get_sandbox_updates()
        
        return {
            "scheduler": "UpdateScheduler",
            "status": "healthy",
            "pending_updates": len(pending),
            "sandbox_updates": len(sandbox),
            "last_run": self.schedule.get("last_run"),
            "next_scheduled": self.schedule.get("next_scheduled"),
            "live_content_size": len(self.get_live_content())
        }
    
    @staticmethod
    def _hash_content(content: Dict[str, Any]) -> str:
        """Calcula hash SHA256 do conteúdo"""
        try:
            content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.warning(f"Erro ao calcular hash: {e}")
            return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scheduler = UpdateScheduler()
    print(f"\nStatus: {scheduler.get_health_status()}")
