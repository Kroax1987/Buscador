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
# MELHORIA: Corrigido "Ponto Importantes" para "Pontos Importantes" para consistência.
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
        "campos": ["Analista", "Unidade", "Protocolo", "Incidente", "Causa", "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento", "SLA", "Pontos Importantes"]
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
        st.info("Este erro ('File is not a zip file') geralmente acontece se o arquivo no GitHub estiver corrompido ou for um ponteiro do Git LFS. Por favor, tente baixar o arquivo do seu repositório e abri-lo localmente para verificar sua integridade.")
        return None

# CORREÇÃO CRÍTICA: A função original tinha erros de lógica e sintaxe que a impediam de funcionar.
def buscar_palavra(df, palavra):
    """Busca uma palavra-chave de forma flexível e robusta, iterando coluna por coluna."""
    # 1. Validação inicial
    if df is None or df.empty or not palavra:
        return pd.DataFrame()

    # 2. Normalizar a palavra-chave de busca uma única vez
    # Remove caracteres especiais e converte para minúsculas para uma busca mais flexível.
    palavra_normalizada = re.sub(r'[^a-zA-Z0-9]', '', str(palavra)).lower()

    # Se a palavra normalizada ficar vazia (ex: o usuário digitou apenas "[]"), não há o que buscar.
    if not palavra_normalizada:
        return pd.DataFrame()

    # 3. Criar uma máscara booleana para acumular os resultados
    final_mask = pd.Series(False, index=df.index)

    # 4. Iterar sobre cada coluna do DataFrame
    for col in df.columns:
        try:
            # Normalizar a coluna inteira para o mesmo formato da palavra-chave
            col_normalizada = df[col].astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.lower()
            # Verificar quais células da coluna contêm a palavra normalizada
            col_mask = col_normalizada.str.contains(palavra_normalizada, na=False)
            # Acumular os resultados na máscara final (usando o operador OR `|`)
            final_mask = final_mask | col_mask
        except Exception:
            # Ignora colunas que possam causar erro na conversão para string (raro, mas seguro)
            continue
            
    # 5. Retornar as linhas do DataFrame original onde a máscara é True
    return df[final_mask]

def destacar_palavra(val, palavra):
    """Função para aplicar estilo: destaca a palavra-chave encontrada em uma célula."""
    val_str = str(val)
    # A busca com re.escape garante que caracteres especiais na palavra (como '+', '()') não quebrem o regex.
    if palavra and re.search(re.escape(palavra), val_str, re.IGNORECASE):
        return 'background-color: yellow; color: black;'
    return ''

def adicionar_registro(caminho_arquivo, campos, novos_dados):
    """Lê um arquivo Excel, adiciona uma nova linha e o salva de volta."""
    try:
        if os.path.exists(caminho_arquivo):
            df = pd.read_excel(caminho_arquivo, engine='openpyxl')
        else:
            # Se o arquivo não existe, cria um DataFrame vazio com as colunas corretas.
            df = pd.DataFrame(columns=campos)

        # Garante que todas as colunas do formulário existam no DataFrame.
        for col in campos:
            if col not in df.columns:
                df[col] = None

        nova_linha = pd.DataFrame([novos_dados])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_excel(caminho_arquivo, index=False, engine='openpyxl')
        return True, None
    except Exception as e:
        return False, str(e)

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

all_data = carregar_dados()

tab_busca, tab_adicionar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Novo Registro"])

with tab_busca:
    st.header("Ferramenta de Busca Rápida")
    if all_data:
        # A barra lateral para depuração é uma ótima ideia!
        with st.sidebar:
            st.write("---")
            st.write("**Status dos Dados Carregados:**")
            for nome, df_info in all_data.items():
                st.write(f"- `{nome}`: {len(df_info)} linhas")
            st.write("---")

        palavra = st.text_input("Digite uma palavra-chave para buscar (ex: MPLS, Oi, cancelado):", placeholder="Não é necessário usar [ ] ou ( )")
        
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
                        # Usando 'styler' para aplicar o destaque
                        st.dataframe(
                            resultados.style.applymap(lambda val: destacar_palavra(val, palavra)),
                            use_container_width=True
                        )
                    else:
                        st.info(f"Nenhum resultado para '{palavra}' em {titulo.split(' - ')[1]}.")
    else:
        st.warning("A busca está indisponível pois os arquivos de dados não foram carregados.")

with tab_adicionar:
    st.header("Criar um Novo Registro")
    
    if not all_data:
        st.error("A função de adicionar registro está desabilitada pois os arquivos de dados não puderam ser lidos.")
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
                    elif campo.lower() in ["obs", "pontos importantes", "causa", "incidente"]:
                        novos_dados[campo] = st.text_area(f"**{campo}**")
                    else:
                        novos_dados[campo] = st.text_input(f"**{campo}**")
                
                submitted = st.form_submit_button("💾 Salvar Registro")
                if submitted:
                    sucesso, erro_msg = adicionar_registro(caminho_arquivo, campos, novos_dados)
                    if sucesso:
                        st.success(f"Registro adicionado com sucesso ao arquivo '{caminho_arquivo}'!")
                        st.info("Os dados serão atualizados em breve. A página será recarregada.")
                        st.cache_data.clear() # Limpa o cache
                        st.rerun() # Recarrega a página para refletir a mudança
                    else:
                        st.error(f"Falha ao salvar o registro: {erro_msg}")
