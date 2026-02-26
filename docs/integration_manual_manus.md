# Integration Manual — ATTI Agent Template
## Knowledge Package v2.1.0

> **Para uso do time Manus / Engenharia de Execução**
> Versão do documento: 2.1.0 | Data: 2026-02-25 | Core: v2.0.0

---

## 1. Visão Geral

Este manual descreve como integrar os 9 pacotes de conhecimento vetorial
ao repositório `Marcslourenco/atti-agent-template`, garantindo
compatibilidade com o Core v2.0.0 sem quebrar nenhum componente existente.

### Segmentos incluídos

- Hospital Privado
- Concessionária de Veículos
- hoteleiro
- Shopping Center
- Prefeitura Municipal
- educacao_superior
- Clínica Odontológica
- Energia Solar Fotovoltaica
- Estudante de Medicina

### Totais

| Métrica | Valor |
|---------|-------|
| Total de pacotes | 9 |
| Total de blocos knowledge | 1425 |
| Blocos regulatórios | 447 |
| Blocos vector-ready | 1425 |
| Versão do conhecimento | 2.1.0 |
| Compatibilidade Core | v2.0.0 |

---

## 2. Onde Posicionar no Repositório

### Estrutura de destino

```
atti-agent-template/
├── knowledge_packages/          ← NOVA pasta (não existia)
│   ├── hospital_privado_v2_1_0.json
│   ├── concessionaria_veiculos_v2_1_0.json
│   ├── hotelaria_v2_1_0.json
│   ├── shopping_center_v2_1_0.json
│   ├── prefeitura_municipal_v2_1_0.json
│   ├── universidade_privada_v2_1_0.json
│   ├── clinica_odontologica_v2_1_0.json
│   ├── energia_solar_v2_1_0.json
│   └── estudante_medicina_v2_1_0.json
│
├── knowledge_manifest_v2_1_0.json   ← NOVO arquivo
├── knowledge_loader_v2_1_0.py       ← NOVO arquivo
│
├── docs/
│   ├── integration_manual_manus.md          ← NOVO
│   └── knowledge_architecture_report.md     ← NOVO
│
├── platform_connector.py     ← NÃO MODIFICAR
├── soulx/                    ← NÃO MODIFICAR
├── rule_engine/              ← NÃO MODIFICAR
├── analytics_engine/         ← NÃO MODIFICAR
└── ... (demais arquivos existentes — NÃO MODIFICAR)
```

> **REGRA CRÍTICA**: Apenas adicionar. Nunca modificar arquivos existentes.

---

## 3. Como Versionar

### Nomenclatura de versão

```
knowledge_v{MAJOR}.{MINOR}.{PATCH}
```

- **MAJOR**: Mudança arquitetural (ex: v3.0.0 = novo formato de bloco)
- **MINOR**: Adição de novos segmentos ou campos (ex: v2.1.0 → v2.2.0)
- **PATCH**: Correções em blocos existentes (ex: v2.1.0 → v2.1.1)

### Arquivos com versão no nome

Sempre incluir versão no nome do arquivo:
```
hospital_privado_v2_1_0.json     ✓
knowledge_manifest_v2_1_0.json   ✓
knowledge_loader_v2_1_0.py       ✓
```

---

## 4. Como Criar Branch knowledge-v2.1.0

```bash
# Certifique-se de estar na branch main atualizada
git checkout main
git pull origin main

# Criar branch de feature de conhecimento
git checkout -b knowledge-v2.1.0

# Adicionar todos os arquivos novos
git add knowledge_packages/
git add knowledge_manifest_v2_1_0.json
git add knowledge_loader_v2_1_0.py
git add docs/integration_manual_manus.md
git add docs/knowledge_architecture_report.md

# Commit inicial
git commit -m "feat(knowledge): add knowledge packages v2.1.0

- 9 segments: Hospital, Concessionária, Hotelaria, Shopping Center,
  Prefeitura, Universidade, Odontologia, Energia Solar, Medicina
- 1425 knowledge blocks total
- Vector-ready (FAISS/Pinecone compatible)
- Hybrid retrieval: Rule Engine + Vector Store
- Core v2.0.0 backward compatible
- Zero modification to existing files

Closes #knowledge-v2.1.0"

# Push da branch
git push origin knowledge-v2.1.0
```

---

## 5. Como Gerar Tag v2.1.0

Após aprovação do Pull Request e merge em main:

