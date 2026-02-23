# Integração com Digital Worker Platform

## Visão Geral

O módulo `platform_connector.py` permite que o template reutilizável se conecte **opcionalmente** à plataforma Digital Worker Platform via API REST.

**Características principais:**
- ✅ Comunicação exclusiva via HTTP REST
- ✅ Autenticação via API Key
- ✅ Fallback gracioso se plataforma não estiver disponível
- ✅ Zero dependência de código da plataforma
- ✅ Sistema funciona normalmente mesmo sem conexão

---

## Instalação

### 1. Adicionar Dependência

```bash
pip install httpx
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Integração com Digital Worker Platform (opcional)
PLATFORM_ENABLED=true
PLATFORM_ENDPOINT=https://sua-plataforma.com/api
PLATFORM_API_KEY=seu_api_key_aqui
PLATFORM_TIMEOUT=30
PLATFORM_RETRY_ATTEMPTS=3
```

**Notas:**
- `PLATFORM_ENABLED=false` desativa a integração (padrão)
- Se não configurado, o sistema funciona em modo offline
- A plataforma é completamente opcional

---

## Uso

### Inicializar Conector

```python
from backend.platform_connector import PlatformConnector

# Carrega configuração de variáveis de ambiente
connector = PlatformConnector()

# Ou com configuração customizada
from backend.platform_connector import PlatformConfig

config = PlatformConfig(
    endpoint="https://api.plataforma.com",
    api_key="seu_token_aqui",
    timeout=30,
    retry_attempts=3,
    enabled=True
)
connector = PlatformConnector(config)
```

### Consultar Worker

```python
import asyncio

async def query_example():
    response = await connector.query_worker(
        query="Qual é a alíquota de IPI?",
        worker_id="tax-expert",
        context={"domain": "tax"}
    )
    
    if response.get("fallback"):
        print("Plataforma indisponível. Usando resposta offline.")
    else:
        print(f"Resposta: {response.get('response')}")

asyncio.run(query_example())
```

### Enviar Documento

```python
async def upload_example():
    response = await connector.upload_document(
        document_content="Texto da legislação...",
        document_type="text",
        metadata={
            "source": "DOU",
            "date": "2026-02-23",
            "category": "tax"
        }
    )
    
    if response.get("success"):
        document_id = response.get("id")
        print(f"Documento enviado: {document_id}")
    else:
        print("Falha ao enviar documento")

asyncio.run(upload_example())
```

### Verificar Status

```python
# Status da conexão
status = connector.get_status()  # "connected", "disconnected", "error"

# Verificar se está conectado
if connector.is_connected():
    print("✅ Conectado à plataforma")
else:
    print("❌ Plataforma indisponível")

# Status de um worker específico
worker_status = await connector.get_worker_status("tax-expert")

# Listar workers disponíveis
workers = await connector.list_workers()
```

### Fechar Conexão

```python
connector.close()
```

---

## Integração com FastAPI

### Exemplo: Endpoint que Usa Platform Connector

```python
from fastapi import FastAPI, HTTPException
from backend.platform_connector import PlatformConnector

app = FastAPI()
connector = PlatformConnector()

@app.post("/api/v1/query")
async def query_with_platform(query: str, worker_id: str = "default"):
    """
    Consulta um worker na plataforma.
    Se plataforma indisponível, retorna resposta offline.
    """
    response = await connector.query_worker(
        query=query,
        worker_id=worker_id
    )
    
    return {
        "query": query,
        "response": response.get("response"),
        "platform_available": not response.get("fallback", False)
    }

@app.post("/api/v1/documents/upload")
async def upload_with_platform(content: str, doc_type: str = "text"):
    """
    Envia documento para plataforma.
    Se plataforma indisponível, retorna erro gracioso.
    """
    response = await connector.upload_document(
        document_content=content,
        document_type=doc_type
    )
    
    if response.get("fallback"):
        raise HTTPException(
            status_code=503,
            detail="Plataforma indisponível. Tente novamente mais tarde."
        )
    
    return response

@app.get("/api/v1/platform/status")
async def platform_status():
    """Retorna status da conexão com plataforma"""
    return {
        "status": connector.get_status(),
        "connected": connector.is_connected()
    }

@app.on_event("shutdown")
async def shutdown():
    """Fecha conexão ao desligar aplicação"""
    connector.close()
```

---

## Tratamento de Erros

O conector implementa fallback automático em caso de:

### 1. Plataforma Indisponível
```python
response = await connector.query_worker("pergunta")
if response.get("fallback"):
    # Plataforma não está disponível
    # Use resposta offline ou cache local
    pass
```

### 2. Autenticação Falha
```python
# Se API Key for inválida, retorna fallback automaticamente
response = await connector.query_worker("pergunta")
# Status 401 é tratado internamente
```

### 3. Timeout
```python
# Retry automático com número configurável de tentativas
# Padrão: 3 tentativas
# Configurável via PLATFORM_RETRY_ATTEMPTS
```

### 4. Documento Muito Grande
```python
response = await connector.upload_document(huge_content)
if response.get("error") == "document_too_large":
    # Dividir documento em partes menores
    pass
```

---

## Estrutura de Respostas

### Query Worker - Sucesso
```json
{
    "success": true,
    "query": "Qual é a alíquota de IPI?",
    "response": "A alíquota de IPI é de 25%...",
    "worker_id": "tax-expert",
    "timestamp": "2026-02-23T15:46:00Z"
}
```

### Query Worker - Fallback
```json
{
    "success": false,
    "query": "Qual é a alíquota de IPI?",
    "response": "Plataforma indisponível. Usando modo offline.",
    "fallback": true,
    "timestamp": "2026-02-23T15:46:00Z"
}
```

