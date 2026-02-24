"""
ATTI Zero-Config Engine v2.0
Sistema de auto-detecção de ambiente, criação automática de configuração padrão e boot fail-safe.
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime
import platform
import sys


class ZeroConfigEngine:
    """
    Motor Zero-Config para Avatar ATTI v2.0
    
    Características:
    - Auto-detecção de ambiente (dev, staging, prod)
    - Criação automática de configuração padrão
    - Fail-safe boot
    - Setup automático inicial
    - Validação de dependências
    """
    
    # Configurações padrão por ambiente
    DEFAULT_CONFIGS = {
        "development": {
            "debug": True,
            "log_level": "DEBUG",
            "database": "sqlite:///./atti_dev.db",
            "api_timeout": 30,
            "cache_enabled": False,
            "cors_origins": ["http://localhost:3000", "http://localhost:8000"],
            "rate_limit_enabled": False
        },
        "staging": {
            "debug": False,
            "log_level": "INFO",
            "database": "postgresql://user:pass@localhost/atti_staging",
            "api_timeout": 60,
            "cache_enabled": True,
            "cors_origins": ["https://staging.example.com"],
            "rate_limit_enabled": True,
            "rate_limit_requests": 100,
            "rate_limit_period": 3600
        },
        "production": {
            "debug": False,
            "log_level": "WARNING",
            "database": "postgresql://user:pass@prod-server/atti_prod",
            "api_timeout": 120,
            "cache_enabled": True,
            "cors_origins": ["https://example.com"],
            "rate_limit_enabled": True,
            "rate_limit_requests": 1000,
            "rate_limit_period": 3600,
            "ssl_enabled": True
        }
    }
    
    def __init__(self, config_dir: str = "./config"):
        """
        Inicializa o motor zero-config
        
        Args:
            config_dir: Diretório para armazenar configurações
        """
        self.config_dir = config_dir
        self.environment = self._detect_environment()
        self.config: Dict = {}
        
        # Criar diretório se não existir
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        
        # Carregar ou criar configuração
        self._initialize_config()
    
    def _detect_environment(self) -> str:
        """
        Detecta o ambiente atual
        
        Prioridade:
        1. Variável ENVIRONMENT
        2. Variável NODE_ENV
        3. Padrão: development
        
        Returns:
            Nome do ambiente (development, staging, production)
        """
        env = os.getenv("ENVIRONMENT") or os.getenv("NODE_ENV") or "development"
        
        # Validar ambiente
        if env not in self.DEFAULT_CONFIGS:
            print(f"Warning: Unknown environment '{env}', using 'development'")
            return "development"
        
        return env
    
    def _initialize_config(self) -> None:
        """Inicializa configuração do sistema"""
        config_file = os.path.join(self.config_dir, f"{self.environment}.json")
        
        # Tentar carregar configuração existente
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✓ Configuration loaded from {config_file}")
                return
            except Exception as e:
                print(f"Warning: Error loading config: {e}")
        
        # Criar configuração padrão
        self._create_default_config(config_file)
    
    def _create_default_config(self, config_file: str) -> None:
        """Cria arquivo de configuração padrão"""
        try:
            # Obter configuração padrão
            default_config = self.DEFAULT_CONFIGS.get(self.environment, {}).copy()
            
            # Adicionar metadados
            default_config["_metadata"] = {
                "environment": self.environment,
                "created_at": datetime.now().isoformat(),
                "auto_generated": True,
                "version": "2.0.0"
            }
            
            # Sobrescrever com variáveis de ambiente
            self._apply_env_overrides(default_config)
            
            # Salvar arquivo
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            self.config = default_config
            print(f"✓ Default configuration created at {config_file}")
            
        except Exception as e:
            print(f"Error creating config: {e}")
            # Usar configuração em memória como fallback
            self.config = self.DEFAULT_CONFIGS.get(self.environment, {})
    
    def _apply_env_overrides(self, config: Dict) -> None:
        """Aplica sobrescrita de variáveis de ambiente"""
        env_mappings = {
            "DATABASE_URL": "database",
            "LOG_LEVEL": "log_level",
            "API_TIMEOUT": "api_timeout",
            "DEBUG": "debug",
            "CORS_ORIGINS": "cors_origins"
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Converter tipos
                if config_key == "debug":
                    config[config_key] = value.lower() == "true"
                elif config_key == "api_timeout":
                    config[config_key] = int(value)
                elif config_key == "cors_origins":
                    config[config_key] = value.split(",")
                else:
                    config[config_key] = value
    
    def get_config(self, key: Optional[str] = None, default: any = None) -> any:
        """
        Obtém valor de configuração
        
        Args:
            key: Chave da configuração (ex: "database", "log_level")
            default: Valor padrão se chave não encontrada
            
        Returns:
            Valor da configuração
        """
        if key is None:
            return self.config
        
        return self.config.get(key, default)
    
    def get_environment(self) -> str:
        """Retorna o ambiente atual"""
        return self.environment
    
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.environment == "development"
    
    def validate_dependencies(self) -> Dict[str, bool]:
        """
        Valida dependências do sistema
        
        Returns:
            Dicionário com status de cada dependência
        """
        dependencies = {
            "python": self._check_python(),
            "pip": self._check_pip(),
            "git": self._check_git(),
            "database": self._check_database(),
            "network": self._check_network()
        }
        
        return dependencies
    
    def _check_python(self) -> bool:
        """Verifica versão do Python"""
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            print(f"✓ Python {current_version[0]}.{current_version[1]} OK")
            return True
        else:
            print(f"✗ Python {required_version[0]}.{required_version[1]}+ required")
            return False
    
    def _check_pip(self) -> bool:
        """Verifica se pip está disponível"""
        try:
            import pip
            print(f"✓ pip available")
            return True
        except ImportError:
            print(f"✗ pip not available")
            return False
    
    def _check_git(self) -> bool:
        """Verifica se git está disponível"""
        try:
            import subprocess
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            print(f"✓ git available")
            return True
        except:
            print(f"✗ git not available")
            return False
    
    def _check_database(self) -> bool:
        """Verifica conectividade com banco de dados"""
        try:
            # Validação básica da URL
            db_url = self.config.get("database", "")
            if db_url and ("sqlite" in db_url or "postgresql" in db_url):
                print(f"✓ Database URL configured")
                return True
            else:
                print(f"⚠ Database not configured")
                return False
        except:
            print(f"✗ Database check failed")
            return False
    
    def _check_network(self) -> bool:
        """Verifica conectividade de rede"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            print(f"✓ Network connectivity OK")
            return True
        except:
            print(f"⚠ Network connectivity limited")
            return False
    
    def get_system_info(self) -> Dict:
        """Retorna informações do sistema"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "environment": self.environment,
            "config_dir": self.config_dir,
            "timestamp": datetime.now().isoformat()
        }
    
    def perform_health_check(self) -> Dict:
        """
        Realiza health check completo
        
        Returns:
            Dicionário com status de saúde
        """
        print("\n" + "="*50)
        print("ATTI Avatar Zero-Config Health Check")
        print("="*50 + "\n")
        
        system_info = self.get_system_info()
        print(f"Environment: {system_info['environment']}")
        print(f"Platform: {system_info['platform']}")
        print(f"Python: {system_info['python_version']}\n")
        
        dependencies = self.validate_dependencies()
        
        print("\n" + "="*50)
        all_ok = all(dependencies.values())
        status = "✓ READY" if all_ok else "⚠ WARNINGS"
        print(f"Status: {status}")
        print("="*50 + "\n")
        
        return {
            "system_info": system_info,
            "dependencies": dependencies,
            "all_ok": all_ok
        }
    
    def export_config(self) -> Dict:
        """Exporta configuração atual"""
        return {
            "environment": self.environment,
            "config": self.config,
            "system_info": self.get_system_info()
        }


# Exemplo de uso
if __name__ == "__main__":
    zero_config = ZeroConfigEngine("./config")
    
    print("Zero-Config Engine initialized")
    print(f"Environment: {zero_config.get_environment()}")
    print(f"Is Production: {zero_config.is_production()}")
    
    # Health check
    health = zero_config.perform_health_check()
    
    # Obter configuração
    config = zero_config.get_config()
    print(f"\nConfiguration: {json.dumps(config, indent=2)}")
