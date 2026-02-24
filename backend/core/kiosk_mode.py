"""
ATTI Kiosk Mode Engine v2.0
Sistema de modo quiosque com bloqueio de fullscreen, desativação de navegação e sessão isolada.
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class KioskConfig:
    """Configuração do modo quiosque"""
    enabled: bool = False
    fullscreen_lock: bool = True
    disable_external_navigation: bool = True
    disable_back_button: bool = True
    disable_refresh: bool = True
    session_timeout_minutes: int = 30
    allowed_domains: list = None  # Lista de domínios permitidos
    show_exit_button: bool = False
    exit_password: Optional[str] = None
    custom_css: Optional[str] = None


class KioskMode:
    """
    Motor de Modo Quiosque para Avatar ATTI v2.0
    
    Características:
    - Bloqueio de fullscreen
    - Desativação de navegação externa
    - Sessão isolada e controlada
    - Timeout automático
    - Proteção por senha para sair
    - Customização de CSS
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o modo quiosque
        
        Args:
            config: Dicionário com configurações ou None para usar env vars
        """
        self.config = self._load_config(config)
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.session_active = False
        self.exit_attempts = 0
    
    def _load_config(self, config: Optional[Dict]) -> KioskConfig:
        """
        Carrega configuração de Kiosk
        
        Prioridade:
        1. Parâmetro config
        2. Variáveis de ambiente
        3. Valores padrão
        """
        if config:
            return KioskConfig(**config)
        
        # Carregar de variáveis de ambiente
        kiosk_config = KioskConfig()
        
        kiosk_config.enabled = os.getenv("KIOSK_MODE_ENABLED", "false").lower() == "true"
        kiosk_config.fullscreen_lock = os.getenv("KIOSK_FULLSCREEN_LOCK", "true").lower() == "true"
        kiosk_config.disable_external_navigation = os.getenv("KIOSK_DISABLE_NAV", "true").lower() == "true"
        kiosk_config.disable_back_button = os.getenv("KIOSK_DISABLE_BACK", "true").lower() == "true"
        kiosk_config.disable_refresh = os.getenv("KIOSK_DISABLE_REFRESH", "true").lower() == "true"
        kiosk_config.session_timeout_minutes = int(os.getenv("KIOSK_TIMEOUT_MIN", "30"))
        kiosk_config.show_exit_button = os.getenv("KIOSK_SHOW_EXIT", "false").lower() == "true"
        kiosk_config.exit_password = os.getenv("KIOSK_EXIT_PASSWORD", None)
        
        allowed_domains_str = os.getenv("KIOSK_ALLOWED_DOMAINS", "")
        kiosk_config.allowed_domains = [d.strip() for d in allowed_domains_str.split(",") if d.strip()]
        
        return kiosk_config
    
    def is_enabled(self) -> bool:
        """Retorna se modo quiosque está ativado"""
        return self.config.enabled
    
    def start_session(self) -> Dict:
        """
        Inicia uma sessão de quiosque
        
        Returns:
            Dicionário com informações da sessão
        """
        if not self.config.enabled:
            return {"success": False, "error": "Kiosk mode is not enabled"}
        
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.session_active = True
        self.exit_attempts = 0
        
        return {
            "success": True,
            "session_id": self._generate_session_id(),
            "start_time": self.session_start_time.isoformat(),
            "timeout_minutes": self.config.session_timeout_minutes,
            "config": self.get_client_config()
        }
    
    def end_session(self, password: Optional[str] = None) -> Dict:
        """
        Encerra a sessão de quiosque
        
        Args:
            password: Senha de saída (se configurada)
            
        Returns:
            Dicionário com resultado
        """
        if not self.session_active:
            return {"success": False, "error": "No active session"}
        
        # Verificar senha se configurada
        if self.config.exit_password:
            if not password or password != self.config.exit_password:
                self.exit_attempts += 1
                return {
                    "success": False,
                    "error": "Invalid exit password",
                    "attempts": self.exit_attempts
                }
        
        self.session_active = False
        
        return {
            "success": True,
            "session_duration_seconds": self._get_session_duration_seconds(),
            "exit_attempts": self.exit_attempts
        }
    
    def is_session_active(self) -> bool:
        """Verifica se sessão está ativa"""
        if not self.session_active:
            return False
        
        # Verificar timeout
        elapsed = datetime.now() - self.session_start_time
        timeout = timedelta(minutes=self.config.session_timeout_minutes)
        
        if elapsed > timeout:
            self.session_active = False
            return False
        
        return True
    
    def record_activity(self) -> None:
        """Registra atividade do usuário (atualiza timestamp)"""
        self.last_activity_time = datetime.now()
    
    def get_session_info(self) -> Dict:
        """Retorna informações da sessão atual"""
        return {
            "active": self.is_session_active(),
            "start_time": self.session_start_time.isoformat(),
            "duration_seconds": self._get_session_duration_seconds(),
            "timeout_minutes": self.config.session_timeout_minutes,
            "time_remaining_seconds": self._get_time_remaining_seconds(),
            "last_activity": self.last_activity_time.isoformat()
        }
    
    def validate_navigation(self, target_url: str) -> Dict:
        """
        Valida se navegação é permitida
        
        Args:
            target_url: URL de destino
            
        Returns:
            Dicionário com permissão
        """
        if not self.config.enabled:
            return {"allowed": True}
        
        if not self.config.disable_external_navigation:
            return {"allowed": True}
        
        # Extrair domínio da URL
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        target_domain = parsed.netloc
        
        # Verificar se domínio é permitido
        if self.config.allowed_domains:
            allowed = any(
                target_domain.endswith(domain) or target_domain == domain
                for domain in self.config.allowed_domains
            )
            return {
                "allowed": allowed,
                "reason": "Domain not in allowed list" if not allowed else None
            }
        
        return {"allowed": False, "reason": "External navigation disabled"}
    
    def get_client_config(self) -> Dict:
        """
        Retorna configuração para enviar ao cliente (JavaScript)
        
        Returns:
            Dicionário com configuração do cliente
        """
        return {
            "kioskModeEnabled": self.config.enabled,
            "fullscreenLock": self.config.fullscreen_lock,
            "disableExternalNavigation": self.config.disable_external_navigation,
            "disableBackButton": self.config.disable_back_button,
            "disableRefresh": self.config.disable_refresh,
            "sessionTimeoutMinutes": self.config.session_timeout_minutes,
            "showExitButton": self.config.show_exit_button,
            "requireExitPassword": self.config.exit_password is not None,
            "allowedDomains": self.config.allowed_domains or []
        }
    
    def get_client_css(self) -> str:
        """
        Retorna CSS para aplicar no cliente
        
        Returns:
            String com CSS
        """
        css = """
        /* Kiosk Mode CSS */
        body {
            overflow: hidden;
            margin: 0;
            padding: 0;
        }
        
        /* Desabilitar seleção de texto */
        body {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        
        /* Esconder elementos de navegação */
        nav, .navbar, .header-nav {
            display: none !important;
        }
        
        /* Fullscreen */
        .kiosk-container {
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }
        """
        
        if self.config.custom_css:
            css += "\n" + self.config.custom_css
        
        return css
    
    def get_exit_button_html(self) -> str:
        """Retorna HTML do botão de saída (se habilitado)"""
        if not self.config.show_exit_button:
            return ""
        
        if self.config.exit_password:
            return """
            <button id="kiosk-exit-btn" class="kiosk-exit-button" onclick="showExitPassword()">
                Sair
            </button>
            <div id="kiosk-exit-modal" class="kiosk-modal" style="display:none;">
                <div class="kiosk-modal-content">
                    <h3>Digite a senha para sair</h3>
                    <input type="password" id="kiosk-exit-password" placeholder="Senha">
                    <button onclick="submitExitPassword()">Confirmar</button>
                    <button onclick="closeExitModal()">Cancelar</button>
                </div>
            </div>
            """
        else:
            return """
            <button id="kiosk-exit-btn" class="kiosk-exit-button" onclick="exitKioskMode()">
                Sair
            </button>
            """
    
    def _generate_session_id(self) -> str:
        """Gera ID único para sessão"""
        import uuid
        return str(uuid.uuid4())
    
    def _get_session_duration_seconds(self) -> int:
        """Retorna duração da sessão em segundos"""
        elapsed = datetime.now() - self.session_start_time
        return int(elapsed.total_seconds())
    
    def _get_time_remaining_seconds(self) -> int:
        """Retorna tempo restante em segundos"""
        elapsed = datetime.now() - self.session_start_time
        timeout = timedelta(minutes=self.config.session_timeout_minutes)
        remaining = timeout - elapsed
        return max(0, int(remaining.total_seconds()))
    
    def export_config(self) -> Dict:
        """Exporta configuração em JSON"""
        return {
            "enabled": self.config.enabled,
            "fullscreen_lock": self.config.fullscreen_lock,
            "disable_external_navigation": self.config.disable_external_navigation,
            "disable_back_button": self.config.disable_back_button,
            "disable_refresh": self.config.disable_refresh,
            "session_timeout_minutes": self.config.session_timeout_minutes,
            "show_exit_button": self.config.show_exit_button,
            "has_exit_password": self.config.exit_password is not None,
            "allowed_domains": self.config.allowed_domains or []
        }


# Exemplo de uso
if __name__ == "__main__":
    kiosk = KioskMode({
        "enabled": True,
        "fullscreen_lock": True,
        "disable_external_navigation": True,
        "session_timeout_minutes": 30,
        "show_exit_button": True,
        "exit_password": "1234"
    })
    
    print("Kiosk Mode initialized")
    print(f"Enabled: {kiosk.is_enabled()}")
    
    # Iniciar sessão
    result = kiosk.start_session()
    print(f"Session started: {result}")
    
    # Verificar navegação
    nav_result = kiosk.validate_navigation("https://external.com")
    print(f"Navigation allowed: {nav_result}")
    
    # Informações da sessão
    info = kiosk.get_session_info()
    print(f"Session info: {info}")
