# 📊 Analisador Inteligente de CSV

Uma interface web inteligente para análise de arquivos CSV usando IA.

## ✨ Funcionalidades

- 📁 Upload de arquivos ZIP contendo CSVs
- 🤖 Análise inteligente usando IA (Google Gemini)
- 💬 Interface de chat para fazer perguntas sobre os dados
- 📊 Visualização e análise automática dos dados

## 🚀 Como Usar

1. **Instalação**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuração**
   - Crie uma conta no Google Cloud
   - Obtenha uma chave de API para o Gemini
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione: `GOOGLE_API_KEY=sua_chave_api_aqui`

3. **Executando**
   ```bash
   streamlit run app.py
   ```

4. **Usando a Interface**
   - Faça upload do arquivo ZIP contendo seus CSVs
   - Digite suas perguntas em linguagem natural
   - A IA analisará os dados e responderá suas perguntas

## 💡 Exemplos de Perguntas

- "Me mostre um resumo geral dos dados"
- "Quais são as principais tendências?"
- "Existe correlação entre as colunas?"
- "Qual a média da coluna X?"
- "Compare os dados entre os arquivos"

## 🛠️ Tecnologias

- Streamlit
- Google Gemini AI
- Pandas
- Python 