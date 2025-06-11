# 📊 Assistente de Análise de Dados

Este é um assistente inteligente para análise de dados CSV usando Streamlit e Google Gemini AI.

## 🚀 Funcionalidades

- Upload de arquivos CSV via arquivo ZIP
- Conversão automática para JSON
- Interface de chat interativa
- Análise inteligente dos dados
- Respostas contextualizadas às suas perguntas

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Chave API do Google Gemini

## 🛠️ Instalação

1. Clone este repositório:
```bash
git clone [url-do-repositorio]
cd [nome-do-repositorio]
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure sua chave API:
- Crie um arquivo `.env` na raiz do projeto
- Adicione sua chave API do Google:
```
GOOGLE_API_KEY=sua_chave_api_aqui
```

## 🚀 Como usar

1. Execute o aplicativo:
```bash
streamlit run app.py
```

2. Acesse o aplicativo no navegador (geralmente em http://localhost:8501)

3. Faça upload de um arquivo ZIP contendo seus arquivos CSV

4. Comece a fazer perguntas sobre seus dados!

## 📝 Formato dos Dados

- Os arquivos devem estar em formato CSV
- Devem estar compactados em um arquivo ZIP
- Não há limite para o número de arquivos CSV

## 🤖 Exemplos de Perguntas

- "Qual é a média de idade dos clientes?"
- "Mostre um resumo dos dados de vendas"
- "Quais são os produtos com estoque baixo?"
- "Qual foi o total de vendas no último mês?"

## 🔒 Segurança

- Seus dados são processados localmente
- Apenas as consultas são enviadas para a API do Gemini
- Não armazenamos nenhuma informação permanentemente

## 📫 Suporte

Para dúvidas ou problemas, abra uma issue no repositório. 