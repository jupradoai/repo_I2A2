# Analisador de CSVs com Agentes

Sistema de análise de notas fiscais utilizando uma arquitetura baseada em agentes.

## Estrutura do Projeto

```
📦 agentes-csv-analyzer
├── 📁 data
│   └── 202401_NFs.zip
├── 📁 agents
│   ├── loader_agent.py
│   ├── supplier_analysis_agent.py
│   └── item_analysis_agent.py
├── 📁 interface
│   └── app.py
├── 📁 config
│   └── .env
├── README.md
└── requirements.txt
```

## Configuração

1. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env`
- Adicione sua chave da API do Gemini

## Executando o Projeto

1. Ative o ambiente virtual
2. Execute o aplicativo Streamlit:
```bash
streamlit run interface/app.py
```

## Funcionalidades

- Upload de arquivos ZIP contendo CSVs de notas fiscais
- Análise de fornecedores (montante recebido, quantidade de notas)
- Análise de itens (volume, quantidade)
- Interface conversacional para consultas em linguagem natural 