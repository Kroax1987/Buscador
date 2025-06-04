# buscador_app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador de Palavras", layout="wide")

st.title("🔍 Buscador em Planilha Excel")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📤 Envie sua planilha Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Leitura da planilha
        df = pd.read_excel(uploaded_file, sheet_name=None)

        # Exibir nomes das planilhas
        sheet_names = list(df.keys())
        selected_sheet = st.selectbox("Escolha a planilha:", sheet_names)
        data = df[selected_sheet]

        # Exibir a planilha
        st.subheader("📄 Visualização da Planilha")
        st.dataframe(data)

        # Campo de busca
        termo = st.text_input("🔎 Digite o termo a buscar (sensível à caixa):")

        if termo:
            # Busca (filtra linhas que contêm o termo em qualquer célula)
            resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo).any(), axis=1)]

            st.subheader("📌 Resultados da Busca")
            if not resultado.empty:
                st.dataframe(resultado)
            else:
                st.warning("Nenhum resultado encontrado para o termo buscado.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
else:
    st.info("Aguardando envio de um arquivo Excel (.xlsx)...")
