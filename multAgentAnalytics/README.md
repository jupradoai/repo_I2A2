# Sistema Multiagente para Automação de VR/VA

## 🎯 Objetivo
Automatizar o processo mensal de compra de Vale Refeição (VR) e Vale Alimentação (VA), garantindo cálculo preciso baseado em múltiplas regras de negócio e validações.

## 🏗️ Arquitetura

### Sistema Multiagente
Sistema composto por 6 agentes especializados:
- **Coordenador**: Orquestra todo o processo
- **Consolidador**: Unifica as 5 bases de dados
- **Limpeza**: Trata exclusões e valida dados
- **Calculador**: Processa regras de negócio
- **Validador**: Verifica consistência final
- **Gerador**: Cria planilha de saída

### Interface Web
- **Flask**: Framework web para interface amigável
- **Socket.IO**: Atualizações em tempo real
- **Bootstrap 5**: Interface moderna e responsiva
- **Upload Drag & Drop**: Interface intuitiva para arquivos

## 📁 Estrutura do Projeto
```
multAgentAnalytics/
├── src/                    # Código fonte
│   ├── agents/            # Agentes do sistema
│   ├── models/            # Modelos de dados
│   ├── services/          # Serviços auxiliares
│   ├── utils/             # Utilitários
│   ├── templates/         # Templates HTML Flask
│   └── app.py             # Aplicação Flask principal
├── data/                  # Dados de entrada/saída
├── tests/                 # Testes automatizados
├── config/                # Configurações
├── logs/                  # Logs do sistema
└── docs/                  # Documentação
```

## 🚀 Instalação
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd multAgentAnalytics

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

## 📊 Bases de Dados Suportadas
- ATIVOS.xlsx
- FÉRIAS.xlsx
- DESLIGADOS.xlsx
- ADMISSÃO ABRIL.xlsx
- Base sindicato x valor.xlsx
- Base dias uteis.xlsx
- EXTERIOR.xlsx
- ESTÁGIO.xlsx
- APRENDIZ.xlsx
- AFASTAMENTOS.xlsx

## 🔧 Uso

### Via Linha de Comando
```bash
# Executar sistema completo
python -m src.main

# Executar agente específico
python -m src.agents.consolidador

# Executar testes
pytest tests/
```

### Via Interface Web (Recomendado)
```bash
# Executar sistema via Flask
make run-web

# Ou diretamente
python src/app.py
```

Após executar, acesse: http://localhost:5000

## 📝 Regras de Negócio
- Cálculo baseado em dias úteis por sindicato
- Exclusão de diretores, estagiários e aprendizes
- Tratamento de férias e afastamentos
- Regras de desligamento (antes/depois do dia 15)
- Custo empresa: 80%, Profissional: 20%

## 🤝 Contribuição
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença
Este projeto é de uso interno da empresa. 