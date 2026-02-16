# 📚 Base de Conhecimento

Este diretório contém a base de conhecimento do seu agente conversacional.

## Formato de Dados

O arquivo `sample_questions.json` contém pares de perguntas e respostas:

```json
[
  {
    "question": "Pergunta do usuário",
    "answer": "Resposta do agente"
  },
  {
    "question": "Outra pergunta",
    "answer": "Outra resposta"
  }
]
```

## Como Customizar

### 1. Editar `sample_questions.json`

Substitua o conteúdo com suas próprias perguntas e respostas:

```json
[
  {
    "question": "Qual é a política de férias?",
    "answer": "Todos os funcionários têm direito a 30 dias de férias por ano..."
  },
  {
    "question": "Como solicitar um dia de folga?",
    "answer": "Você pode solicitar através do sistema RH..."
  }
]
```

### 2. Gerar Embeddings FAISS

Após atualizar os dados, gere os embeddings:

```bash
cd backend
python orchestrator/generate_embeddings.py
cd ..
```

Isso criará um índice FAISS otimizado para busca semântica.

### 3. Deploy

Faça deploy do backend com os novos dados:

```bash
cd backend
bash deploy/deploy_orchestrator.sh
cd ..
```

## Dicas

- **Qualidade:** Perguntas e respostas claras e bem estruturadas resultam em melhores respostas
- **Quantidade:** Comece com 50-100 Q&As e expanda conforme necessário
- **Atualização:** Atualize regularmente a base de conhecimento com novas informações
- **Validação:** Teste as respostas do agente e refine conforme necessário

## Exemplos de Domínios

### RH
```json
[
  {"question": "Qual é a política de férias?", "answer": "..."},
  {"question": "Como solicitar licença maternidade?", "answer": "..."}
]
```

### Jurídico
```json
[
  {"question": "Qual é a lei de proteção de dados?", "answer": "..."},
  {"question": "Como fazer uma denúncia?", "answer": "..."}
]
```

### Suporte Técnico
```json
[
  {"question": "Como resetar minha senha?", "answer": "..."},
  {"question": "O sistema está fora do ar?", "answer": "..."}
]
```

## Próximos Passos

1. Edite `sample_questions.json` com seus dados
2. Execute `generate_embeddings.py`
3. Faça deploy do backend
4. Teste seu agente!
