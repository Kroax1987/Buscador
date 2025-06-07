import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

# --- CONFIGURAÇÕES E CONSTANTES ---
# Nomes dos arquivos
FILE_OPERADORAS = "Operadoras.xlsx"
FILE_DESIGNACOES = "Circuitos e Designações.xlsx"
FILE_CHAMADOS = "Chamados Abertos Fechados.xlsx"

# Configuração da página
st.set_page_config(page_title="Buscador Inteligente", layout="wide")
st.title("💡 Buscador e Editor de Dados Operacionais")

# --- DEFINIÇÃO DOS CAMPOS PARA OS FORMULÁRIOS ---
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
    """Carrega os dados dos arquivos Excel. Retorna um dicionário de DataFrames."""
    dados = {}
    try:
        dados[FILE_OPERADORAS] = pd.read_excel(FILE_OPERADORAS, engine='openpyxl')
        dados[FILE_DESIGNACOES] = pd.read_excel(FILE_DESIGNACOES, engine='openpyxl')
        dados[FILE_CHAMADOS] = pd.read_excel(FILE_CHAMADOS, engine='openpyxl')
        return dados
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo não encontrado - {e.filename}. Verifique se todos os arquivos Excel estão no repositório.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado ao carregar os arquivos: {e}")
        return None

def buscar_palavra(df, palavra):
    """Busca uma palavra-chave em todas as colunas de um DataFrame."""
    if not palavra:
        return pd.DataFrame()
    mask = df.apply(lambda row: row.astype(str).str.contains(palavra, case=False, na=False).any(), axis=1)
    return df[mask]

def destacar_palavra(val, palavra):
    """Função para aplicar estilo: destaca a palavra-chave encontrada em uma célula."""
    val_str = str(val)
    if palavra and re.search(palavra, val_str, re.IGNORECASE):
        return 'background-color: yellow; color: black;'
    return ''

def adicionar_registro(caminho_arquivo, campos, novos_dados):
    """Lê um arquivo Excel, adiciona uma nova linha e o salva de volta."""
    try:
        if os.path.exists(caminho_arquivo):
            df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        else:
            # Cria um DataFrame vazio se o arquivo não existir
            df = pd.DataFrame(columns=campos)

        # Garante que todas as colunas do formulário existam no DataFrame
        for col in campos:
            if col not in df.columns:
                df[col] = None

        nova_linha = pd.DataFrame([novos_dados])
        df = pd.concat([df, nova_linha], ignore_index=True)
        
        # Salva o arquivo
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        return True, None
    except Exception as e:
        return False, str(e)

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

# Carrega os dados
all_data = carregar_dados()

# Cria as abas principais da aplicação
tab_busca, tab_adicionar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Novo Registro"])

# --- ABA DE BUSCA ---
with tab_busca:
    st.header("Ferramenta de Busca Rápida")
    if all_data:
        palavra = st.text_input("Digite uma palavra-chave para buscar em todas as bases:", placeholder="Ex: Oi, Embratel, cancelado...")

        if palavra:
            st.markdown("---")
            datasets_map = {
                "🔌 Resultados - Operadoras": FILE_OPERADORAS,
                "📡 Resultados - Circuitos e Designações": FILE_DESIGNACOES,
                "📁 Resultados - Chamados": FILE_CHAMADOS
            }

            for titulo, arquivo_nome in datasets_map.items():
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
        st.warning("A busca está indisponível pois os arquivos de dados não foram carregados.")

# --- ABA DE ADICIONAR REGISTRO ---
with tab_adicionar:
    st.header("Criar um Novo Registro")
    st.info("Selecione o tipo de formulário, preencha os dados e clique em 'Salvar'. O novo registro será adicionado ao arquivo Excel correspondente.")

    # Seleção do tipo de formulário
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
                # Lógica para campos de Data/Hora terem valor padrão
                if "Data/Hora" in campo:
                    valor_padrao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    novos_dados[campo] = st.text_input(f"**{campo}**", value=valor_padrao)
                # Lógica para campos de texto longos
                elif campo.lower() in ["obs", "pontos importantes", "ponto importantes", "causa", "incidente"]:
                    novos_dados[campo] = st.text_area(f"**{campo}**")
                else:
                    novos_dados[campo] = st.text_input(f"**{campo}**")
            
            # Botão de salvar dentro do formulário
            submitted = st.form_submit_button("💾 Salvar Registro")

            if submitted:
                sucesso, erro_msg = adicionar_registro(caminho_arquivo, campos, novos_dados)
                if sucesso:
                    st.success(f"Registro adicionado com sucesso ao arquivo '{caminho_arquivo}'!")
                    st.info("A página será atualizada para refletir os novos dados.")
                    # Limpa o cache para que os dados sejam recarregados na próxima execução
                    st.cache_data.clear()
                    # Força a re-execução do script para atualizar a visualização
                    st.experimental_rerun()
                else:
                    st.error(f"Falha ao salvar o registro: {erro_msg}")
