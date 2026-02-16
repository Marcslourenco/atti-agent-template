#!/bin/bash

# Script para fazer deploy do Orquestrador no Modal

set -e

echo "🚀 Iniciando deploy do Orquestrador..."

# Verificar se Modal CLI está instalado
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI não encontrado. Instale com: pip install modal"
    exit 1
fi

# Verificar autenticação
if ! modal token show &> /dev/null; then
    echo "❌ Não autenticado no Modal. Execute: modal token new"
    exit 1
fi

# Deploy
echo "📦 Fazendo deploy do Orquestrador..."
cd ../orchestrator
modal deploy modal_orchestrator_api.py

echo "✅ Deploy do Orquestrador concluído!"
echo ""
echo "📝 Próximas etapas:"
echo "1. Copie a URL do Orquestrador"
echo "2. Configure VITE_API_BASE_URL no frontend"
echo "3. Execute: bash deploy_voice_pipeline.sh"
