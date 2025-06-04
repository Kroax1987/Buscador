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
        # Lê todas as abas
        df = pd.read_excel(caminho_arquivo, sheet_name=None)

        # Opção para escolher uma aba ou todas as abas
        sheet_names = list(df.keys())
        sheet_names.insert(0, "Todas as abas")  # Inserir opção "Todas as abas" no topo
        selected_sheet = st.selectbox("📑 Escolha a aba da planilha:", sheet_names)

        termo = st.text_input("🔎 Digite o termo a buscar:")

        if termo:
            st.subheader("📌 Resultados da Busca")

            # Se escolher "Todas as abas"
            if selected_sheet == "Todas as abas":
                resultados = []
                for sheet_name, data in df.items():
                    # Busca na aba atual
                    resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo, case=False, na=False), axis=1)]
                    if not resultado.empty:
                        resultados.append((sheet_name, resultado))

                if resultados:
                    for sheet_name, resultado in resultados:
                        st.markdown(f"### Aba: {sheet_name}")
                        st.dataframe(resultado)
                        # Botão para baixar resultado
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
                # Busca na aba selecionada
                data = df[selected_sheet]
                resultado = data[data.apply(lambda row: row.astype(str).str.contains(termo, case=False, na=False), axis=1)]

                st.subheader(f"Resultados na aba {selected_sheet}")
                if not resultado.empty:
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

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")

else:
    st.error(f"Arquivo '{caminho_arquivo}' não encontrado.")
