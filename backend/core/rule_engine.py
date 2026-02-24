"""
ATTI Rule Engine v2.0
Sistema de regras determinístico baseado em JSON.
Independente de LLM, com prioridade de execução e matching por contexto.
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import re


class RuleOperator(Enum):
    """Operadores disponíveis para regras"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    IN_LIST = "in"
    NOT_IN_LIST = "not_in"
    EXISTS = "exists"


@dataclass
class RuleCondition:
    """Condição de uma regra"""
    field: str
    operator: RuleOperator
    value: Any


@dataclass
class RuleAction:
    """Ação a executar quando regra é acionada"""
    type: str  # "response", "function", "redirect", "log"
    target: str
    parameters: Dict = None


@dataclass
class Rule:
    """Definição de uma regra"""
    name: str
    description: str
    priority: int  # Maior = executado primeiro
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    enabled: bool = True
    max_executions: Optional[int] = None  # None = ilimitado


class RuleEngine:
    """
    Motor de Regras Determinístico para Avatar ATTI v2.0
    
    Características:
    - Regras baseadas em JSON
    - Prioridade de execução
    - Matching por contexto
    - Sem dependência de LLM
    - Suporte a múltiplas condições
    - Ações configuráveis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor de regras
        
        Args:
            config: Dicionário com configurações:
                - rules_file: Caminho para arquivo JSON com regras
                - enable_logging: Registrar execução de regras
        """
        self.config = config or {}
        self.rules: Dict[str, Rule] = {}
        self.execution_count: Dict[str, int] = {}
        self.enable_logging = self.config.get("enable_logging", True)
        self.custom_actions: Dict[str, Callable] = {}
        
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Registra regras padrão do sistema"""
        
        # Regra: Saudação
        greeting_rule = Rule(
            name="greeting",
            description="Responde a saudações",
            priority=100,
            conditions=[
                RuleCondition("input", RuleOperator.REGEX, r"^(hi|hello|oi|olá|hola).*$")
            ],
            actions=[
                RuleAction("response", "greeting_response", {"tone": "friendly"})
            ]
        )
        self.register_rule(greeting_rule)
        
        # Regra: Despedida
        goodbye_rule = Rule(
            name="goodbye",
            description="Responde a despedidas",
            priority=100,
            conditions=[
                RuleCondition("input", RuleOperator.REGEX, r"^(bye|goodbye|adeus|adiós).*$")
            ],
            actions=[
                RuleAction("response", "goodbye_response", {"tone": "friendly"})
            ]
        )
        self.register_rule(goodbye_rule)
        
        # Regra: Erro de conexão
        error_rule = Rule(
            name="connection_error",
            description="Trata erros de conexão",
            priority=200,
            conditions=[
                RuleCondition("error_type", RuleOperator.EQUALS, "connection_error")
            ],
            actions=[
                RuleAction("response", "error_response", {"type": "connection"})
            ]
        )
        self.register_rule(error_rule)
    
    def register_rule(self, rule: Rule) -> None:
        """Registra uma nova regra"""
        self.rules[rule.name] = rule
        self.execution_count[rule.name] = 0
    
    def register_custom_action(self, action_name: str, handler: Callable) -> None:
        """
        Registra uma ação customizada
        
        Args:
            action_name: Nome da ação
            handler: Função que executa a ação
        """
        self.custom_actions[action_name] = handler
    
    def _evaluate_condition(self, condition: RuleCondition, context: Dict) -> bool:
        """
        Avalia uma condição contra o contexto
        
        Args:
            condition: Condição a avaliar
            context: Dicionário com contexto
            
        Returns:
            True se condição é atendida
        """
        field_value = context.get(condition.field)
        target_value = condition.value
        
        if condition.operator == RuleOperator.EQUALS:
            return field_value == target_value
        
        elif condition.operator == RuleOperator.NOT_EQUALS:
            return field_value != target_value
        
        elif condition.operator == RuleOperator.GREATER_THAN:
            try:
                return float(field_value) > float(target_value)
            except (ValueError, TypeError):
                return False
        
        elif condition.operator == RuleOperator.GREATER_EQUAL:
            try:
                return float(field_value) >= float(target_value)
            except (ValueError, TypeError):
                return False
        
        elif condition.operator == RuleOperator.LESS_THAN:
            try:
                return float(field_value) < float(target_value)
            except (ValueError, TypeError):
                return False
        
        elif condition.operator == RuleOperator.LESS_EQUAL:
            try:
                return float(field_value) <= float(target_value)
            except (ValueError, TypeError):
                return False
        
        elif condition.operator == RuleOperator.CONTAINS:
            return target_value in str(field_value)
        
        elif condition.operator == RuleOperator.NOT_CONTAINS:
            return target_value not in str(field_value)
        
        elif condition.operator == RuleOperator.REGEX:
            try:
                return bool(re.search(target_value, str(field_value), re.IGNORECASE))
            except re.error:
                return False
        
        elif condition.operator == RuleOperator.IN_LIST:
            return field_value in target_value if isinstance(target_value, list) else False
        
        elif condition.operator == RuleOperator.NOT_IN_LIST:
            return field_value not in target_value if isinstance(target_value, list) else True
        
        elif condition.operator == RuleOperator.EXISTS:
            return condition.field in context
        
        return False
    
    def evaluate_rule(self, rule: Rule, context: Dict) -> bool:
        """
        Avalia se uma regra deve ser acionada
        
        Args:
            rule: Regra a avaliar
            context: Dicionário com contexto
            
        Returns:
            True se todas as condições são atendidas
        """
        if not rule.enabled:
            return False
        
        # Verificar limite de execuções
        if rule.max_executions:
            if self.execution_count.get(rule.name, 0) >= rule.max_executions:
                return False
        
        # Avaliar todas as condições (AND)
        return all(
            self._evaluate_condition(condition, context)
            for condition in rule.conditions
        )
    
    def match_rules(self, context: Dict) -> List[Rule]:
        """
        Encontra todas as regras que correspondem ao contexto
        
        Args:
            context: Dicionário com contexto
            
        Returns:
            Lista de regras ordenadas por prioridade
        """
        matching_rules = [
            rule for rule in self.rules.values()
            if self.evaluate_rule(rule, context)
        ]
        
        # Ordenar por prioridade (maior primeiro)
        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return matching_rules
    
    def execute_rule(self, rule: Rule, context: Dict) -> Dict:
        """
        Executa uma regra
        
        Args:
            rule: Regra a executar
            context: Contexto de execução
            
        Returns:
            Dicionário com resultado
        """
        result = {
            "rule_name": rule.name,
            "executed": False,
            "actions": []
        }
        
        if not self.evaluate_rule(rule, context):
            return result
        
        # Executar ações
        for action in rule.actions:
            action_result = self._execute_action(action, context)
            result["actions"].append(action_result)
        
        # Incrementar contador
        self.execution_count[rule.name] = self.execution_count.get(rule.name, 0) + 1
        result["executed"] = True
        
        if self.enable_logging:
            print(f"[RULE] Executed: {rule.name}")
        
        return result
    
    def _execute_action(self, action: RuleAction, context: Dict) -> Dict:
        """
        Executa uma ação
        
        Args:
            action: Ação a executar
            context: Contexto
            
        Returns:
            Resultado da ação
        """
        result = {
            "action_type": action.type,
            "target": action.target,
            "success": False,
            "result": None
        }
        
        try:
            if action.type == "response":
                result["result"] = self._generate_response(action.target, action.parameters or {})
                result["success"] = True
            
            elif action.type == "function":
                if action.target in self.custom_actions:
                    result["result"] = self.custom_actions[action.target](context, action.parameters or {})
                    result["success"] = True
            
            elif action.type == "log":
                print(f"[LOG] {action.target}: {action.parameters}")
                result["success"] = True
            
            elif action.type == "redirect":
                result["result"] = {"redirect_to": action.target}
                result["success"] = True
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _generate_response(self, response_type: str, parameters: Dict) -> str:
        """Gera resposta baseada no tipo"""
        responses = {
            "greeting_response": "Hello! How can I help you?",
            "goodbye_response": "Goodbye! Have a great day!",
            "error_response": "I encountered an error. Please try again.",
        }
        
        return responses.get(response_type, "I'm here to help!")
    
    def process_context(self, context: Dict) -> Dict:
        """
        Processa contexto e executa regras aplicáveis
        
        Args:
            context: Dicionário com contexto
            
        Returns:
            Resultado do processamento
        """
        matching_rules = self.match_rules(context)
        
        result = {
            "matching_rules": len(matching_rules),
            "executed_rules": [],
            "responses": []
        }
        
        # Executar primeira regra que corresponde (ou todas, dependendo da configuração)
        for rule in matching_rules:
            execution_result = self.execute_rule(rule, context)
            result["executed_rules"].append(execution_result)
            
            # Parar na primeira regra executada (pode ser configurável)
            if execution_result["executed"]:
                break
        
        return result
    
    def load_rules_from_json(self, json_path: str) -> bool:
        """
        Carrega regras de arquivo JSON
        
        Args:
            json_path: Caminho do arquivo JSON
            
        Returns:
            True se carregado com sucesso
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            for rule_data in rules_data.get("rules", []):
                conditions = [
                    RuleCondition(
                        field=c["field"],
                        operator=RuleOperator(c["operator"]),
                        value=c["value"]
                    )
                    for c in rule_data.get("conditions", [])
                ]
                
                actions = [
                    RuleAction(
                        type=a["type"],
                        target=a["target"],
                        parameters=a.get("parameters")
                    )
                    for a in rule_data.get("actions", [])
                ]
                
                rule = Rule(
                    name=rule_data["name"],
                    description=rule_data.get("description", ""),
                    priority=rule_data.get("priority", 0),
                    conditions=conditions,
                    actions=actions,
                    enabled=rule_data.get("enabled", True),
                    max_executions=rule_data.get("max_executions")
                )
                
                self.register_rule(rule)
            
            return True
        except Exception as e:
            print(f"Error loading rules: {e}")
            return False
    
    def export_rules(self) -> Dict:
        """Exporta todas as regras em formato JSON"""
        return {
            "rules": [
                {
                    "name": rule.name,
                    "description": rule.description,
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "conditions": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value
                        }
                        for c in rule.conditions
                    ],
                    "actions": [
                        {
                            "type": a.type,
                            "target": a.target,
                            "parameters": a.parameters
                        }
                        for a in rule.actions
                    ]
                }
                for rule in self.rules.values()
            ]
        }


# Exemplo de uso
if __name__ == "__main__":
    engine = RuleEngine({
        "enable_logging": True
    })
    
    print("Rule Engine initialized")
    print(f"Registered rules: {list(engine.rules.keys())}")
    
    # Testar contexto
    context = {
        "input": "Hello there!",
        "user_id": "user_123"
    }
    
    # Encontrar regras
    matching = engine.match_rules(context)
    print(f"Matching rules: {[r.name for r in matching]}")
    
    # Processar contexto
    result = engine.process_context(context)
    print(f"Result: {result}")
