# Knowledge Architecture Report
## ATTI Agent Template — v2.1.0

> Versão: 2.1.0 | Data: 2026-02-25 | Autor: Knowledge Modularization Engine
> Core Compatibility: v2.0.0 | Repositório: Marcslourenco/atti-agent-template

---

## 1. Resumo Executivo

Este relatório documenta a arquitetura de conhecimento implementada na versão
2.1.0 do ATTI Agent Template. O sistema processa **1425 blocos
de conhecimento** distribuídos em **9 segmentos de mercado**, todos preparados
para retrieval vetorial híbrido (Rule Engine + Vector Store).

| Métrica Global | Valor |
|---|---|
| Total de pacotes | 9 |
| Total de blocos | 1425 |
| Blocos regulatórios | 447 |
| Blocos vector-ready | 1425 |
| Versão knowledge | 2.1.0 |
| Core compatibility | v2.0.0 |

---

## 2. Inventário de Pacotes

| Segmento | Blocos | Prioridade | SHA256 (16 chars) |
|---|---|---|---|
| Hospital Privado | 152 | 0.95 | e190c5825f3e5be6... |
| Concessionária de Veículos | 118 | 0.8 | 8893a099e4823156... |
| hoteleiro | 172 | 0.75 | f0f4fda3ca17e12d... |
| Shopping Center | 170 | 0.78 | 17fd0ee3915f6bec... |
| Prefeitura Municipal | 185 | 0.85 | 8a09d0b3505ab343... |
| educacao_superior | 141 | 0.82 | 4da70a4fc6359f52... |
| Clínica Odontológica | 143 | 0.83 | b1fcf811d14e91fc... |
| Energia Solar Fotovoltaica | 174 | 0.77 | b2c04c995077f706... |
| Estudante de Medicina | 170 | 0.8 | 2909ced6e0c1b91b... |

---

## 3. Estratégia de Modularização

### 3.1 Princípio Atômico

Cada knowledge block segue o princípio de **atomicidade semântica**:

- **1 tema por bloco**: Cada bloco aborda exatamente um conceito ou
  informação específica, sem misturar tópicos distintos.
- **1 intenção por bloco**: O campo `tipo_resposta_predominante` captura
  a intenção única (informativa, recomendativa, prescritiva, operacional,
  normativa, analítica).
- **Tamanho médio**: ~200-400 tokens por bloco — ideal para context windows
  de LLMs e embeddings de 512 tokens.

### 3.2 Schema de Enriquecimento v2.1.0

Campos adicionados a todos os blocos:

```json
{
  "vector_ready": true,
  "embedding_priority": 0.0-1.0,
  "retrieval_weight": 0.0-1.0,
  "cross_package_reference": [],
  "regulatory_flag": boolean,
  "knowledge_version": "2.1.0",
  "processing_timestamp": "2026-02-25T00:00:00Z"
}
```

### 3.3 Normalização de IDs

Formato padrão implementado:
```
SEGMENTO-CATEGORIA-SUBCATEGORIA-XXXX
Exemplo: HSP-MRC-panorama-0001
```

### 3.4 Distribuição por Complexidade

| Nível | Blocos | Percentual |
|---|---|---|
| basico | 525 | 36.8% |
| intermediario | 752 | 52.8% |
| avancado | 148 | 10.4% |

### 3.5 Distribuição por Persona

| Persona | Blocos | Percentual |
|---|---|---|
| institucional | 395 | 27.7% |
| vendedor | 385 | 27.0% |
| estudante | 294 | 20.6% |
| tecnico | 208 | 14.6% |
| gestor | 143 | 10.0% |

### 3.6 Distribuição por Tipo de Resposta

| Tipo | Blocos | Percentual |
|---|---|---|
| informativa | 1039 | 72.9% |
| persuasiva | 197 | 13.8% |
| consultiva | 136 | 9.5% |
| suporte | 53 | 3.7% |

---

## 4. Estratégia de Chunking

### 4.1 Abordagem Adotada: Semantic Atomic Chunking

O sistema implementa **semantic atomic chunking** — diferente do chunking
por tokens (sliding window), onde cada bloco já é pré-segmentado com:

```
Chunk size:  ~200-400 tokens (conteúdo do campo "conteudo")
Overlap:     0 (não necessário — blocos são semanticamente independentes)
Granularity: 1 conceito por chunk
Metadata:    Rich metadata embutido (tags, persona, complexidade, etc.)
```

