"""
ATTI Analytics Engine v2.0
Sistema de análise de interações e geração automática de relatórios PDF.
Estrutura: Sumário, Interações, Insights, Métricas.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import statistics


@dataclass
class InteractionMetric:
    """Métrica de uma interação"""
    timestamp: str
    user_input: str
    avatar_response: str
    duration_ms: float
    user_satisfaction: Optional[int] = None
    interaction_type: str = "general"


@dataclass
class SessionAnalytics:
    """Análise de uma sessão"""
    session_id: str
    user_id: str
    start_time: str
    end_time: Optional[str] = None
    total_interactions: int = 0
    total_duration_seconds: float = 0.0
    average_interaction_duration_ms: float = 0.0
    interactions: List[InteractionMetric] = None
    
    def __post_init__(self):
        if self.interactions is None:
            self.interactions = []


class AnalyticsEngine:
    """
    Motor de Analytics para Avatar ATTI v2.0
    
    Características:
    - Registro de interações
    - Cálculo de métricas
    - Geração de insights
    - Exportação de relatórios PDF
    - Análise de satisfação do usuário
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor de analytics
        
        Args:
            config: Dicionário com configurações:
                - storage_dir: Diretório para armazenar analytics
                - enable_pdf_export: Gerar PDFs
        """
        self.config = config or {}
        self.storage_dir = self.config.get("storage_dir", "./analytics")
        self.enable_pdf_export = self.config.get("enable_pdf_export", True)
        
        self.current_session: Optional[SessionAnalytics] = None
        self.sessions: Dict[str, SessionAnalytics] = {}
        
        # Criar diretório
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
    
    def start_session(self, session_id: str, user_id: str) -> SessionAnalytics:
        """
        Inicia uma nova sessão de analytics
        
        Args:
            session_id: ID único da sessão
            user_id: ID do usuário
            
        Returns:
            Objeto da sessão
        """
        session = SessionAnalytics(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now().isoformat()
        )
        
        self.current_session = session
        self.sessions[session_id] = session
        
        return session
    
    def record_interaction(self, user_input: str, avatar_response: str,
                          duration_ms: float, interaction_type: str = "general",
                          user_satisfaction: Optional[int] = None) -> bool:
        """
        Registra uma interação
        
        Args:
            user_input: Entrada do usuário
            avatar_response: Resposta do avatar
            duration_ms: Duração em milissegundos
            interaction_type: Tipo de interação
            user_satisfaction: Avaliação (1-5)
            
        Returns:
            True se registrado
        """
        if not self.current_session:
            return False
        
        metric = InteractionMetric(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            avatar_response=avatar_response,
            duration_ms=duration_ms,
            interaction_type=interaction_type,
            user_satisfaction=user_satisfaction
        )
        
        self.current_session.interactions.append(metric)
        self.current_session.total_interactions += 1
        self.current_session.total_duration_seconds += duration_ms / 1000
        
        # Atualizar média
        if self.current_session.total_interactions > 0:
            self.current_session.average_interaction_duration_ms = (
                self.current_session.total_duration_seconds * 1000 /
                self.current_session.total_interactions
            )
        
        return True
    
    def end_session(self) -> Optional[SessionAnalytics]:
        """
        Encerra a sessão atual
        
        Returns:
            Sessão finalizada
        """
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now().isoformat()
        
        session = self.current_session
        self.current_session = None
        
        return session
    
    def get_session_metrics(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """
        Retorna métricas de uma sessão
        
        Args:
            session_id: ID da sessão (usa atual se None)
            
        Returns:
            Dicionário com métricas
        """
        session = None
        
        if session_id:
            session = self.sessions.get(session_id)
        else:
            session = self.current_session
        
        if not session:
            return None
        
        # Calcular métricas
        satisfactions = [
            i.user_satisfaction for i in session.interactions
            if i.user_satisfaction is not None
        ]
        
        metrics = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_interactions": session.total_interactions,
            "total_duration_seconds": session.total_duration_seconds,
            "average_interaction_duration_ms": session.average_interaction_duration_ms,
            "user_satisfaction": {
                "average": statistics.mean(satisfactions) if satisfactions else 0,
                "ratings_count": len(satisfactions),
                "distribution": self._calculate_satisfaction_distribution(satisfactions)
            },
            "interaction_types": self._count_interaction_types(session.interactions)
        }
        
        return metrics
    
    def get_insights(self, session_id: Optional[str] = None) -> Dict:
        """
        Gera insights sobre uma sessão
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dicionário com insights
        """
        metrics = self.get_session_metrics(session_id)
        if not metrics:
            return {}
        
        insights = {
            "session_duration": self._format_duration(metrics["total_duration_seconds"]),
            "interaction_count": metrics["total_interactions"],
            "average_response_time": f"{metrics['average_interaction_duration_ms']:.0f}ms",
            "user_satisfaction_score": f"{metrics['user_satisfaction']['average']:.1f}/5",
            "most_common_interaction": self._get_most_common_type(metrics["interaction_types"]),
            "engagement_level": self._calculate_engagement_level(metrics),
            "recommendations": self._generate_recommendations(metrics)
        }
        
        return insights
    
    def generate_pdf_report(self, session_id: Optional[str] = None,
                           output_path: Optional[str] = None) -> Optional[str]:
        """
        Gera relatório PDF da sessão
        
        Args:
            session_id: ID da sessão
            output_path: Caminho de saída (usa padrão se None)
            
        Returns:
            Caminho do arquivo gerado
        """
        if not self.enable_pdf_export:
            return None
        
        session = None
        if session_id:
            session = self.sessions.get(session_id)
        else:
            session = self.current_session
        
        if not session:
            return None
        
        # Preparar dados
        metrics = self.get_session_metrics(session_id)
        insights = self.get_insights(session_id)
        
        # Gerar conteúdo HTML (pode ser convertido para PDF depois)
        html_content = self._generate_html_report(session, metrics, insights)
        
        # Salvar HTML
        if not output_path:
            output_path = os.path.join(
                self.storage_dir,
                f"report_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
    
    def _generate_html_report(self, session: SessionAnalytics, metrics: Dict,
                             insights: Dict) -> str:
        """Gera conteúdo HTML do relatório"""
        
        interactions_html = "".join([
            f"""
            <tr>
                <td>{i.timestamp}</td>
                <td>{i.user_input[:50]}...</td>
                <td>{i.duration_ms:.0f}ms</td>
                <td>{i.user_satisfaction or '-'}</td>
            </tr>
            """
            for i in session.interactions
        ])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>ATTI Avatar Session Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .section {{ margin-top: 20px; padding: 10px; border-left: 4px solid #007bff; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin-right: 20px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
            </style>
        </head>
        <body>
            <h1>ATTI Avatar Session Report</h1>
            
            <div class="section">
                <h2>Session Summary</h2>
                <p><strong>Session ID:</strong> {session.session_id}</p>
                <p><strong>User ID:</strong> {session.user_id}</p>
                <p><strong>Start Time:</strong> {session.start_time}</p>
                <p><strong>End Time:</strong> {session.end_time or 'Ongoing'}</p>
            </div>
            
            <div class="section">
                <h2>Metrics</h2>
                <div class="metric">
                    <div>Total Interactions</div>
                    <div class="metric-value">{metrics['total_interactions']}</div>
                </div>
                <div class="metric">
                    <div>Session Duration</div>
                    <div class="metric-value">{insights['session_duration']}</div>
                </div>
                <div class="metric">
                    <div>Avg Response Time</div>
                    <div class="metric-value">{insights['average_response_time']}</div>
                </div>
                <div class="metric">
                    <div>User Satisfaction</div>
                    <div class="metric-value">{insights['user_satisfaction_score']}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Insights</h2>
                <p><strong>Engagement Level:</strong> {insights['engagement_level']}</p>
                <p><strong>Most Common Interaction:</strong> {insights['most_common_interaction']}</p>
                <p><strong>Recommendations:</strong></p>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in insights['recommendations'])}
                </ul>
            </div>
            
            <div class="section">
                <h2>Interaction History</h2>
                <table>
                    <tr>
                        <th>Timestamp</th>
                        <th>User Input</th>
                        <th>Duration</th>
                        <th>Satisfaction</th>
                    </tr>
                    {interactions_html}
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _calculate_satisfaction_distribution(self, satisfactions: List[int]) -> Dict:
        """Calcula distribuição de satisfação"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for s in satisfactions:
            if 1 <= s <= 5:
                distribution[s] += 1
        return distribution
    
    def _count_interaction_types(self, interactions: List[InteractionMetric]) -> Dict:
        """Conta tipos de interação"""
        types = {}
        for i in interactions:
            types[i.interaction_type] = types.get(i.interaction_type, 0) + 1
        return types
    
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def _get_most_common_type(self, types: Dict) -> str:
        """Retorna tipo de interação mais comum"""
        if not types:
            return "N/A"
        return max(types, key=types.get)
    
    def _calculate_engagement_level(self, metrics: Dict) -> str:
        """Calcula nível de engajamento"""
        interactions = metrics["total_interactions"]
        if interactions < 3:
            return "Low"
        elif interactions < 10:
            return "Medium"
        else:
            return "High"
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Gera recomendações baseadas em métricas"""
        recommendations = []
        
        if metrics["total_interactions"] < 3:
            recommendations.append("Increase user engagement with proactive suggestions")
        
        if metrics["average_interaction_duration_ms"] > 5000:
            recommendations.append("Consider optimizing response time")
        
        satisfaction = metrics["user_satisfaction"]["average"]
        if satisfaction < 3:
            recommendations.append("Review interaction quality and improve responses")
        
        if not recommendations:
            recommendations.append("Session performance is good!")
        
        return recommendations
    
    def export_analytics(self) -> Dict:
        """Exporta todos os analytics"""
        return {
            "total_sessions": len(self.sessions),
            "sessions": [
                self.get_session_metrics(sid)
                for sid in self.sessions.keys()
            ]
        }


# Exemplo de uso
if __name__ == "__main__":
    import os
    
    analytics = AnalyticsEngine({
        "storage_dir": "./analytics_test",
        "enable_pdf_export": True
    })
    
    print("Analytics Engine initialized")
    
    # Iniciar sessão
    analytics.start_session("session_001", "user_123")
    
    # Registrar interações
    analytics.record_interaction(
        "What is AI?",
        "AI is Artificial Intelligence...",
        2500,
        "question",
        5
    )
    
    analytics.record_interaction(
        "Tell me more",
        "AI involves machine learning...",
        3000,
        "question",
        4
    )
    
    # Obter métricas
    metrics = analytics.get_session_metrics()
    print(f"Metrics: {metrics}")
    
    # Obter insights
    insights = analytics.get_insights()
    print(f"Insights: {insights}")
    
    # Gerar relatório
    report_path = analytics.generate_pdf_report()
    print(f"Report generated: {report_path}")
