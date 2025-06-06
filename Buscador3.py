import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscador de Palavras", layout="wide")
st.title("🔍 Buscador NOC")

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
        # Lê todas as abas
        df = pd.read_excel(caminho_arquivo, sheet_name=None)

        # Opção para escolher uma aba ou todas as abas
        sheet_names = list(df.keys())
        sheet_names.insert(0, "Todas as abas")
        selected_sheet = st.selectbox("📑 Escolha a aba da planilha:", sheet_names)

        termo = st.text_input("🔎 Digite o termo a buscar:")

        if termo:
            st.subheader("📌 Resultados da Busca")

            if selected_sheet == "Todas as abas":
                resultados = []
                for sheet_name, data in df.items():
                    resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo, case=False, na=False), axis=1)]
                    if not resultado.empty:
                        resultados.append((sheet_name, resultado))

                if resultados:
                    for sheet_name, resultado in resultados:
                        st.markdown(f"### Aba: {sheet_name}")
                        st.dataframe(resultado)
                        csv = resultado.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Baixar resultados da aba {sheet_name}",
                            data=csv,
                            file_name=f'resultados_{sheet_name}.csv',
                            mime='text/csv'
                        )
                else:
                    st.warning("Nenhum resultado encontrado em nenhuma aba.")

            else:
                data = df[selected_sheet]
                resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo, case=False, na=False), axis=1)]

                if not resultado.empty:
                    st.subheader(f"Resultados na aba '{selected_sheet}'")
                    st.dataframe(resultado)
                    csv = resultado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar resultados",
                        data=csv,
                        file_name=f'resultados_{selected_sheet}.csv',
                        mime='text/csv'
                    )
                else:
                    st.warning("Nenhum resultado encontrado nessa aba.")
        else:
            st.info("Digite um termo para iniciar a busca.")

        # 🔽 Adicionar conteúdo se uma aba específica for escolhida
        if selected_sheet != "Todas as abas":
            st.markdown("---")
            st.subheader(f"📝 Adicionar novo conteúdo na aba '{selected_sheet}'")

            aba_df = df[selected_sheet]
            colunas = aba_df.columns.tolist()
            novos_dados = {}

            with st.form("formulario_novo_dado"):
                for coluna in colunas:
                    novos_dados[coluna] = st.text_input(f"{coluna}:", key=coluna)

                submitted = st.form_submit_button("➕ Adicionar linha")
                if submitted:
                    nova_linha = pd.DataFrame([novos_dados])
                    novo_df = pd.concat([aba_df, nova_linha], ignore_index=True)

                    # Salva no arquivo Excel mantendo as outras abas
                    with pd.ExcelWriter(caminho_arquivo, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        for aba, dados in df.items():
                            if aba == selected_sheet:
                                novo_df.to_excel(writer, sheet_name=aba, index=False)
                            else:
                                dados.to_excel(writer, sheet_name=aba, index=False)

                    st.success("✅ Nova linha adicionada com sucesso!")
                    st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
else:
    st.error(f"Arquivo '{caminho_arquivo}' não encontrado.")
