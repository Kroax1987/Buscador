import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("💡 Buscador e Editor de Dados Operacionais")

# Upload de arquivos
st.sidebar.header("Upload dos Arquivos Excel")
operadoras_file = st.sidebar.file_uploader("Arquivo de Operadoras (.xlsx)", type=["xlsx"])

# Inicializa os DataFrames
df_operadoras = None

# Tenta ler os arquivos e trata erros
try:
    if operadoras_file:
        df_operadoras = pd.read_excel(operadoras_file, engine="openpyxl")
        st.success("Arquivo de Operadoras carregado com sucesso!")
except Exception as e:
    st.error(f"Falha ao abrir {operadoras_file.name}: {e}")
    st.info("Verifique se o arquivo está corrompido ou se é um arquivo válido do Excel (.xlsx).")

# Exibição da interface apenas se os dados forem carregados com sucesso
if df_operadoras is not None:
    aba = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Novo Registro"])

    with aba[0]:
        st.subheader("Ferramenta de Busca Rápida")
        palavra_chave = st.text_input("Digite uma palavra-chave para buscar (ex: MPLS, Oi, cancelado):")

        if palavra_chave:
            resultados = df_operadoras[df_operadoras.apply(lambda row: row.astype(str).str.contains(palavra_chave, case=False).any(), axis=1)]
            st.write(f"Resultados encontrados: {len(resultados)}")
            st.dataframe(resultados)

    with aba[1]:
        st.subheader("Adicionar Novo Registro")
        with st.form("novo_registro_form"):
            novos_dados = {}
            for coluna in df_operadoras.columns:
                novos_dados[coluna] = st.text_input(f"{coluna}", key=coluna)

            if st.form_submit_button("Salvar"):
                nova_linha = pd.DataFrame([novos_dados])
                df_operadoras = pd.concat([df_operadoras, nova_linha], ignore_index=True)
                st.success("Novo registro adicionado!")

else:
    st.warning("Envie o arquivo .xlsx de operadoras válido para utilizar o sistema.")
