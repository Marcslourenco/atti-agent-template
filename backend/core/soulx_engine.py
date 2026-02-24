"""
ATTI SoulX Engine v2.0
Camada de personalidade persistente com histórico de usuário, preferências e tom adaptativo.
Armazenamento leve sem banco de dados pesado.
"""

import json
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class UserPreferences:
    """Preferências do usuário"""
    preferred_language: str = "en"
    communication_tone: str = "professional"  # professional, casual, friendly, formal
    preferred_avatar_style: str = "default"
    interaction_history_limit: int = 50
    enable_suggestions: bool = True
    enable_analytics: bool = True


@dataclass
class InteractionRecord:
    """Registro de uma interação"""
    timestamp: str
    user_input: str
    avatar_response: str
    interaction_type: str  # "question", "statement", "command"
    duration_seconds: float
    user_satisfaction: Optional[int] = None  # 1-5 stars


@dataclass
class UserProfile:
    """Perfil completo do usuário"""
    user_id: str
    created_at: str
    last_interaction: str
    preferences: UserPreferences = field(default_factory=UserPreferences)
    interaction_history: List[InteractionRecord] = field(default_factory=list)
    personality_traits: Dict = field(default_factory=dict)
    communication_patterns: Dict = field(default_factory=dict)


class SoulXEngine:
    """
    Motor SoulX para Avatar ATTI v2.0
    
    Características:
    - Registro de histórico por usuário
    - Preferências persistentes
    - Tom de comunicação adaptativo
    - Armazenamento leve (JSON)
    - Análise de padrões de comunicação
    - Personalidade persistente
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor SoulX
        
        Args:
            config: Dicionário com configurações:
                - storage_dir: Diretório para armazenar perfis (padrão: "./soulx_profiles")
                - max_history_per_user: Máximo de interações armazenadas (padrão: 100)
                - enable_persistence: Salvar em disco (padrão: True)
        """
        self.config = config or {}
        self.storage_dir = self.config.get("storage_dir", "./soulx_profiles")
        self.max_history_per_user = self.config.get("max_history_per_user", 100)
        self.enable_persistence = self.config.get("enable_persistence", True)
        
        self.current_user_id: Optional[str] = None
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Criar diretório de armazenamento
        if self.enable_persistence:
            Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
    
    def create_user(self, user_id: str, preferences: Optional[Dict] = None) -> UserProfile:
        """
        Cria um novo perfil de usuário
        
        Args:
            user_id: ID único do usuário
            preferences: Dicionário com preferências iniciais
            
        Returns:
            Perfil do usuário criado
        """
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        now = datetime.now().isoformat()
        user_prefs = UserPreferences(**preferences) if preferences else UserPreferences()
        
        profile = UserProfile(
            user_id=user_id,
            created_at=now,
            last_interaction=now,
            preferences=user_prefs
        )
        
        self.user_profiles[user_id] = profile
        
        if self.enable_persistence:
            self._save_profile(profile)
        
        return profile
    
    def load_user(self, user_id: str) -> Optional[UserProfile]:
        """
        Carrega perfil de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Perfil do usuário ou None se não encontrado
        """
        # Verificar cache em memória
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # Tentar carregar do disco
        if self.enable_persistence:
            profile = self._load_profile(user_id)
            if profile:
                self.user_profiles[user_id] = profile
                return profile
        
        return None
    
    def set_current_user(self, user_id: str) -> bool:
        """
        Define o usuário atual
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se usuário foi definido
        """
        profile = self.load_user(user_id)
        if not profile:
            profile = self.create_user(user_id)
        
        self.current_user_id = user_id
        return True
    
    def get_current_user(self) -> Optional[UserProfile]:
        """Retorna o perfil do usuário atual"""
        if not self.current_user_id:
            return None
        return self.user_profiles.get(self.current_user_id)
    
    def record_interaction(self, user_input: str, avatar_response: str, 
                          interaction_type: str = "question", 
                          duration_seconds: float = 0.0) -> bool:
        """
        Registra uma interação
        
        Args:
            user_input: Entrada do usuário
            avatar_response: Resposta do avatar
            interaction_type: Tipo de interação
            duration_seconds: Duração em segundos
            
        Returns:
            True se registrado com sucesso
        """
        profile = self.get_current_user()
        if not profile:
            return False
        
        record = InteractionRecord(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            avatar_response=avatar_response,
            interaction_type=interaction_type,
            duration_seconds=duration_seconds
        )
        
        profile.interaction_history.append(record)
        profile.last_interaction = datetime.now().isoformat()
        
        # Manter limite de histórico
        if len(profile.interaction_history) > self.max_history_per_user:
            profile.interaction_history = profile.interaction_history[-self.max_history_per_user:]
        
        # Atualizar padrões de comunicação
        self._update_communication_patterns(profile)
        
        if self.enable_persistence:
            self._save_profile(profile)
        
        return True
    
    def rate_interaction(self, interaction_index: int, rating: int) -> bool:
        """
        Avalia uma interação anterior
        
        Args:
            interaction_index: Índice da interação no histórico
            rating: Avaliação (1-5 estrelas)
            
        Returns:
            True se avaliação foi registrada
        """
        profile = self.get_current_user()
        if not profile or interaction_index >= len(profile.interaction_history):
            return False
        
        if rating < 1 or rating > 5:
            return False
        
        profile.interaction_history[interaction_index].user_satisfaction = rating
        
        if self.enable_persistence:
            self._save_profile(profile)
        
        return True
    
    def get_interaction_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retorna histórico de interações
        
        Args:
            limit: Número máximo de interações (usa padrão se None)
            
        Returns:
            Lista de interações
        """
        profile = self.get_current_user()
        if not profile:
            return []
        
        limit = limit or self.max_history_per_user
        history = profile.interaction_history[-limit:]
        
        return [asdict(record) for record in history]
    
    def set_preferences(self, preferences: Dict) -> bool:
        """
        Atualiza preferências do usuário
        
        Args:
            preferences: Dicionário com novas preferências
            
        Returns:
            True se atualizado
        """
        profile = self.get_current_user()
        if not profile:
            return False
        
        for key, value in preferences.items():
            if hasattr(profile.preferences, key):
                setattr(profile.preferences, key, value)
        
        if self.enable_persistence:
            self._save_profile(profile)
        
        return True
    
    def get_preferences(self) -> Optional[Dict]:
        """Retorna preferências do usuário atual"""
        profile = self.get_current_user()
        if not profile:
            return None
        return asdict(profile.preferences)
    
    def get_communication_tone(self) -> str:
        """Retorna o tom de comunicação do usuário atual"""
        profile = self.get_current_user()
        if not profile:
            return "professional"
        return profile.preferences.communication_tone
    
    def set_communication_tone(self, tone: str) -> bool:
        """
        Define o tom de comunicação
        
        Args:
            tone: Novo tom (professional, casual, friendly, formal)
            
        Returns:
            True se definido
        """
        valid_tones = ["professional", "casual", "friendly", "formal"]
        if tone not in valid_tones:
            return False
        
        return self.set_preferences({"communication_tone": tone})
    
    def _update_communication_patterns(self, profile: UserProfile) -> None:
        """
        Analisa e atualiza padrões de comunicação do usuário
        
        Args:
            profile: Perfil do usuário
        """
        if not profile.interaction_history:
            return
        
        # Análise simples de padrões
        total_interactions = len(profile.interaction_history)
        question_count = sum(1 for r in profile.interaction_history if r.interaction_type == "question")
        avg_duration = sum(r.duration_seconds for r in profile.interaction_history) / total_interactions
        
        profile.communication_patterns = {
            "total_interactions": total_interactions,
            "question_percentage": (question_count / total_interactions * 100) if total_interactions > 0 else 0,
            "average_interaction_duration": avg_duration,
            "last_interaction_type": profile.interaction_history[-1].interaction_type if profile.interaction_history else None
        }
    
    def _save_profile(self, profile: UserProfile) -> None:
        """Salva perfil em disco"""
        try:
            file_path = os.path.join(self.storage_dir, f"{profile.user_id}.json")
            
            # Converter para dicionário serializável
            data = {
                "user_id": profile.user_id,
                "created_at": profile.created_at,
                "last_interaction": profile.last_interaction,
                "preferences": asdict(profile.preferences),
                "interaction_history": [asdict(r) for r in profile.interaction_history],
                "personality_traits": profile.personality_traits,
                "communication_patterns": profile.communication_patterns
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profile: {e}")
    
    def _load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Carrega perfil do disco"""
        try:
            file_path = os.path.join(self.storage_dir, f"{user_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir objetos
            preferences = UserPreferences(**data.get("preferences", {}))
            history = [
                InteractionRecord(**record)
                for record in data.get("interaction_history", [])
            ]
            
            profile = UserProfile(
                user_id=data["user_id"],
                created_at=data["created_at"],
                last_interaction=data["last_interaction"],
                preferences=preferences,
                interaction_history=history,
                personality_traits=data.get("personality_traits", {}),
                communication_patterns=data.get("communication_patterns", {})
            )
            
            return profile
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def export_profile(self) -> Optional[Dict]:
        """Exporta perfil do usuário atual"""
        profile = self.get_current_user()
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "created_at": profile.created_at,
            "last_interaction": profile.last_interaction,
            "preferences": asdict(profile.preferences),
            "interaction_count": len(profile.interaction_history),
            "communication_patterns": profile.communication_patterns
        }


# Exemplo de uso
if __name__ == "__main__":
    soulx = SoulXEngine({
        "storage_dir": "./soulx_test",
        "max_history_per_user": 50,
        "enable_persistence": True
    })
    
    print("SoulX Engine initialized")
    
    # Criar usuário
    soulx.set_current_user("user_123")
    user = soulx.get_current_user()
    print(f"User created: {user.user_id}")
    
    # Registrar interações
    soulx.record_interaction(
        "What is AI?",
        "AI is Artificial Intelligence...",
        "question",
        2.5
    )
    
    # Definir preferências
    soulx.set_preferences({"communication_tone": "casual"})
    
    # Obter histórico
    history = soulx.get_interaction_history()
    print(f"Interactions: {len(history)}")
    
    # Exportar perfil
    profile = soulx.export_profile()
    print(f"Profile: {profile}")
