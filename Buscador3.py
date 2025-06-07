import streamlit as st
import pandas as pd
import re # Importa o módulo de expressões regulares para o highlighting

# --- CONFIGURAÇÕES E CONSTANTES ---
# Caminhos dos arquivos
PATH_OPERADORAS = "Operadoras.xlsx"
PATH_DESIGNACOES = "Circuitos e Designações.xlsx"
PATH_CHAMADOS = "Chamados Abertos Fechados.xlsx"

# Configuração da página
st.set_page_config(page_title="Buscador Inteligente", layout="wide")
st.title("🔍 Buscador Inteligente de Dados Operacionais")

# --- FUNÇÕES ---

@st.cache_data
def carregar_dados():
    """Carrega os dados dos arquivos Excel, retornando os DataFrames."""
    try:
        operadoras_df = pd.read_excel(PATH_OPERADORAS)
        designacoes_df = pd.read_excel(PATH_DESIGNACOES)
        chamados_df = pd.read_excel(PATH_CHAMADOS)
        return operadoras_df, designacoes_df, chamados_df
    except FileNotFoundError:
        st.error(f"Erro: Um ou mais arquivos não foram encontrados. Verifique se os arquivos `{PATH_OPERADORAS}`, `{PATH_DESIGNACOES}` e `{PATH_CHAMADOS}` estão na mesma pasta que o script.")
        return None, None, None
    except Exception as e:
        st.error(f"Erro inesperado ao carregar os arquivos: {e}")
        return None, None, None

def buscar_palavra(df, palavra):
    """
    Busca uma palavra-chave em todas as colunas de um DataFrame.
    A busca é case-insensitive.
    """
    if not palavra:
        return pd.DataFrame()
    
    # Cria uma máscara booleana para as linhas que contêm a palavra
    mask = df.apply(lambda row: row.astype(str).str.contains(palavra, case=False, na=False).any(), axis=1)
    resultados = df[mask]
    return resultados

def destacar_palavra(val, palavra):
    """
    Função para aplicar estilo: destaca a palavra-chave encontrada em uma célula.
    """
    val_str = str(val)
    if palavra and re.search(palavra, val_str, re.IGNORECASE):
        return 'background-color: yellow'
    return ''

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

# Carrega os dados e armazena em cache
operadoras_df, designacoes_df, chamados_df = carregar_dados()

# Verifica se os dados foram carregados com sucesso antes de continuar
if all(df is not None for df in [operadoras_df, designacoes_df, chamados_df]):
    
    # Input da palavra-chave
    palavra = st.text_input("Digite uma palavra-chave para buscar:", placeholder="Ex: Oi, Embratel, cancelado...")

    if palavra:
        st.markdown("---") # Linha divisória
        
        # Dicionário para iterar sobre os DataFrames e seus títulos
        datasets = {
            "🔌 Resultados - Operadoras": operadoras_df,
            "📡 Resultados - Circuitos e Designações": designacoes_df,
            "📁 Resultados - Chamados": chamados_df
        }

        for titulo, df in datasets.items():
            with st.expander(titulo, expanded=True):
                resultados = buscar_palavra(df, palavra)
                
                if not resultados.empty:
                    # Aplica o estilo para destacar a palavra encontrada
                    st.dataframe(
                        resultados.style.applymap(lambda val: destacar_palavra(val, palavra)),
                        use_container_width=True
                    )
                else:
                    st.info(f"Nenhum resultado encontrado para '{palavra}' nesta base de dados.")
else:
    st.warning("A aplicação não pode iniciar pois os arquivos de dados não foram carregados. Por favor, corrija o erro acima.")
