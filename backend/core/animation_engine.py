"""
ATTI Avatar Animation Engine v2.0
Sistema de animações idle com estados configuráveis e micro-movimentos programáveis.
Preparado para integração com engine 3D futura.
"""

import time
from enum import Enum
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


class AvatarState(Enum):
    """Estados do avatar durante a sessão"""
    ACTIVE = "active"          # Interagindo com usuário
    THINKING = "thinking"      # Processando resposta
    IDLE = "idle"              # Aguardando interação
    LISTENING = "listening"    # Escutando áudio
    SPEAKING = "speaking"      # Reproduzindo áudio


@dataclass
class AnimationFrame:
    """Definição de um frame de animação"""
    name: str
    duration_ms: int
    properties: Dict = field(default_factory=dict)
    easing: str = "linear"  # linear, ease-in, ease-out, ease-in-out


@dataclass
class IdleAnimation:
    """Definição de uma animação idle"""
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    priority: int = 0


class AnimationEngine:
    """
    Motor de animações para Avatar ATTI v2.0
    
    Características:
    - Estados configuráveis (active, thinking, idle, listening, speaking)
    - Temporizador adaptativo
    - Micro-movimentos programáveis
    - Hook para engine 3D
    - Suporte a múltiplas animações simultâneas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor de animações
        
        Args:
            config: Dicionário com configurações:
                - idle_timeout_ms: Tempo antes de entrar em idle (padrão: 5000)
                - animation_speed: Multiplicador de velocidade (padrão: 1.0)
                - enable_3d_hooks: Ativar hooks para engine 3D (padrão: False)
        """
        self.config = config or {}
        self.idle_timeout_ms = self.config.get("idle_timeout_ms", 5000)
        self.animation_speed = self.config.get("animation_speed", 1.0)
        self.enable_3d_hooks = self.config.get("enable_3d_hooks", False)
        
        self.current_state = AvatarState.IDLE
        self.previous_state = AvatarState.IDLE
        self.state_changed_at = datetime.now()
        
        self.animations: Dict[str, IdleAnimation] = {}
        self.current_animation: Optional[IdleAnimation] = None
        self.animation_frame_index = 0
        self.animation_start_time = 0
        
        self.is_playing = False
        self.last_activity_time = time.time()
        
        self._register_default_animations()
    
    def _register_default_animations(self):
        """Registra animações padrão do sistema"""
        
        # Animação de respiração (idle)
        breathing = IdleAnimation(
            name="breathing",
            frames=[
                AnimationFrame("breathe_in", 1000, {"scale": 1.05, "opacity": 1.0}),
                AnimationFrame("breathe_hold", 500, {"scale": 1.05, "opacity": 1.0}),
                AnimationFrame("breathe_out", 1000, {"scale": 0.95, "opacity": 1.0}),
                AnimationFrame("breathe_hold2", 500, {"scale": 0.95, "opacity": 1.0}),
            ],
            loop=True,
            priority=0
        )
        self.register_animation(breathing)
        
        # Animação de pensamento
        thinking = IdleAnimation(
            name="thinking",
            frames=[
                AnimationFrame("think_glow_1", 500, {"glow": 0.3}),
                AnimationFrame("think_glow_2", 500, {"glow": 0.6}),
                AnimationFrame("think_glow_1", 500, {"glow": 0.3}),
            ],
            loop=True,
            priority=1
        )
        self.register_animation(thinking)
        
        # Animação de escuta
        listening = IdleAnimation(
            name="listening",
            frames=[
                AnimationFrame("listen_pulse_1", 300, {"pulse": 0.5}),
                AnimationFrame("listen_pulse_2", 300, {"pulse": 1.0}),
                AnimationFrame("listen_pulse_1", 300, {"pulse": 0.5}),
            ],
            loop=True,
            priority=2
        )
        self.register_animation(listening)
    
    def register_animation(self, animation: IdleAnimation) -> None:
        """Registra uma nova animação no sistema"""
        self.animations[animation.name] = animation
    
    def set_state(self, new_state: AvatarState) -> None:
        """
        Altera o estado do avatar
        
        Args:
            new_state: Novo estado (AvatarState)
        """
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_changed_at = datetime.now()
            self.last_activity_time = time.time()
            
            # Trigger hook para engine 3D
            if self.enable_3d_hooks:
                self._trigger_3d_hook("state_changed", {
                    "previous_state": self.previous_state.value,
                    "new_state": new_state.value
                })
    
    def get_current_state(self) -> AvatarState:
        """Retorna o estado atual do avatar"""
        return self.current_state
    
    def get_idle_time_ms(self) -> int:
        """Retorna tempo em idle em milissegundos"""
        if self.current_state == AvatarState.IDLE:
            return int((time.time() - self.last_activity_time) * 1000)
        return 0
    
    def should_enter_idle(self) -> bool:
        """Verifica se deve entrar em estado idle"""
        idle_time = self.get_idle_time_ms()
        return idle_time > self.idle_timeout_ms and self.current_state != AvatarState.IDLE
    
    def play_animation(self, animation_name: str) -> bool:
        """
        Inicia reprodução de uma animação
        
        Args:
            animation_name: Nome da animação registrada
            
        Returns:
            True se animação foi iniciada, False se não encontrada
        """
        if animation_name not in self.animations:
            return False
        
        self.current_animation = self.animations[animation_name]
        self.animation_frame_index = 0
        self.animation_start_time = time.time()
        self.is_playing = True
        
        if self.enable_3d_hooks:
            self._trigger_3d_hook("animation_started", {"animation": animation_name})
        
        return True
    
    def stop_animation(self) -> None:
        """Para a animação atual"""
        self.is_playing = False
        self.current_animation = None
        self.animation_frame_index = 0
        
        if self.enable_3d_hooks:
            self._trigger_3d_hook("animation_stopped", {})
    
    def get_current_frame(self) -> Optional[Dict]:
        """
        Retorna o frame atual da animação em execução
        
        Returns:
            Dicionário com propriedades do frame ou None
        """
        if not self.is_playing or not self.current_animation:
            return None
        
        elapsed_ms = (time.time() - self.animation_start_time) * 1000
        total_duration = sum(f.duration_ms for f in self.current_animation.frames)
        
        # Ajustar para velocidade configurada
        adjusted_elapsed = elapsed_ms / self.animation_speed
        
        if self.current_animation.loop:
            adjusted_elapsed = adjusted_elapsed % total_duration
        elif adjusted_elapsed >= total_duration:
            self.stop_animation()
            return None
        
        # Encontrar frame atual
        current_time = 0
        for i, frame in enumerate(self.current_animation.frames):
            if current_time + frame.duration_ms > adjusted_elapsed:
                self.animation_frame_index = i
                progress = (adjusted_elapsed - current_time) / frame.duration_ms
                return {
                    "frame_name": frame.name,
                    "frame_index": i,
                    "total_frames": len(self.current_animation.frames),
                    "progress": progress,
                    "properties": frame.properties,
                    "easing": frame.easing
                }
            current_time += frame.duration_ms
        
        return None
    
    def update(self) -> Optional[Dict]:
        """
        Atualiza o estado da animação
        Deve ser chamado a cada frame (recomendado: 60 FPS)
        
        Returns:
            Dicionário com estado atual ou None
        """
        # Verificar se deve entrar em idle
        if self.should_enter_idle():
            self.set_state(AvatarState.IDLE)
        
        # Atualizar animação baseado no estado
        if self.current_state == AvatarState.IDLE and not self.is_playing:
            self.play_animation("breathing")
        elif self.current_state == AvatarState.THINKING and not self.is_playing:
            self.play_animation("thinking")
        elif self.current_state == AvatarState.LISTENING and not self.is_playing:
            self.play_animation("listening")
        
        return self.get_current_frame()
    
    def _trigger_3d_hook(self, event: str, data: Dict) -> None:
        """
        Hook para integração com engine 3D
        
        Args:
            event: Nome do evento
            data: Dados do evento
        """
        # Placeholder para integração futura com engine 3D
        # Exemplo: Babylon.js, Three.js, ou engine customizada
        pass
    
    def export_config(self) -> Dict:
        """Exporta configuração atual em JSON"""
        return {
            "idle_timeout_ms": self.idle_timeout_ms,
            "animation_speed": self.animation_speed,
            "enable_3d_hooks": self.enable_3d_hooks,
            "animations": {
                name: {
                    "frames": len(anim.frames),
                    "loop": anim.loop,
                    "priority": anim.priority
                }
                for name, anim in self.animations.items()
            }
        }
    
    def import_config(self, config_dict: Dict) -> None:
        """Importa configuração de JSON"""
        self.idle_timeout_ms = config_dict.get("idle_timeout_ms", self.idle_timeout_ms)
        self.animation_speed = config_dict.get("animation_speed", self.animation_speed)
        self.enable_3d_hooks = config_dict.get("enable_3d_hooks", self.enable_3d_hooks)


# Exemplo de uso
if __name__ == "__main__":
    engine = AnimationEngine({
        "idle_timeout_ms": 3000,
        "animation_speed": 1.0,
        "enable_3d_hooks": True
    })
    
    print("Animation Engine initialized")
    print(f"Current state: {engine.get_current_state().value}")
    print(f"Available animations: {list(engine.animations.keys())}")
    
    # Simular ciclo de animação
    engine.set_state(AvatarState.ACTIVE)
    engine.play_animation("breathing")
    
    for i in range(10):
        frame = engine.update()
        if frame:
            print(f"Frame: {frame['frame_name']} ({frame['progress']:.2%})")
        time.sleep(0.1)
