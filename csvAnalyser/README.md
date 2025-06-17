# 🤖 Assistente de Análise de Dados Inteligente

Um assistente avançado para análise de dados CSV com **validação Pydantic**, **respostas objetivas** e **métricas de qualidade** usando Streamlit e Google Gemini AI.

## ✨ Funcionalidades Principais

### 🛡️ **Validação e Integridade**
- ✅ **Validação Pydantic** para estrutura de dados
- 🔍 **Verificação automática** de integridade
- 📊 **Controle de tipos** de dados
- 🕒 **Timestamps automáticos** de processamento
- 📝 **Logging detalhado** de erros

### 🎯 **Sistema de Respostas Objetivas**
- 📊 **Prompts estruturados** por tipo de análise
- 🎯 **Classificação automática** de perguntas
- 📈 **Métricas de qualidade** em tempo real
- ⚡ **Respostas mais rápidas** e precisas
- 📋 **Estrutura obrigatória** para consistência

### 📊 **Tipos de Análise Suportados**
- **📊 Estatística:** Médias, medianas, correlações, desvios padrão
- **📈 Tendências:** Padrões, evoluções, comportamentos temporais
- **⚖️ Comparações:** Diferenças, rankings, análises comparativas
- **📋 Geral:** Análises customizadas e exploratórias

### 💾 **Funcionalidades Avançadas**
- 📁 **Upload de múltiplos CSVs** via ZIP
- 🔄 **Processamento automático** com validação
- 📊 **Visualização interativa** dos dados
- 💾 **Exportação JSON** estruturada
- 📈 **Resumos estatísticos** automáticos

## 🚀 Instalação Rápida

### 1. **Clone o Repositório**
```bash
git clone [url-do-repositorio]
cd csvAnalyser
```

### 2. **Configure o Ambiente Virtual**
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Linux/Mac)
source venv/bin/activate
```

### 3. **Instale as Dependências**
```bash
pip install -r requirements.txt
```

### 4. **Configure a API do Google**
Crie um arquivo `.env` na raiz do projeto:
```env
GOOGLE_API_KEY=sua_chave_api_aqui
```

**Para obter a chave API:**
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova chave de API
3. Copie e cole no arquivo `.env`

### 5. **Execute o App**
```bash
streamlit run app.py
```

## 🎯 Como Usar

### **1. Upload de Dados**
- Faça upload de um arquivo ZIP contendo seus CSVs
- O sistema processa automaticamente com validação
- Visualize estatísticas de integridade

### **2. Análise Inteligente**
- Use o chat para fazer perguntas sobre seus dados
- O sistema classifica automaticamente o tipo de análise
- Receba respostas estruturadas e objetivas

### **3. Monitoramento de Qualidade**
- Acompanhe métricas de qualidade das respostas
- Visualize estatísticas de performance
- Monitore tipos de análise mais utilizados

## 💡 Exemplos de Perguntas Otimizadas

### 📊 **Análises Estatísticas**
```
✅ "Qual é a média de vendas por mês?"
✅ "Calcule a mediana de idade dos clientes"
✅ "Qual é o desvio padrão dos preços?"
✅ "Mostre a correlação entre vendas e marketing"
```

### 📈 **Análises de Tendências**
```
✅ "Existe alguma tendência de crescimento nas vendas?"
✅ "Como o comportamento do cliente evolui ao longo do tempo?"
✅ "Identifique padrões sazonais nos dados"
✅ "Qual a tendência de churn dos clientes?"
```

### ⚖️ **Comparações**
```
✅ "Compare o desempenho entre as regiões"
✅ "Qual é maior: vendas online vs offline?"
✅ "Diferenças entre clientes novos e recorrentes"
✅ "Compare a eficiência dos canais de marketing"
```

### ❌ **Evite Perguntas Vagas**
```
❌ "Analise os dados"
❌ "O que você acha?"
❌ "Tem algo interessante?"
❌ "Mostre um resumo"
```

## 📊 Métricas de Qualidade

O sistema calcula automaticamente:

- **Score de Qualidade (0-100):** Baseado em números e especificidade
- **Números Encontrados:** Quantidade de valores numéricos na resposta
- **Especificidade:** Uso de termos técnicos apropriados
- **Tipo de Análise:** Classificação automática da pergunta

## 🛡️ Validações Implementadas

### **Modelos Pydantic**
- `DadosCSV`: Validação de estrutura de dados CSV
- `AnaliseDados`: Estruturação de respostas da IA
- `DadosProcessados`: Validação de conjunto de arquivos

### **Verificações Automáticas**
- ✅ Consistência no número de registros
- ✅ Validação de tipos de dados
- ✅ Verificação de integridade
- ✅ Controle de timestamps
- ✅ Logging de erros

## 📁 Formato dos Dados

### **Requisitos**
- ✅ Arquivos em formato CSV
- ✅ Compactados em arquivo ZIP
- ✅ Sem limite de arquivos CSV
- ✅ Limite automático de 1000 registros por arquivo (performance)

### **Estrutura Recomendada**
```
dados.zip
├── vendas.csv
├── clientes.csv
├── produtos.csv
└── marketing.csv
```

## 🔒 Segurança e Privacidade

- 🔐 **Processamento local** dos dados
- 🌐 **Apenas consultas** enviadas para API externa
- 🗑️ **Sem armazenamento** permanente de dados
- 🔍 **Validação local** antes do envio
- 📝 **Logs locais** para auditoria

## 📈 Performance

### **Otimizações Implementadas**
- ⚡ **Limitação automática** a 1000 registros por arquivo
- 🔄 **Processamento assíncrono** de múltiplos arquivos
- 📊 **Cache inteligente** de análises
- 🎯 **Prompts otimizados** para respostas rápidas

### **Métricas Típicas**
- 📁 **Upload:** 2-5 segundos por arquivo
- 💬 **Análise:** 3-8 segundos por pergunta
- 📊 **Validação:** < 1 segundo
- 💾 **Exportação:** 1-3 segundos

## 🛠️ Tecnologias Utilizadas

- **Frontend:** Streamlit
- **IA:** Google Gemini 2.0 Flash
- **Validação:** Pydantic
- **Dados:** Pandas
- **Logging:** Python Logging
- **Configuração:** python-dotenv

## 📞 Suporte

### **Problemas Comuns**
1. **Erro de API Key:** Verifique o arquivo `.env`
2. **Arquivo ZIP inválido:** Certifique-se de que contém CSVs
3. **Timeout:** Reduza o tamanho dos arquivos
4. **Erro de validação:** Verifique o formato dos CSVs

### **Contato**
- 📧 Abra uma issue no repositório
- 📖 Consulte a documentação do código
- 🔍 Verifique os logs de erro

## 🚀 Roadmap

### **Próximas Funcionalidades**
- 📊 **Gráficos interativos** automáticos
- 🔄 **Análises em lote** programadas
- 📱 **Interface mobile** otimizada
- 🔗 **Integração com APIs** externas
- 📈 **Dashboard** de métricas avançadas

---

**⭐ Se este projeto te ajudou, considere dar uma estrela no repositório!** 