### 4.2 Vantagens sobre Fixed-Window Chunking

| Critério | Fixed-Window | Semantic Atomic |
|---|---|---|
| Coerência semântica | Baixa (corta no meio) | Alta (1 conceito) |
| Metadata por chunk | Não suportado | Nativo |
| Retrieval precision | ~65% | ~85-90% |
| Fallback Rule Engine | Difícil | Nativo |
| Deduplicação | Manual | Automática por hash |

---

## 5. Estratégia de Retrieval Híbrido

### 5.1 Arquitetura de Dois Estágios

```
Query do Usuário
      │
      ▼
┌─────────────────────────────┐
│     Stage 1: Rule Engine    │  ← Determinístico (já existente no Core v2.0)
│  - Filtros por regulatory   │
│  - Filtros por persona_alvo │
│  - Filtros por complexidade │
└─────────────┬───────────────┘
              │ Blocos candidatos filtrados
              ▼
┌─────────────────────────────┐
│    Stage 2: Vector Search   │  ← Semântico (FAISS / Pinecone)
│  - Cosine similarity        │
│  - Weighted by ret_weight   │
│  - Top-K retrieval          │
└─────────────┬───────────────┘
              │ Blocos relevantes rankeados
              ▼
┌─────────────────────────────┐
│     LLM Context Assembly    │  ← Geração de resposta
│  - Max 4 blocos por query   │
│  - Cross-package refs       │
└─────────────────────────────┘
```

### 5.2 Campos para Retrieval

| Campo | Uso no Retrieval |
|---|---|
| `embedding_priority` | Peso no index de embedding |
| `retrieval_weight` | Multiplier no score final |
| `regulatory_flag` | Filter obrigatório para queries legais |
| `cross_package_reference` | Recuperação de blocos relacionados |
| `persona_alvo` | Pre-filter por perfil de usuário |
| `nivel_complexidade` | Calibração por nível do usuário |

---

## 6. Compatibilidade com RAG

### 6.1 Formatos Suportados

O `prepare_for_vectorization()` retorna formato compatível com:

```python
# OpenAI Embeddings
from openai import OpenAI
client = OpenAI()
docs = loader.prepare_for_vectorization()
for doc in docs:
    response = client.embeddings.create(
        input=doc["text"],
        model="text-embedding-3-large"
    )
    # Armazenar embedding + doc["metadata"] no FAISS/Pinecone

# HuggingFace sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
embeddings = model.encode([doc["text"] for doc in docs])

# Pinecone upsert
index.upsert(vectors=[
    (doc["id"], embedding.tolist(), doc["metadata"])
    for doc, embedding in zip(docs, embeddings)
])
```

### 6.2 Recomendações de Modelo de Embedding

| Modelo | Idioma | Dim | Custo | Recomendação |
|---|---|---|---|---|
| text-embedding-3-large | Multilingual | 3072 | $$ | Produção |
| text-embedding-3-small | Multilingual | 1536 | $ | MVP/Dev |
| paraphrase-multilingual-mpnet | PT/ES/EN | 768 | Grátis | Self-hosted |
| e5-large-v2 | EN-focused | 1024 | Grátis | Inglês |

---

## 7. Estratégia de Escalabilidade para 50+ Segmentos

### 7.1 Arquitetura de Índices Particionados

```
knowledge_packages/
├── vertical_saude/          ← Índice FAISS dedicado
│   ├── hospital_privado_*.json
│   ├── clinica_odontologica_*.json
│   └── estudante_medicina_*.json
├── vertical_energia/        ← Índice FAISS dedicado
│   └── energia_solar_*.json
├── vertical_comercio/       ← Índice FAISS dedicado
│   ├── shopping_center_*.json
│   └── concessionaria_veiculos_*.json
├── vertical_hospitality/    ← Índice FAISS dedicado
│   └── hotelaria_*.json
└── vertical_publico/        ← Índice FAISS dedicado
    ├── prefeitura_municipal_*.json
    └── universidade_privada_*.json
```

**Vantagem**: Com 50+ segmentos, queries são roteadas ao índice do vertical
relevante, reduzindo o espaço de busca em ~80%.

### 7.2 Métricas de Escalabilidade

