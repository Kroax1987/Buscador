import streamlit as st
import pandas as pd
import os

# Caminhos dos arquivos
PATH_OPERADORAS = "Operadoras.xlsx"
PATH_DESIGNACOES = "Circuitos e Designações.xlsx"
PATH_CHAMADOS = "Chamados Abertos Fechados.xlsx"

# Configuração da página
st.set_page_config(page_title="Buscador Inteligente", layout="wide")
st.title("🔍 Buscador Inteligente de Dados Operacionais")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    try:
        operadoras_df = pd.read_excel(PATH_OPERADORAS)
        designacoes_df = pd.read_excel(PATH_DESIGNACOES)
        chamados_df = pd.read_excel(PATH_CHAMADOS)
        return operadoras_df, designacoes_df, chamados_df
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos: {e}")
        return None, None, None

# Função de busca dinâmica
def buscar_palavra(df, palavra):
    if palavra:
        resultados = df[df.apply(lambda row: row.astype(str).str.contains(palavra, case=False, na=False).any(), axis=1)]
        return resultados.head(3)  # Mostra no máximo 3 resultados
    return pd.DataFrame()

# Carrega os dados
operadoras_df, designacoes_df, chamados_df = carregar_dados()

# Input da palavra-chave
palavra = st.text_input("Digite uma palavra-chave para buscar:")

if palavra and all([operadoras_df is not None, designacoes_df is not None, chamados_df is not None]):
    with st.expander("🔌 Resultados - Operadoras", expanded=True):
        resultados_operadoras = buscar_palavra(operadoras_df, palavra)
        if not resultados_operadoras.empty:
            st.dataframe(resultados_operadoras)
        else:
            st.info("Nenhum resultado encontrado em Operadoras.")

    with st.expander("📡 Resultados - Circuitos e Designações", expanded=True):
        resultados_designacoes = buscar_palavra(designacoes_df, palavra)
        if not resultados_designacoes.empty:
            st.dataframe(resultados_designacoes)
        else:
            st.info("Nenhum resultado encontrado em Circuitos e Designações.")

    with st.expander("📁 Resultados - Chamados", expanded=True):
        resultados_chamados = buscar_palavra(chamados_df, palavra)
        if not resultados_chamados.empty:
            st.dataframe(resultados_chamados)
        else:
            st.info("Nenhum resultado encontrado em Chamados.")