### Upload Document - Sucesso
```json
{
    "success": true,
    "id": "doc_abc123xyz",
    "type": "text",
    "size": 1024,
    "timestamp": "2026-02-23T15:46:00Z"
}
```

### Upload Document - Fallback
```json
{
    "success": false,
    "error": "platform_unavailable",
    "message": "Plataforma indisponível. Documento não foi enviado.",
    "fallback": true,
    "timestamp": "2026-02-23T15:46:00Z"
}
```

---

## Endpoints da Plataforma

O conector espera que a plataforma implemente os seguintes endpoints:

### Health Check
```
GET /api/v1/health
Response: 200 OK
```

### Query Worker
```
POST /api/v1/workers/query
Request:
{
    "query": "string",
    "worker_id": "string",
    "context": {},
    "timestamp": "ISO-8601"
}
Response:
{
    "success": true,
    "response": "string",
    "worker_id": "string"
}
```

### Upload Document
```
POST /api/v1/documents/upload
Request:
{
    "content": "string",
    "type": "string",
    "metadata": {},
    "timestamp": "ISO-8601"
}
Response:
{
    "success": true,
    "id": "string",
    "type": "string",
    "size": number
}
```

### Get Worker Status
```
GET /api/v1/workers/{worker_id}/status
Response:
{
    "status": "active|inactive|error",
    "worker_id": "string",
    "last_heartbeat": "ISO-8601"
}
```

### List Workers
```
GET /api/v1/workers
Response:
{
    "workers": [
        {
            "id": "string",
            "name": "string",
            "status": "active"
        }
    ]
}
```

---

## Modo Offline

Se a plataforma não estiver configurada ou indisponível:

1. ✅ O template continua funcionando normalmente
2. ✅ Respostas offline são retornadas automaticamente
3. ✅ Nenhum erro é lançado
4. ✅ Sistema é resiliente

```python
# Mesmo sem plataforma, o sistema funciona
connector = PlatformConnector()

# Retorna fallback automaticamente
response = await connector.query_worker("pergunta")
print(response)
# {
#     "success": false,
#     "fallback": true,
#     "response": "Plataforma indisponível..."
# }
```

---

## Logging

O conector registra eventos importantes:

```
✅ Conectado à plataforma Digital Worker
❌ Plataforma indisponível (ConnectError)
❌ Timeout ao conectar à plataforma
✅ Query ao worker bem-sucedida: tax-expert
❌ Autenticação falhou (API Key inválida)
❌ Worker não encontrado: unknown-worker
```

Ative logs detalhados:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("platform_connector")
```

---

## Testes

### Teste Sem Plataforma
```python
# Sem configurar PLATFORM_ENDPOINT
connector = PlatformConnector()
response = await connector.query_worker("teste")
assert response.get("fallback") == True
```

### Teste Com Mock
```python
from unittest.mock import patch, AsyncMock

@patch("httpx.Client.post")
async def test_query_worker(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": True,
        "response": "Resposta de teste"
    }
    
    connector = PlatformConnector()
    response = await connector.query_worker("teste")
    assert response["success"] == True
```

---

## Troubleshooting

### Problema: "Plataforma indisponível"
**Solução:**
1. Verifique se `PLATFORM_ENABLED=true`
2. Verifique se `PLATFORM_ENDPOINT` está correto
3. Verifique conectividade: `curl https://seu-endpoint/api/v1/health`

### Problema: "Autenticação falhou"
**Solução:**
1. Verifique se `PLATFORM_API_KEY` está correto
2. Verifique se token não expirou
3. Gere novo token na plataforma

### Problema: Timeout
**Solução:**
1. Aumentar `PLATFORM_TIMEOUT` (padrão: 30s)
2. Aumentar `PLATFORM_RETRY_ATTEMPTS` (padrão: 3)
3. Verificar latência de rede

---

## Segurança

### Boas Práticas

1. **Nunca commitar API Key**
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Usar variáveis de ambiente**
   ```python
   api_key = os.getenv("PLATFORM_API_KEY")
   ```

3. **Validar certificados SSL**
   ```python
   # Padrão: validação habilitada
   # Para desabilitar (apenas desenvolvimento):
   config = PlatformConfig(
       endpoint="https://...",
       api_key="...",
       verify_ssl=False  # ⚠️ Apenas para testes
   )
   ```

4. **Usar HTTPS**
   ```python
   # Sempre usar HTTPS em produção
   endpoint="https://api.plataforma.com"  # ✅
   endpoint="http://api.plataforma.com"   # ❌
   ```

---

## Performance

### Otimizações

1. **Connection Pooling**
   - Cliente HTTP reutiliza conexões
   - Reduz latência em múltiplas requisições

2. **Retry Automático**
   - Falhas temporárias são retentadas
   - Melhora confiabilidade

3. **Timeout Configurável**
   - Padrão: 30 segundos
   - Ajustável via `PLATFORM_TIMEOUT`

### Métricas

```python
# Latência esperada
- Query: 200-500ms
- Upload: 500-2000ms
- Health Check: 100-300ms
```

---

## Roadmap

Futuras melhorias:

- [ ] Cache de respostas
- [ ] Circuit breaker automático
- [ ] Métricas de performance
- [ ] Suporte a webhooks
- [ ] Integração com observabilidade (Prometheus)
- [ ] Suporte a streaming de respostas

---

## Suporte

Para dúvidas ou problemas:

1. Verifique logs: `logging.basicConfig(level=logging.DEBUG)`
2. Teste conectividade: `curl -H "Authorization: Bearer $TOKEN" $ENDPOINT/api/v1/health`
3. Valide configuração: `echo $PLATFORM_ENDPOINT && echo $PLATFORM_API_KEY`

---

**Última atualização:** 2026-02-23
**Versão:** 1.0.0
