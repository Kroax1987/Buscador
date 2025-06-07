import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

# --- CONFIGURAÇÕES E CONSTANTES ---
FILE_OPERADORAS = "Operadoras.xlsx"
FILE_DESIGNACOES = "Circuitos e Designações.xlsx"
FILE_CHAMADOS = "Chamados Abertos Fechados.xlsx"

st.set_page_config(page_title="Buscador Inteligente", layout="wide")
st.title("💡 Buscador e Editor de Dados Operacionais")

CAMPOS_FORMULARIOS = {
    "Contatos das Operadoras": {
        "arquivo": FILE_OPERADORAS,
        "campos": ["Operadora", "Links", "User", "Senha", "E-mail", "Telefone", "CNPJ", "OBS", "Pontos importantes"]
    },
    "Designações dos Links": {
        "arquivo": FILE_DESIGNACOES,
        "campos": ["Operadora", "Unidade", "Link", "Designação", "Geo"]
    },
    "Chamados de Operadoras": {
        "arquivo": FILE_CHAMADOS,
        "campos": ["Analista", "Unidade", "Protocolo", "Incidente", "Causa", "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento", "SLA", "Ponto Importantes"]
    }
}

# --- FUNÇÕES ---

@st.cache_data
def carregar_dados():
    dados = {}
    arquivos = [FILE_OPERADORAS, FILE_DESIGNACOES, FILE_CHAMADOS]
    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            st.warning(f"⚠️ Arquivo não encontrado: `{arquivo}`.")
            continue
        try:
            df = pd.read_excel(arquivo, engine='openpyxl')
            dados[arquivo] = df
        except Exception as e:
            st.error(f"❌ Falha ao abrir `{arquivo}`: {e}")
            st.info("Verifique se o arquivo está corrompido ou se é um arquivo válido do Excel (.xlsx).")
    return dados if dados else None

def buscar_palavra(df, palavra):
    if not palavra:
        return pd.DataFrame()

    palavra_normalizada = re.sub(r'[^a-zA-Z0-9]', '', str(palavra)).lower()
    if not palavra_normalizada:
        return pd.DataFrame()

    final_mask = pd.Series(False, index=df.index)

    for col in df.columns:
        try:
            col_normalizada = df[col].astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.lower()
            col_mask = col_normalizada.str.contains(palavra_normalizada, na=False)
            final_mask = final_mask | col_mask
        except:
            continue
    return df[final_mask]

def destacar_palavra(val, palavra):
    val_str = str(val)
    if palavra and re.search(re.escape(palavra), val_str, re.IGNORECASE):
        return 'background-color: yellow; color: black;'
    return ''

def adicionar_registro(caminho_arquivo, campos, novos_dados):
    try:
        if os.path.exists(caminho_arquivo):
            df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        else:
            df = pd.DataFrame(columns=campos)

        for col in campos:
            if col not in df.columns:
                df[col] = None

        nova_linha = pd.DataFrame([novos_dados])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        return True, None
    except Exception as e:
        return False, str(e)

# --- EXECUÇÃO ---

all_data = carregar_dados()

tab_busca, tab_adicionar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Novo Registro"])

with tab_busca:
    st.header("Ferramenta de Busca Rápida")
    if all_data:
        palavra = st.text_input("Digite uma palavra-chave para buscar (ex: MPLS, Oi, cancelado):", placeholder="Não é necessário usar [ ] ou ( )")
        
        if palavra:
            st.markdown("---")
            datasets_map = {
                "🔌 Resultados - Operadoras": FILE_OPERADORAS,
                "📡 Resultados - Circuitos e Designações": FILE_DESIGNACOES,
                "📁 Resultados - Chamados": FILE_CHAMADOS
            }
            for titulo, arquivo_nome in datasets_map.items():
                if arquivo_nome in all_data:
                    with st.expander(titulo, expanded=True):
                        df = all_data[arquivo_nome]
                        resultados = buscar_palavra(df, palavra)
                        if not resultados.empty:
                            st.dataframe(
                                resultados.style.applymap(lambda val: destacar_palavra(val, palavra)),
                                use_container_width=True
                            )
                        else:
                            st.info(f"Nenhum resultado para '{palavra}' em {titulo.split(' - ')[1]}.")
                else:
                    st.warning(f"Arquivo {arquivo_nome} não carregado. Verifique sua integridade.")
    else:
        st.warning("A busca está indisponível pois nenhum dado foi carregado com sucesso.")

with tab_adicionar:
    st.header("Criar um Novo Registro")
    
    if not all_data:
        st.error("A função de adicionar está desabilitada pois os arquivos não foram carregados corretamente.")
    else:
        st.info("Selecione o tipo de formulário, preencha os dados e clique em 'Salvar'.")
        tipo_formulario = st.selectbox(
            "Qual tipo de registro você deseja adicionar?",
            options=list(CAMPOS_FORMULARIOS.keys())
        )
        if tipo_formulario:
            info_form = CAMPOS_FORMULARIOS[tipo_formulario]
            caminho_arquivo = info_form["arquivo"]
            campos = info_form["campos"]
            with st.form(key=f"form_{caminho_arquivo}", clear_on_submit=True):
                st.subheader(f"Formulário: {tipo_formulario}")
                novos_dados = {}
                for campo in campos:
                    if "Data/Hora" in campo:
                        valor_padrao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        novos_dados[campo] = st.text_input(f"**{campo}**", value=valor_padrao)
                    elif campo.lower() in ["obs", "pontos importantes", "ponto importantes", "causa", "incidente"]:
                        novos_dados[campo] = st.text_area(f"**{campo}**")
                    else:
                        novos_dados[campo] = st.text_input(f"**{campo}**")

                submitted = st.form_submit_button("💾 Salvar Registro")
                if submitted:
                    sucesso, erro_msg = adicionar_registro(caminho_arquivo, campos, novos_dados)
                    if sucesso:
                        st.success(f"Registro adicionado com sucesso ao arquivo '{caminho_arquivo}'!")
                        st.info("A página será atualizada para refletir os novos dados.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Falha ao salvar o registro: {erro_msg}")
