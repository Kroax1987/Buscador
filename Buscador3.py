import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscador Inteligente com Edição", layout="wide")
st.title("📂 Buscador Inteligente com Edição")

# Sessões para armazenar arquivos e dados
if 'dataframes' not in st.session_state:
    st.session_state['dataframes'] = {}
if 'filenames' not in st.session_state:
    st.session_state['filenames'] = []

# Upload de múltiplos arquivos
uploaded_files = st.file_uploader("Selecione arquivos Excel", type=["xlsx", "xls"], accept_multiple_files=True)

for file in uploaded_files:
    if file.name not in st.session_state['filenames']:
        try:
            df = pd.read_excel(file, engine='openpyxl')
            st.session_state['dataframes'][file.name] = df
            st.session_state['filenames'].append(file.name)
        except Exception as e:
            st.error(f"Erro ao carregar {file.name}: {e}")

# Campo de busca
st.subheader("🔍 Buscar Palavra-chave nos Arquivos")
palavra_chave = st.text_input("Digite a palavra-chave").strip().lower()

if st.button("Buscar") and palavra_chave:
    for nome_arquivo, df in st.session_state['dataframes'].items():
        resultados = df.applymap(lambda x: palavra_chave in str(x).lower() if pd.notnull(x) else False)
        linhas_encontradas = df[resultados.any(axis=1)]

        st.markdown(f"### 📁 {nome_arquivo}")
        if linhas_encontradas.empty:
            st.info("Nenhum resultado encontrado.")
        else:
            st.success(f"{len(linhas_encontradas)} resultado(s) encontrado(s).")
            st.dataframe(linhas_encontradas)

# Exibição das planilhas em abas
st.subheader("🗂 Planilhas Carregadas")
if st.session_state['dataframes']:
    abas = st.tabs(st.session_state['filenames'])
    for i, nome in enumerate(st.session_state['filenames']):
        with abas[i]:
            st.dataframe(st.session_state['dataframes'][nome])
