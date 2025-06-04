import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscador de Palavras", layout="wide")
st.title("🔍 Buscador de Palavras - Planilhas Automáticas")

# Arquivos Excel do repositório
planilhas_disponiveis = {
    "Chamados Abertos Fechados": "Chamados Abertos Fechados.xlsx",
    "Circuitos e Designações": "Circuitos e Designações.xlsx",
    "Operadoras": "Operadoras.xlsx"
}

# Seleção do arquivo
arquivo_selecionado = st.selectbox("📁 Escolha o arquivo:", list(planilhas_disponiveis.keys()))
caminho_arquivo = planilhas_disponiveis[arquivo_selecionado]

if os.path.exists(caminho_arquivo):
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name=None)

        # Seleção da aba
        sheet_names = list(df.keys())
        selected_sheet = st.selectbox("📑 Escolha a aba da planilha:", sheet_names)
        data = df[selected_sheet]

        st.subheader("📄 Visualização da Planilha")
        st.dataframe(data)

        termo = st.text_input("🔎 Digite o termo a buscar:")

        if termo:
            resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo, case=False, na=False), axis=1)]
            st.subheader("📌 Resultados da Busca")
            if not resultado.empty:
                st.dataframe(resultado)
            else:
                st.warning("Nenhum resultado encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
else:
    st.error(f"Arquivo '{caminho_arquivo}' não encontrado.")
