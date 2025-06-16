import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buscador Inteligente", layout="wide")
st.title("🔍 Buscador Inteligente de Planilhas")

# Carrega as planilhas
@st.cache_data
def carregar_planilhas():
    try:
        df_operadoras = pd.read_excel("operadoras.xlsx")
        df_mpls = pd.read_excel("mpls.xlsx")
        return df_operadoras, df_mpls
    except Exception as e:
        st.error(f"Erro ao carregar planilhas: {e}")
        return None, None

df_operadoras, df_mpls = carregar_planilhas()

if df_operadoras is not None and df_mpls is not None:
    # Campo de busca
    termo = st.text_input("Digite uma palavra-chave para buscar nos dados:")

    if termo:
        termo_lower = termo.lower()

        # Busca inteligente nas duas planilhas
        def buscar(df):
            return df[df.apply(lambda row: row.astype(str).str.lower().str.contains(termo_lower).any(), axis=1)]

        resultado_operadoras = buscar(df_operadoras)
        resultado_mpls = buscar(df_mpls)

        # Exibe os resultados
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📁 Resultados - Operadoras")
            st.dataframe(resultado_operadoras, use_container_width=True)

        with col2:
            st.subheader("📁 Resultados - MPLS")
            st.dataframe(resultado_mpls, use_container_width=True)

        # Download dos resultados, se houver
        if not resultado_operadoras.empty or not resultado_mpls.empty:
            with st.expander("⬇️ Baixar resultados"):
                if not resultado_operadoras.empty:
                    csv1 = resultado_operadoras.to_csv(index=False).encode('utf-8')
                    st.download_button("Baixar Operadoras CSV", csv1, "operadoras_resultado.csv", "text/csv")

                if not resultado_mpls.empty:
                    csv2 = resultado_mpls.to_csv(index=False).encode('utf-8')
                    st.download_button("Baixar MPLS CSV", csv2, "mpls_resultado.csv", "text/csv")

    else:
        st.info("Digite um termo acima para iniciar a busca.")
else:
    st.warning("Certifique-se de que os arquivos 'operadoras.xlsx' e 'mpls.xlsx' estão na mesma pasta do script.")