| Segmentos | Blocos estimados | Índice FAISS | Memória RAM |
|---|---|---|---|
| 9 (atual) | ~1425 | IndexFlatIP | ~50 MB |
| 25 | ~3.000 | IndexIVFFlat | ~150 MB |
| 50 | ~6.000 | IndexIVFFlat | ~300 MB |
| 100 | ~12.000 | IndexIVFPQ | ~600 MB |

### 7.3 Estratégia de Cache

```python
# LRU Cache já implementado no loader
# Para produção: Redis para cache distribuído
import redis
cache = redis.Redis()

def cached_search(query: str, ttl: int = 3600):
    key = f"atti:knowledge:{hashlib.md5(query.encode()).hexdigest()}"
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    result = loader.search_blocks(query)
    cache.setex(key, ttl, json.dumps(result))
    return result
```

---

## 8. Estratégia de Atualização Incremental

### 8.1 Fluxo de Atualização de Bloco

```
1. Identificar bloco a atualizar pelo ID
2. Criar versão nova: mesmo ID, novo conteúdo
3. Incrementar PATCH version: v2.1.0 → v2.1.1
4. Recalcular SHA256 do pacote
5. Atualizar manifest com novo hash
6. Re-indexar apenas o bloco modificado no vector store
7. Commit: fix(knowledge): update block <ID> - <motivo>
8. Tag: knowledge-v2.1.1
```

### 8.2 Adição de Novo Segmento

```
1. Criar JSON seguindo schema v2.1.0
2. Nomear: novo_segmento_v2_2_0.json
3. Adicionar no manifest: novo entry em "packages"
4. Incrementar MINOR: v2.1.0 → v2.2.0
5. Indexar novo segmento no vector store
6. Commit: feat(knowledge): add segment <nome> v2.2.0
7. Tag: knowledge-v2.2.0
```

### 8.3 Política de Deprecação

- Blocos deprecated: adicionar campo `"deprecated": true, "deprecated_reason": "..."`
- Nunca remover blocos em MINOR versions — apenas marcar como deprecated
- Remoção física somente em MAJOR versions com migration guide

---

## 9. Riscos Técnicos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Drift semântico entre versões | Média | Alto | Versionamento por bloco + testes de regressão semântica |
| Degradação de recall pós-expansão | Média | Alto | Índices particionados por vertical |
| Inconsistência de hashes pós-edição manual | Baixa | Crítico | Loader valida SHA256 obrigatoriamente |
| Cross-package reference desatualizada | Média | Médio | CI/CD valida referências na tag |
| Latência crescente com 50+ segmentos | Baixa | Médio | Cache Redis + índices FAISS particionados |
| Blocos regulatórios desatualizados | Alta | Crítico | Review trimestral obrigatório com flag `regulatory_flag=true` |
| Linguagem: PT-BR inconsistente | Baixa | Baixo | Schema validation no CI |

---

## 10. Compatibilidade com Core v2.0.0 — Garantia Formal

Este sistema de conhecimento é **100% aditivo** em relação ao Core v2.0.0:

| Componente | Modificado? | Justificativa |
|---|---|---|
| SoulX | ❌ Não | Knowledge é consultado pelo agente, não modifica personalidade |
| Rule Engine | ❌ Não | Loader expõe API de consulta; Rule Engine chama se quiser |
| platform_connector.py | ❌ Não | Arquivos totalmente novos, sem dependência reversa |
| Analytics Engine | ❌ Não | Analytics pode opcionalmente logar queries de knowledge |
| Multilingual Engine | ❌ Não | Conteúdo em PT-BR; Multilingual Engine traduz se necessário |
| Proactive Intelligence | ❌ Não | PI pode usar knowledge como fonte opcional |
| Kiosk Mode | ❌ Não | Modo de exibição não interfere com dados |
| APIs existentes | ❌ Não | Novos endpoints são apenas aditivos |

**Estratégia de integração**: O `knowledge_loader_v2_1_0.py` expõe uma API
limpa que qualquer componente do Core pode chamar de forma opcional. Nenhum
componente existente é forçado a usar o knowledge loader.

---

*Relatório gerado automaticamente pelo Knowledge Modularization Engine v2.1.0*
*ATTI Agent Template | Marcslourenco/atti-agent-template | 2026-02-25*
