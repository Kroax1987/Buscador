import streamlit as st
import pandas as pd
import os

# Caminhos dos arquivos dentro da pasta data/
PATH_OPERADORAS = "data/Operadoras.xlsx"
PATH_DESIGNACOES = "data/Circuitos_e_Designacoes.xlsx"
PATH_CHAMADOS = "data/Chamados_Operadoras.xlsx"

st.set_page_config(page_title="Buscador Inteligente", layout="wide")

st.title("🔍 Buscador Inteligente de Dados Operacionais")

# Função para carregar as planilhas
@st.cache_data
def carregar_dados():
    try:
        operadores_df = pd.read_excel(PATH_OPERADORAS)
        designacoes_df = pd.read_excel(PATH_DESIGNACOES)
        chamados_df = pd.read_excel(PATH_CHAMADOS)
        return operadores_df, designacoes_df, chamados_df
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos: {e}")
        return None, None, None

# Função para buscar dados em uma planilha por palavra-chave
def buscar_palavra_chave(df, palavra):
    if df is None or df.empty:
        return pd.DataFrame()
    resultados = df[df.apply(lambda row: row.astype(str).str.contains(palavra, case=False, na=False).any(), axis=1)]
    return resultados

# Carregar dados
operadoras_df, designacoes_df, chamados_df = carregar_dados()

# Interface
palavra = st.text_input("Digite uma palavra-chave para buscar:")

if palavra:
    with st.spinner("Buscando..."):

        st.subheader("🔌 Resultado: Operadoras")
        resultado_operadoras = buscar_palavra_chave(operadoras_df, palavra)
        st.dataframe(resultado_operadoras, use_container_width=True)

        st.subheader("🧩 Resultado: Circuitos e Designações")
        resultado_designacoes = buscar_palavra_chave(designacoes_df, palavra)
        st.dataframe(resultado_designacoes, use_container_width=True)

        st.subheader("📑 Resultado: Chamados Abertos / Fechados")
        resultado_chamados = buscar_palavra_chave(chamados_df, palavra)
        st.dataframe(resultado_chamados, use_container_width=True)

        if (
            resultado_operadoras.empty and
            resultado_designacoes.empty and
            resultado_chamados.empty
        ):
            st.warning("🔎 Nenhum resultado encontrado.")
