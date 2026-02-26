"""
Registry Manager - Gerencia registro central de avatares

Características:
- Registro centralizado de avatares
- Versionamento de avatares
- Histórico de alterações
- Busca e filtro
- Sem acoplamento com SoulX
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class AvatarEntry:
    """Entrada no registro de avatares"""
    id: str
    name: str
    version: str
    segment: str
    theme_id: str
    created_at: str
    updated_at: str
    status: str  # active, inactive, archived
    description: str
    metadata: Dict[str, Any]
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)


class RegistryManager:
    """
    Gerencia registro central de avatares
    
    Responsabilidades:
    - Manter registro de avatares
    - Versionamento
    - Histórico de alterações
    - Busca e filtro
    """
    
    def __init__(self, base_path: str = "."):
        """
        Inicializa manager
        
        Args:
            base_path: Caminho base do projeto
        """
        self.base_path = Path(base_path)
        self.registry_dir = self.base_path / "avatar_registry"
        self.registry_file = self.registry_dir / "registry.json"
        self.history_dir = self.registry_dir / "history"
        
        # Criar diretórios
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry = self._load_registry()
        
        logger.info(f"RegistryManager inicializado ({len(self.registry)} avatares)")
    
    def _load_registry(self) -> Dict[str, AvatarEntry]:
        """Carrega registro do arquivo"""
        if not self.registry_file.exists():
            logger.info("Registro vazio, criando novo")
            return {}
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                registry = {}
                for avatar_id, entry_data in data.items():
                    try:
                        registry[avatar_id] = AvatarEntry(**entry_data)
                    except Exception as e:
                        logger.warning(f"Erro ao carregar avatar {avatar_id}: {e}")
                return registry
        except Exception as e:
            logger.error(f"Erro ao carregar registro: {e}")
            return {}
    
    def _save_registry(self) -> bool:
        """Salva registro em arquivo"""
        try:
            data = {
                avatar_id: entry.to_dict()
                for avatar_id, entry in self.registry.items()
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Registro salvo ({len(self.registry)} avatares)")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao salvar registro: {e}")
            return False
    
    def _save_history(self, avatar_id: str, action: str, details: Dict[str, Any]) -> bool:
        """Salva histórico de alteração"""
        try:
            timestamp = datetime.now().isoformat()
            history_file = self.history_dir / f"{avatar_id}_{timestamp.replace(':', '-')}.json"
            
            history_entry = {
                "avatar_id": avatar_id,
                "action": action,
                "timestamp": timestamp,
                "details": details
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_entry, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro ao salvar histórico: {e}")
            return False
    
    def register_avatar(
        self,
        avatar_id: str,
        name: str,
        segment: str,
        theme_id: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Registra novo avatar
        
        Args:
            avatar_id: ID único do avatar
            name: Nome do avatar
            segment: Segmento de negócio
            theme_id: ID do tema
            description: Descrição
            metadata: Metadata adicional
            
        Returns:
            (sucesso, mensagem)
        """
        if avatar_id in self.registry:
            return False, f"Avatar {avatar_id} já existe"
        
        try:
            now = datetime.now().isoformat()
            
            # Calcular checksum
            checksum = self._calculate_checksum({
                "id": avatar_id,
                "name": name,
                "segment": segment,
                "theme_id": theme_id
            })
            
            entry = AvatarEntry(
                id=avatar_id,
                name=name,
                version="1.0.0",
                segment=segment,
                theme_id=theme_id,
                created_at=now,
                updated_at=now,
                status="active",
                description=description,
                metadata=metadata or {},
                checksum=checksum
            )
            
            self.registry[avatar_id] = entry
            
            # Salvar
            if self._save_registry():
                self._save_history(avatar_id, "created", {"name": name, "segment": segment})
                logger.info(f"✓ Avatar registrado: {avatar_id}")
                return True, f"Avatar {avatar_id} registrado com sucesso"
            else:
                # Rollback
                del self.registry[avatar_id]
                return False, "Erro ao salvar registro"
                
        except Exception as e:
            logger.error(f"✗ Erro ao registrar avatar: {e}")
            return False, str(e)
    
    def get_avatar(self, avatar_id: str) -> Optional[AvatarEntry]:
        """Obtém avatar do registro"""
        return self.registry.get(avatar_id, None)
    
    def update_avatar(
        self,
        avatar_id: str,
        updates: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Atualiza avatar no registro
        
        Args:
            avatar_id: ID do avatar
            updates: Campos a atualizar
            
        Returns:
            (sucesso, mensagem)
        """
        if avatar_id not in self.registry:
            return False, f"Avatar {avatar_id} não encontrado"
        
        try:
            entry = self.registry[avatar_id]
            
            # Atualizar campos permitidos
            allowed_fields = ["name", "theme_id", "description", "metadata", "status"]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(entry, field, value)
            
            # Atualizar timestamp e versão
            entry.updated_at = datetime.now().isoformat()
            
            # Incrementar versão patch
            parts = entry.version.split('.')
            parts[2] = str(int(parts[2]) + 1)
            entry.version = '.'.join(parts)
            
            if self._save_registry():
                self._save_history(avatar_id, "updated", updates)
                logger.info(f"✓ Avatar atualizado: {avatar_id}")
                return True, f"Avatar {avatar_id} atualizado com sucesso"
            else:
                return False, "Erro ao salvar registro"
                
        except Exception as e:
            logger.error(f"✗ Erro ao atualizar avatar: {e}")
            return False, str(e)
    
    def list_avatars(
        self,
        segment: Optional[str] = None,
        status: str = "active"
    ) -> List[AvatarEntry]:
        """
        Lista avatares com filtro
        
        Args:
            segment: Filtrar por segmento (opcional)
            status: Filtrar por status
            
        Returns:
            Lista de avatares
        """
        avatars = []
        
        for entry in self.registry.values():
            if entry.status != status:
                continue
            
            if segment and entry.segment != segment:
                continue
            
            avatars.append(entry)
        
        return avatars
    
    def search_avatars(self, query: str) -> List[AvatarEntry]:
        """
        Busca avatares por nome ou descrição
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de avatares encontrados
        """
        query = query.lower()
        results = []
        
        for entry in self.registry.values():
            if (query in entry.name.lower() or
                query in entry.description.lower() or
                query in entry.id.lower()):
                results.append(entry)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do registro"""
        total = len(self.registry)
        active = sum(1 for e in self.registry.values() if e.status == "active")
        inactive = sum(1 for e in self.registry.values() if e.status == "inactive")
        archived = sum(1 for e in self.registry.values() if e.status == "archived")
        
        segments = {}
        for entry in self.registry.values():
            segments[entry.segment] = segments.get(entry.segment, 0) + 1
        
        return {
            "total_avatars": total,
            "active": active,
            "inactive": inactive,
            "archived": archived,
            "segments": segments,
            "registry_file_size": self.registry_file.stat().st_size if self.registry_file.exists() else 0
        }
    
    def export_registry(self, file_path: str) -> bool:
        """Exporta registro para arquivo"""
        try:
            data = {
                avatar_id: entry.to_dict()
                for avatar_id, entry in self.registry.items()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Registro exportado: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao exportar: {e}")
            return False
    
    def import_registry(self, file_path: str, merge: bool = False) -> Tuple[bool, str]:
        """
        Importa registro de arquivo
        
        Args:
            file_path: Caminho do arquivo
            merge: Mesclar com registro existente
            
        Returns:
            (sucesso, mensagem)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not merge:
                self.registry = {}
            
            count = 0
            for avatar_id, entry_data in data.items():
                try:
                    self.registry[avatar_id] = AvatarEntry(**entry_data)
                    count += 1
                except Exception as e:
                    logger.warning(f"Erro ao importar {avatar_id}: {e}")
            
            if self._save_registry():
                logger.info(f"✓ {count} avatares importados")
                return True, f"{count} avatares importados com sucesso"
            else:
                return False, "Erro ao salvar registro"
                
        except Exception as e:
            logger.error(f"✗ Erro ao importar: {e}")
            return False, str(e)
    
    @staticmethod
    def _calculate_checksum(data: Dict[str, Any]) -> str:
        """Calcula checksum de dados"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde"""
        return {
            "manager": "RegistryManager",
            "total_avatars": len(self.registry),
            "registry_file_exists": self.registry_file.exists(),
            "registry_file_size": self.registry_file.stat().st_size if self.registry_file.exists() else 0,
            "history_entries": len(list(self.history_dir.glob("*.json"))),
            "status": "healthy"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = RegistryManager()
    
    # Teste
    success, msg = manager.register_avatar(
        "avatar_001",
        "Hospital Assistant",
        "hospital",
        "professional",
        "Avatar para assistência hospitalar"
    )
    
    print(f"\nRegistro: {success} - {msg}")
    print(f"Estatísticas: {manager.get_statistics()}")
    print(f"Status: {manager.get_health_status()}")
