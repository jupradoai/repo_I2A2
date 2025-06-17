import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import pandas as pd
from zipfile import ZipFile
import io
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos Pydantic para validação de dados
class DadosCSV(BaseModel):
    """Modelo para validação de dados CSV"""
    nome_arquivo: str
    registros: List[Dict[str, Any]]
    total_registros: int
    colunas: List[str]
    tipos_dados: Dict[str, str]
    timestamp_processamento: datetime = Field(default_factory=datetime.now)
    
    @validator('registros')
    def validar_registros(cls, v):
        if not v:
            raise ValueError('Lista de registros não pode estar vazia')
        return v
    
    @validator('total_registros')
    def validar_total_registros(cls, v, values):
        if 'registros' in values and v != len(values['registros']):
            raise ValueError('Total de registros não corresponde ao número real de registros')
        return v

class AnaliseDados(BaseModel):
    """Modelo para estruturação da análise de dados"""
    pergunta_usuario: str
    interpretacao: str
    dados_analisados: List[str]
    calculos_realizados: List[str]
    resultado: str
    confianca: float = Field(ge=0.0, le=1.0)
    timestamp_analise: datetime = Field(default_factory=datetime.now)
    
    @validator('confianca')
    def validar_confianca(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confiança deve estar entre 0.0 e 1.0')
        return v

class DadosProcessados(BaseModel):
    """Modelo para validação dos dados processados"""
    arquivos: Dict[str, DadosCSV]
    total_arquivos: int
    timestamp_processamento: datetime = Field(default_factory=datetime.now)
    
    @validator('total_arquivos')
    def validar_total_arquivos(cls, v, values):
        if 'arquivos' in values and v != len(values['arquivos']):
            raise ValueError('Total de arquivos não corresponde ao número real de arquivos')
        return v

# Carregar variáveis de ambiente
load_dotenv()

# Configurar o Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar o modelo
model = genai.GenerativeModel('gemini-2.0-flash')

# Sistema de prompts estruturados para respostas mais objetivas
class SistemaPrompts:
    """Sistema de prompts estruturados para análises mais objetivas"""
    
    @staticmethod
    def prompt_analise_estatistica():
        return """
        Você é um analista de dados especializado. Responda de forma OBJETIVA e PRECISA.
        
        ESTRUTURA OBRIGATÓRIA da resposta:
        
        ## 📊 ANÁLISE ESTATÍSTICA
        
        **Pergunta:** [pergunta do usuário]
        
        **Dados Analisados:** [arquivos e registros utilizados]
        
        **Métricas Encontradas:**
        - [métrica 1]: [valor numérico]
        - [métrica 2]: [valor numérico]
        
        **Conclusão:** [resposta direta e objetiva em 1-2 frases]
        
        **Confiança:** [0-100%] - [justificativa breve]
        
        REGRAS:
        - Use APENAS dados fornecidos
        - Seja CONCISO e DIRETO
        - Evite linguagem vaga
        - Sempre forneça valores numéricos quando possível
        - Máximo 3 parágrafos
        """
    
    @staticmethod
    def prompt_analise_tendencia():
        return """
        Você é um analista de tendências. Identifique padrões de forma OBJETIVA.
        
        ESTRUTURA OBRIGATÓRIA:
        
        ## 📈 ANÁLISE DE TENDÊNCIAS
        
        **Padrão Identificado:** [descrição clara do padrão]
        
        **Evidências:**
        - [evidência 1 com dados]
        - [evidência 2 com dados]
        
        **Força da Tendência:** [Forte/Média/Fraca] - [justificativa]
        
        **Conclusão:** [resposta direta]
        
        REGRAS:
        - Baseie-se APENAS nos dados
        - Quantifique quando possível
        - Seja específico sobre a força da tendência
        """
    
    @staticmethod
    def prompt_comparacao():
        return """
        Você é um analista comparativo. Compare dados de forma OBJETIVA.
        
        ESTRUTURA OBRIGATÓRIA:
        
        ## ⚖️ ANÁLISE COMPARATIVA
        
        **Comparação:** [o que está sendo comparado]
        
        **Diferenças Principais:**
        1. [diferença 1 com valores]
        2. [diferença 2 com valores]
        
        **Conclusão:** [qual é melhor/maior/menor e por quê]
        
        **Significância:** [Alta/Média/Baixa] - [justificativa]
        
        REGRAS:
        - Sempre forneça valores comparativos
        - Evite opiniões pessoais
        - Use dados quantitativos
        """

# Função para processar arquivos CSV dentro de um ZIP com validação Pydantic
def processar_arquivo_zip(arquivo_zip):
    """
    Processa arquivos CSV dentro de um ZIP com validação usando Pydantic
    """
    try:
        dados_arquivos = {}
        
        with ZipFile(arquivo_zip) as zip_file:
            arquivos_csv = [f for f in zip_file.namelist() if f.endswith('.csv')]
            
            if not arquivos_csv:
                raise ValueError("Nenhum arquivo CSV encontrado no ZIP")
            
            for arquivo in arquivos_csv:
                try:
                    with zip_file.open(arquivo) as csv_file:
                        df = pd.read_csv(csv_file)
                        
                        # Limitar a 1000 registros para performance
                        if len(df) > 1000:
                            df = df.sample(1000, random_state=42)
                            logger.info(f"Arquivo {arquivo} limitado a 1000 registros")
                        
                        # Criar instância validada do modelo DadosCSV
                        dados_csv = DadosCSV(
                            nome_arquivo=arquivo,
                            registros=df.to_dict(orient='records'),
                            total_registros=len(df),
                            colunas=df.columns.tolist(),
                            tipos_dados=df.dtypes.astype(str).to_dict()
                        )
                        
                        dados_arquivos[arquivo] = dados_csv
                        logger.info(f"Arquivo {arquivo} processado com sucesso: {len(df)} registros")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar arquivo {arquivo}: {str(e)}")
                    st.error(f"Erro ao processar {arquivo}: {str(e)}")
                    continue
        
        # Criar instância validada do modelo DadosProcessados
        dados_processados = DadosProcessados(
            arquivos=dados_arquivos,
            total_arquivos=len(dados_arquivos)
        )
        
        logger.info(f"Processamento concluído: {len(dados_arquivos)} arquivos processados")
        return dados_processados
        
    except Exception as e:
        logger.error(f"Erro geral no processamento: {str(e)}")
        st.error(f"Erro no processamento: {str(e)}")
        return None

# Função para gerar resposta baseada nos dados e na pergunta com validação Pydantic
def gerar_resposta(prompt, dados_contexto):
    """
    Gera resposta estruturada usando Pydantic para validação e prompts específicos para objetividade
    """
    try:
        # Preparar dados para o contexto
        dados_para_analise = {}
        for nome_arquivo, dados_csv in dados_contexto.items():
            dados_para_analise[nome_arquivo] = {
                'registros': dados_csv.registros,
                'colunas': dados_csv.colunas,
                'tipos_dados': dados_csv.tipos_dados,
                'total_registros': dados_csv.total_registros
            }
        
        # Classificar o tipo de pergunta
        tipo_pergunta = classificar_pergunta(prompt)
        
        # Selecionar prompt específico baseado no tipo de pergunta
        if tipo_pergunta == "estatistica":
            instrucao = SistemaPrompts.prompt_analise_estatistica()
        elif tipo_pergunta == "tendencia":
            instrucao = SistemaPrompts.prompt_analise_tendencia()
        elif tipo_pergunta == "comparacao":
            instrucao = SistemaPrompts.prompt_comparacao()
        else:
            instrucao = """
            Você é um analista de dados especializado. Responda de forma OBJETIVA e PRECISA.
            
            ESTRUTURA OBRIGATÓRIA:
            
            ## 📊 ANÁLISE DE DADOS
            
            **Pergunta:** [pergunta do usuário]
            
            **Dados Analisados:** [arquivos e registros utilizados]
            
            **Análise:** [resposta direta e objetiva]
            
            **Conclusão:** [resumo em 1 frase]
            
            **Confiança:** [0-100%]
            
            REGRAS:
            - Use APENAS dados fornecidos
            - Seja CONCISO e DIRETO
            - Evite linguagem vaga
            - Sempre forneça valores numéricos quando possível
            """
        
        contexto = f"{instrucao}\n\nDADOS DISPONÍVEIS: {json.dumps(dados_para_analise, ensure_ascii=False)}\n\nPERGUNTA: {prompt}"
        
        resposta = model.generate_content(contexto)
        
        # Calcular métricas de qualidade
        qualidade = calcular_qualidade_resposta(resposta.text, dados_contexto)
        
        # Tentar estruturar a resposta usando Pydantic
        try:
            analise_estruturada = AnaliseDados(
                pergunta_usuario=prompt,
                interpretacao=f"Análise {tipo_pergunta} baseada em {len(dados_contexto)} arquivo(s)",
                dados_analisados=list(dados_contexto.keys()),
                calculos_realizados=[f"Análise {tipo_pergunta}", "Validação Pydantic"],
                resultado=resposta.text,
                confianca=qualidade['score'] / 100.0
            )
            
            # Retornar resposta estruturada com métricas de qualidade
            return f"""
{analise_estruturada.resultado}

---
**📊 Métricas de Qualidade:**
- **Score:** {qualidade['score']}/100
- **Números Encontrados:** {qualidade['numeros_encontrados']}
- **Especificidade:** {qualidade['especificidade']}/6
- **Tipo de Análise:** {tipo_pergunta.title()}
- **Timestamp:** {analise_estruturada.timestamp_analise.strftime('%d/%m/%Y %H:%M:%S')}
            """
            
        except Exception as e:
            logger.warning(f"Não foi possível estruturar a resposta: {str(e)}")
            return f"""
{resposta.text}

---
**📊 Métricas de Qualidade:**
- **Score:** {qualidade['score']}/100
- **Números Encontrados:** {qualidade['numeros_encontrados']}
- **Especificidade:** {qualidade['especificidade']}/6
- **Tipo de Análise:** {tipo_pergunta.title()}
            """
            
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {str(e)}")
        return f"Erro ao processar sua pergunta: {str(e)}"

# Função para exportar dados validados em JSON
def exportar_dados_validados(dados_processados):
    """
    Exporta dados processados em formato JSON estruturado
    """
    try:
        dados_export = {
            "metadata": {
                "total_arquivos": dados_processados.total_arquivos,
                "timestamp_processamento": dados_processados.timestamp_processamento.isoformat(),
                "versao": "1.0"
            },
            "arquivos": {}
        }
        
        for nome_arquivo, dados_csv in dados_processados.arquivos.items():
            dados_export["arquivos"][nome_arquivo] = {
                "nome_arquivo": dados_csv.nome_arquivo,
                "total_registros": dados_csv.total_registros,
                "colunas": dados_csv.colunas,
                "tipos_dados": dados_csv.tipos_dados,
                "timestamp_processamento": dados_csv.timestamp_processamento.isoformat(),
                "registros": dados_csv.registros[:100]  # Limitar para exportação
            }
        
        return json.dumps(dados_export, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {str(e)}")
        return None

# Função para validar integridade dos dados
def validar_integridade_dados(dados_processados):
    """
    Valida a integridade dos dados processados
    """
    try:
        validacoes = []
        
        for nome_arquivo, dados_csv in dados_processados.arquivos.items():
            # Validar se o número de registros está correto
            if len(dados_csv.registros) != dados_csv.total_registros:
                validacoes.append(f"❌ {nome_arquivo}: Inconsistência no número de registros")
            else:
                validacoes.append(f"✅ {nome_arquivo}: {dados_csv.total_registros} registros válidos")
            
            # Validar se há colunas
            if not dados_csv.colunas:
                validacoes.append(f"❌ {nome_arquivo}: Nenhuma coluna encontrada")
            else:
                validacoes.append(f"✅ {nome_arquivo}: {len(dados_csv.colunas)} colunas")
            
            # Validar se há dados
            if not dados_csv.registros:
                validacoes.append(f"❌ {nome_arquivo}: Nenhum registro encontrado")
            else:
                validacoes.append(f"✅ {nome_arquivo}: Dados presentes")
        
        return validacoes
        
    except Exception as e:
        logger.error(f"Erro na validação: {str(e)}")
        return [f"❌ Erro na validação: {str(e)}"]

# Função para classificar o tipo de pergunta
def classificar_pergunta(prompt):
    """
    Classifica o tipo de pergunta para usar o prompt mais adequado
    """
    prompt_lower = prompt.lower()
    
    # Palavras-chave para diferentes tipos de análise
    estatisticas = ['média', 'mediana', 'moda', 'desvio', 'padrão', 'percentil', 'quartil', 'correlação']
    tendencias = ['tendência', 'padrão', 'crescimento', 'diminuição', 'evolução', 'comportamento']
    comparacoes = ['comparar', 'diferença', 'maior', 'menor', 'melhor', 'pior', 'versus', 'vs']
    
    if any(palavra in prompt_lower for palavra in estatisticas):
        return "estatistica"
    elif any(palavra in prompt_lower for palavra in tendencias):
        return "tendencia"
    elif any(palavra in prompt_lower for palavra in comparacoes):
        return "comparacao"
    else:
        return "geral"

# Função para calcular métricas de qualidade da resposta
def calcular_qualidade_resposta(resposta, dados_utilizados):
    """
    Calcula métricas de qualidade da resposta
    """
    try:
        # Contar números na resposta (indicador de precisão)
        import re
        numeros = len(re.findall(r'\d+\.?\d*', resposta))
        
        # Contar palavras específicas de dados
        palavras_dados = ['média', 'mediana', 'total', 'percentual', 'correlação', 'tendência']
        especificidade = sum(1 for palavra in palavras_dados if palavra.lower() in resposta.lower())
        
        # Calcular score de qualidade (0-100)
        score = min(100, (numeros * 10) + (especificidade * 15))
        
        return {
            'score': score,
            'numeros_encontrados': numeros,
            'especificidade': especificidade,
            'dados_utilizados': len(dados_utilizados)
        }
    except Exception as e:
        logger.error(f"Erro ao calcular qualidade: {str(e)}")
        return {'score': 50, 'numeros_encontrados': 0, 'especificidade': 0, 'dados_utilizados': 0}

# Configuração da página Streamlit
st.set_page_config(page_title="Assistente de Análise de Dados", layout="wide")
st.title("Assistente de Análise de Dados")

# Estado da sessão
if 'dados_processados' not in st.session_state:
    st.session_state.dados_processados = None
if 'historico_chat' not in st.session_state:
    st.session_state.historico_chat = []
if 'estatisticas_qualidade' not in st.session_state:
    st.session_state.estatisticas_qualidade = {
        'total_respostas': 0,
        'score_medio': 0,
        'melhor_score': 0,
        'tipos_analise': {}
    }

# Upload de arquivo ZIP
arquivo_zip = st.file_uploader("Faça upload do arquivo ZIP contendo seus arquivos CSV", type=['zip'])

if arquivo_zip is not None and st.session_state.dados_processados is None:
    with st.spinner('Processando arquivos com validação Pydantic...'):
        st.session_state.dados_processados = processar_arquivo_zip(arquivo_zip)
    
    if st.session_state.dados_processados:
        st.success(f'✅ {st.session_state.dados_processados.total_arquivos} arquivo(s) processado(s) com sucesso!')
        
        # Validação de integridade
        st.subheader("🔍 Validação de Integridade")
        validacoes = validar_integridade_dados(st.session_state.dados_processados)
        for validacao in validacoes:
            st.write(validacao)
        
        # Mostrar resumo dos arquivos processados
        st.subheader("📁 Arquivos processados")
        for arquivo, dados in st.session_state.dados_processados.arquivos.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Arquivo", arquivo)
            with col2:
                st.metric("Registros", dados.total_registros)
            with col3:
                st.metric("Colunas", len(dados.colunas))
            
            with st.expander(f"Detalhes de {arquivo}"):
                st.json({col: str(tipo) for col, tipo in dados.tipos_dados.items()})

        # Mostrar dados carregados
        with st.expander("📊 Visualizar dados carregados"):
            for nome, dados in st.session_state.dados_processados.arquivos.items():
                st.write(f"**Arquivo:** {nome}")
                st.dataframe(pd.DataFrame(dados.registros).head(10))

        # Botão de resumo estatístico
        if st.button("📈 Gerar resumo estatístico"):
            for nome, dados in st.session_state.dados_processados.arquivos.items():
                df = pd.DataFrame(dados.registros)
                st.write(f"**Resumo estatístico de {nome}**")
                st.write(df.describe(include='all'))
        
        # Exportar dados validados
        if st.button("💾 Exportar dados validados (JSON)"):
            dados_json = exportar_dados_validados(st.session_state.dados_processados)
            if dados_json:
                st.download_button(
                    label="📥 Download JSON",
                    data=dados_json,
                    file_name=f"dados_validados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.error("Erro ao exportar dados")
    else:
        st.error("❌ Erro no processamento dos arquivos")

# Área de chat
if st.session_state.dados_processados is not None:
    st.subheader("💬 Chat com o Assistente")

    # Dicas para perguntas objetivas
    with st.expander("💡 Dicas para Perguntas Mais Objetivas"):
        st.write("""
        **Para obter respostas mais precisas, tente perguntas como:**
        
        📊 **Análises Estatísticas:**
        - "Qual é a média de [coluna]?"
        - "Calcule a mediana de [coluna]"
        - "Qual é o desvio padrão de [coluna]?"
        
        📈 **Análises de Tendências:**
        - "Existe alguma tendência em [coluna]?"
        - "Como [coluna] evolui ao longo do tempo?"
        - "Identifique padrões em [coluna]"
        
        ⚖️ **Comparações:**
        - "Compare [coluna1] com [coluna2]"
        - "Qual é maior: [valor1] ou [valor2]?"
        - "Diferenças entre [grupo1] e [grupo2]"
        
        **Evite perguntas vagas como:**
        - "Analise os dados" ❌
        - "O que você acha?" ❌
        - "Tem algo interessante?" ❌
        """)

    # Mostrar estatísticas de qualidade
    if st.session_state.estatisticas_qualidade['total_respostas'] > 0:
        with st.expander("📊 Estatísticas de Qualidade das Respostas"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Respostas", st.session_state.estatisticas_qualidade['total_respostas'])
            with col2:
                st.metric("Score Médio", f"{st.session_state.estatisticas_qualidade['score_medio']:.1f}/100")
            with col3:
                st.metric("Melhor Score", f"{st.session_state.estatisticas_qualidade['melhor_score']:.1f}/100")
            with col4:
                tipos = st.session_state.estatisticas_qualidade['tipos_analise']
                if tipos:
                    tipo_mais_usado = max(tipos, key=tipos.get)
                    st.metric("Tipo Mais Usado", tipo_mais_usado.title())

    # Histórico de mensagens
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Entrada do usuário
    prompt = st.chat_input("Digite sua pergunta sobre os dados...")

    if prompt:
        st.session_state.historico_chat.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner('Analisando com validação Pydantic...'):
                resposta = gerar_resposta(prompt, st.session_state.dados_processados.arquivos)
                st.write(resposta)
                st.session_state.historico_chat.append({"role": "assistant", "content": resposta})
                
                # Atualizar estatísticas de qualidade
                try:
                    # Extrair score da resposta
                    import re
                    score_match = re.search(r'Score:\s*(\d+)/100', resposta)
                    if score_match:
                        score = int(score_match.group(1))
                        tipo_match = re.search(r'Tipo de Análise:\s*(\w+)', resposta)
                        tipo = tipo_match.group(1).lower() if tipo_match else "geral"
                        
                        # Atualizar estatísticas
                        stats = st.session_state.estatisticas_qualidade
                        stats['total_respostas'] += 1
                        stats['score_medio'] = ((stats['score_medio'] * (stats['total_respostas'] - 1)) + score) / stats['total_respostas']
                        stats['melhor_score'] = max(stats['melhor_score'], score)
                        stats['tipos_analise'][tipo] = stats['tipos_analise'].get(tipo, 0) + 1
                        
                except Exception as e:
                    logger.error(f"Erro ao atualizar estatísticas: {str(e)}")
else:
    st.info("📁 Envie um arquivo ZIP contendo arquivos CSV para iniciar a análise.")

# Sidebar
with st.sidebar:
    st.subheader("🤖 Sobre o Assistente")
    st.write("""
    Este assistente pode ajudar você a:
    - 📊 Analisar arquivos CSV com validação Pydantic
    - 🔍 Identificar padrões nos dados
    - 📈 Realizar cálculos estatísticos
    - 💬 Responder perguntas sobre os dados com IA
    - ✅ Validar integridade dos dados
    - 💾 Exportar dados estruturados
    - 🎯 Gerar respostas objetivas e precisas
    """)

    st.subheader("🛡️ Validações Implementadas")
    st.write("""
    **Pydantic Models:**
    - ✅ Validação de estrutura de dados
    - ✅ Verificação de tipos de dados
    - ✅ Controle de integridade
    - ✅ Timestamps automáticos
    - ✅ Logging de erros
    """)

    st.subheader("🎯 Sistema de Prompts Estruturados")
    st.write("""
    **Tipos de Análise:**
    - 📊 **Estatística:** Médias, medianas, correlações
    - 📈 **Tendências:** Padrões e evoluções
    - ⚖️ **Comparações:** Diferenças e rankings
    - 📋 **Geral:** Análises customizadas
    
    **Benefícios:**
    - 🎯 Respostas mais objetivas
    - 📊 Métricas de qualidade
    - ⚡ Respostas mais rápidas
    - 🔍 Maior precisão
    """)

    if st.session_state.dados_processados is not None:
        st.subheader("📊 Estatísticas")
        st.metric("Arquivos", st.session_state.dados_processados.total_arquivos)
        st.metric("Total de Registros", sum(d.total_registros for d in st.session_state.dados_processados.arquivos.values()))
        
        if st.button("🗑️ Limpar Dados"):
            st.session_state.dados_processados = None
            st.session_state.historico_chat = []
            st.session_state.estatisticas_qualidade = {
                'total_respostas': 0,
                'score_medio': 0,
                'melhor_score': 0,
                'tipos_analise': {}
            }
            st.rerun()
