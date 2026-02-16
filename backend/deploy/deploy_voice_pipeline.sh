#!/bin/bash

# Script para fazer deploy do Voice Pipeline no Modal

set -e

echo "🚀 Iniciando deploy do Voice Pipeline..."

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
echo "📦 Fazendo deploy do Voice Pipeline..."
cd ../voice_pipeline
modal deploy modal_voice_pipeline.py

echo "✅ Deploy do Voice Pipeline concluído!"
echo ""
echo "📝 Próximas etapas:"
echo "1. Copie a URL do Voice Pipeline"
echo "2. Configure VITE_VOICE_API_URL no frontend"
echo "3. Faça deploy do frontend no Netlify"
