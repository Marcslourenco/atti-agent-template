"""
ATTI Proactive Intelligence Engine v2.0
Sistema de observação de contexto e sugestões automáticas baseadas em regras.
Determinístico, sem dependência de LLM.
"""

import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class ContextType(Enum):
    """Tipos de contexto observáveis"""
    USER_BEHAVIOR = "user_behavior"
    PAGE_CONTENT = "page_content"
    TIME_BASED = "time_based"
    INTERACTION_PATTERN = "interaction_pattern"
    ERROR_STATE = "error_state"


@dataclass
class ContextObservation:
    """Observação de contexto"""
    context_type: ContextType
    key: str
    value: str
    confidence: float  # 0.0 a 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProactiveTrigger:
    """Definição de trigger para sugestão proativa"""
    name: str
    conditions: List[Dict]  # Lista de condições que devem ser atendidas
    suggestion: str
    priority: int = 0
    cooldown_ms: int = 5000  # Tempo mínimo entre sugestões iguais
    max_triggers_per_session: int = 3


class ProactiveEngine:
    """
    Motor de inteligência proativa para Avatar ATTI v2.0
    
    Características:
    - Observação contínua de contexto
    - Triggers baseados em regras determinísticas
    - Sugestões automáticas sem LLM
    - Classificação de padrões de interação
    - Sistema de prioridades
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor proativo
        
        Args:
            config: Dicionário com configurações:
                - enable_proactive: Ativar sugestões (padrão: True)
                - observation_interval_ms: Intervalo de observação (padrão: 1000)
                - max_observations: Máximo de observações em buffer (padrão: 100)
        """
        self.config = config or {}
        self.enable_proactive = self.config.get("enable_proactive", True)
        self.observation_interval_ms = self.config.get("observation_interval_ms", 1000)
        self.max_observations = self.config.get("max_observations", 100)
        
        self.observations: List[ContextObservation] = []
        self.triggers: Dict[str, ProactiveTrigger] = {}
        self.last_observation_time = 0
        self.triggered_suggestions: Dict[str, float] = {}  # name -> timestamp
        self.trigger_count_per_session: Dict[str, int] = {}
        
        self._register_default_triggers()
    
    def _register_default_triggers(self):
        """Registra triggers padrão do sistema"""
        
        # Trigger: Usuário inativo por muito tempo
        trigger_inactivity = ProactiveTrigger(
            name="inactivity_suggestion",
            conditions=[
                {"type": "interaction_pattern", "key": "last_interaction_ms", "operator": "gt", "value": 30000}
            ],
            suggestion="Parece que você não interage há um tempo. Posso ajudar com algo?",
            priority=1,
            cooldown_ms=10000,
            max_triggers_per_session=2
        )
        self.register_trigger(trigger_inactivity)
        
        # Trigger: Múltiplas tentativas falhadas
        trigger_error = ProactiveTrigger(
            name="error_recovery_suggestion",
            conditions=[
                {"type": "error_state", "key": "consecutive_errors", "operator": "gte", "value": 2}
            ],
            suggestion="Parece que algo deu errado. Deixe-me tentar de outra forma.",
            priority=2,
            cooldown_ms=5000,
            max_triggers_per_session=3
        )
        self.register_trigger(trigger_error)
        
        # Trigger: Padrão de busca detectado
        trigger_search_pattern = ProactiveTrigger(
            name="search_pattern_suggestion",
            conditions=[
                {"type": "interaction_pattern", "key": "search_count", "operator": "gt", "value": 3},
                {"type": "interaction_pattern", "key": "search_time_window_ms", "operator": "lt", "value": 60000}
            ],
            suggestion="Vejo que você está buscando algo específico. Quer que eu refine a busca?",
            priority=1,
            cooldown_ms=8000,
            max_triggers_per_session=2
        )
        self.register_trigger(trigger_search_pattern)
    
    def register_trigger(self, trigger: ProactiveTrigger) -> None:
        """Registra um novo trigger no sistema"""
        self.triggers[trigger.name] = trigger
        self.trigger_count_per_session[trigger.name] = 0
    
    def observe_context(self, context_type: ContextType, key: str, value: str, 
                       confidence: float = 1.0) -> None:
        """
        Registra uma observação de contexto
        
        Args:
            context_type: Tipo de contexto
            key: Chave da observação
            value: Valor observado
            confidence: Confiança da observação (0.0 a 1.0)
        """
        observation = ContextObservation(
            context_type=context_type,
            key=key,
            value=value,
            confidence=confidence
        )
        
        self.observations.append(observation)
        
        # Manter buffer limitado
        if len(self.observations) > self.max_observations:
            self.observations.pop(0)
    
    def get_recent_observations(self, context_type: Optional[ContextType] = None, 
                               time_window_ms: int = 5000) -> List[ContextObservation]:
        """
        Retorna observações recentes
        
        Args:
            context_type: Filtrar por tipo (opcional)
            time_window_ms: Janela de tempo em ms
            
        Returns:
            Lista de observações recentes
        """
        current_time = time.time()
        threshold = current_time - (time_window_ms / 1000)
        
        result = [
            obs for obs in self.observations
            if obs.timestamp >= threshold
        ]
        
        if context_type:
            result = [obs for obs in result if obs.context_type == context_type]
        
        return result
    
    def _evaluate_condition(self, condition: Dict, observations: List[ContextObservation]) -> bool:
        """
        Avalia uma condição contra observações
        
        Args:
            condition: Dicionário com condição
            observations: Lista de observações
            
        Returns:
            True se condição é atendida
        """
        context_type = ContextType(condition.get("type"))
        key = condition.get("key")
        operator = condition.get("operator")
        target_value = condition.get("value")
        
        # Encontrar observação relevante
        matching_obs = [
            obs for obs in observations
            if obs.context_type == context_type and obs.key == key
        ]
        
        if not matching_obs:
            return False
        
        # Usar observação mais recente
        obs_value = matching_obs[-1].value
        
        # Converter para número se necessário
        try:
            obs_value = float(obs_value)
            target_value = float(target_value)
        except (ValueError, TypeError):
            pass
        
        # Avaliar operador
        if operator == "eq":
            return obs_value == target_value
        elif operator == "ne":
            return obs_value != target_value
        elif operator == "gt":
            return obs_value > target_value
        elif operator == "gte":
            return obs_value >= target_value
        elif operator == "lt":
            return obs_value < target_value
        elif operator == "lte":
            return obs_value <= target_value
        elif operator == "contains":
            return target_value in str(obs_value)
        
        return False
    
    def evaluate_triggers(self) -> Optional[ProactiveTrigger]:
        """
        Avalia todos os triggers registrados
        
        Returns:
            Primeiro trigger que atende as condições, ou None
        """
        if not self.enable_proactive:
            return None
        
        current_time = time.time()
        recent_obs = self.get_recent_observations(time_window_ms=10000)
        
        # Ordenar triggers por prioridade
        sorted_triggers = sorted(
            self.triggers.values(),
            key=lambda t: t.priority,
            reverse=True
        )
        
        for trigger in sorted_triggers:
            # Verificar cooldown
            last_trigger_time = self.triggered_suggestions.get(trigger.name, 0)
            if current_time - last_trigger_time < (trigger.cooldown_ms / 1000):
                continue
            
            # Verificar limite de triggers por sessão
            if self.trigger_count_per_session.get(trigger.name, 0) >= trigger.max_triggers_per_session:
                continue
            
            # Avaliar todas as condições
            all_conditions_met = all(
                self._evaluate_condition(condition, recent_obs)
                for condition in trigger.conditions
            )
            
            if all_conditions_met:
                # Registrar trigger
                self.triggered_suggestions[trigger.name] = current_time
                self.trigger_count_per_session[trigger.name] += 1
                return trigger
        
        return None
    
    def get_suggestion(self) -> Optional[str]:
        """
        Obtém uma sugestão proativa se disponível
        
        Returns:
            String com sugestão ou None
        """
        trigger = self.evaluate_triggers()
        return trigger.suggestion if trigger else None
    
    def classify_interaction_pattern(self) -> Dict[str, any]:
        """
        Classifica o padrão de interação atual
        
        Returns:
            Dicionário com classificação do padrão
        """
        recent_obs = self.get_recent_observations(time_window_ms=60000)
        
        pattern = {
            "total_interactions": len(recent_obs),
            "error_count": len([o for o in recent_obs if o.context_type == ContextType.ERROR_STATE]),
            "search_count": len([o for o in recent_obs if o.key == "search"]),
            "user_engaged": len(recent_obs) > 5,
            "error_rate": 0.0
        }
        
        if pattern["total_interactions"] > 0:
            pattern["error_rate"] = pattern["error_count"] / pattern["total_interactions"]
        
        return pattern
    
    def reset_session(self) -> None:
        """Reseta contadores de sessão"""
        self.observations.clear()
        self.triggered_suggestions.clear()
        self.trigger_count_per_session = {name: 0 for name in self.triggers}
    
    def export_config(self) -> Dict:
        """Exporta configuração em JSON"""
        return {
            "enable_proactive": self.enable_proactive,
            "observation_interval_ms": self.observation_interval_ms,
            "max_observations": self.max_observations,
            "triggers": {
                name: {
                    "conditions": len(trigger.conditions),
                    "priority": trigger.priority,
                    "cooldown_ms": trigger.cooldown_ms
                }
                for name, trigger in self.triggers.items()
            }
        }


# Exemplo de uso
if __name__ == "__main__":
    engine = ProactiveEngine({
        "enable_proactive": True,
        "observation_interval_ms": 1000,
        "max_observations": 100
    })
    
    print("Proactive Engine initialized")
    print(f"Registered triggers: {list(engine.triggers.keys())}")
    
    # Simular observações
    engine.observe_context(ContextType.INTERACTION_PATTERN, "last_interaction_ms", "35000", 1.0)
    
    # Avaliar triggers
    suggestion = engine.get_suggestion()
    print(f"Suggestion: {suggestion}")
    
    # Classificar padrão
    pattern = engine.classify_interaction_pattern()
    print(f"Pattern: {pattern}")