```bash
# Garantir que está na main atualizada
git checkout main
git pull origin main

# Criar tag anotada
git tag -a knowledge-v2.1.0 -m "Knowledge Package v2.1.0

Segments: 9
Total blocks: 1425
Core compatibility: v2.0.0
Date: 2026-02-25"

# Push da tag
git push origin knowledge-v2.1.0

# Verificar tag
git show knowledge-v2.1.0
```

---

## 6. Testes Recomendados

### 6.1 Teste de Integridade (obrigatório antes do merge)

```python
from knowledge_loader_v2_1_0 import KnowledgeLoader

loader = KnowledgeLoader(validate_integrity=True)
loader.load_all_packages()
stats = loader.get_statistics()

assert stats["total_segments_available"] == 9
assert stats["total_blocks_loaded"] == 1425
assert stats["vector_ready_blocks"] == 1425
print("✓ Integridade OK")
```

### 6.2 Teste de Não-Regressão (Core v2.0.0)

```python
# Verificar que componentes existentes não foram afetados
import platform_connector  # deve importar sem erro
import soulx               # deve importar sem erro
import rule_engine         # deve importar sem erro
import analytics_engine    # deve importar sem erro
print("✓ Core v2.0.0 intacto")
```

### 6.3 Teste de Queries

```python
from knowledge_loader_v2_1_0 import (
    get_blocks_by_segment,
    get_blocks_by_complexity,
    get_regulatory_blocks
)

# Testar por segmento
blocks = get_blocks_by_segment("Hospital Privado")
assert len(blocks) > 0

# Testar por complexidade
basic = get_blocks_by_complexity("basico")
assert len(basic) > 0

# Testar regulatórios
reg = get_regulatory_blocks()
assert len(reg) > 0

print("✓ Query functions OK")
```

### 6.4 Teste de Preparação Vetorial

```python
from knowledge_loader_v2_1_0 import prepare_for_vectorization

docs = prepare_for_vectorization()
assert len(docs) == 1425
for doc in docs[:5]:
    assert "id" in doc
    assert "text" in doc
    assert "metadata" in doc
    assert len(doc["text"]) > 0
print("✓ Vector preparation OK")
```

---

## 7. Estratégia Futura de Expansão

### Adicionando novos segmentos (v2.2.0+)

1. Criar arquivo `novo_segmento_v2_2_0.json` seguindo o schema existente
2. Adicionar entrada em `knowledge_manifest_v2_1_0.json` → novo `knowledge_manifest_v2_2_0.json`
3. Incrementar `total_packages` e `total_blocks` no manifest
4. Gerar SHA256 do novo arquivo
5. O loader carrega automaticamente via manifest — sem alteração de código

### Escalabilidade para 50+ segmentos

- Loader usa `lru_cache` e lazy loading — pacotes não utilizados não são carregados
- Manifest centraliza metadados — queries de descoberta sem I/O
- FAISS IndexIVFFlat recomendado para >1M blocos
- Particionamento por segmento permite índices especializados

### Integração com RAG Production

```python
# Exemplo de integração futura com FAISS
from knowledge_loader_v2_1_0 import prepare_for_vectorization
import faiss
import numpy as np

docs = prepare_for_vectorization()
texts = [d["text"] for d in docs]
ids = [d["id"] for d in docs]

# Gerar embeddings (usar OpenAI / HuggingFace)
# embeddings = embedding_model.encode(texts)
# index = faiss.IndexFlatIP(embedding_dim)
# index.add(np.array(embeddings).astype("float32"))
```

---

## 8. Checklist de Validação (pré-deploy)

```
PRÉ-MERGE
□ Branch knowledge-v2.1.0 criada a partir de main atualizada
□ Todos os 9 arquivos JSON presentes em knowledge_packages/
□ knowledge_manifest_v2_1_0.json presente e válido
□ knowledge_loader_v2_1_0.py presente e sem erros de sintaxe
□ SHA256 de todos os pacotes validados pelo loader
□ Teste de integridade passou (validate_integrity=True)
□ Teste de não-regressão passou (Core v2.0.0 intacto)
□ Teste de queries passou
□ Zero arquivos existentes modificados
□ PR revisado por pelo menos 1 engenheiro

PÓS-MERGE
□ Tag knowledge-v2.1.0 criada e pushed
□ GitHub Release criada com changelog
□ Documentação atualizada no Wiki
□ Time notificado no canal #atti-engineering
```

---

*Documento gerado automaticamente pelo Knowledge Modularization Engine v2.1.0*
*ATTI Agent Template | Core v2.0.0 | 2026-02-25*
