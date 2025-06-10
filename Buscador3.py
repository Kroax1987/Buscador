import streamlit as st
import pandas as pd
import re
import os
import hashlib
from datetime import datetime

# --- CONFIGURAÇÕES E CONSTANTES ---
FILE_OPERADORAS = "Operadoras.xlsx"
FILE_DESIGNACOES = "Circuitos e Designações.xlsx"
FILE_CHAMADOS = "Chamados Abertos Fechados.xlsx"
FILE_USUARIOS = "usuarios.csv"

st.set_page_config(page_title="Buscador Inteligente", layout="wide")

# --- FUNÇÕES AUXILIARES PARA LOGIN ---
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_usuario(usuario, senha):
    if not os.path.exists(FILE_USUARIOS):
        return False
    df = pd.read_csv(FILE_USUARIOS)
    senha_hash = hash_senha(senha)
    return ((df["usuario"] == usuario) & (df["senha"] == senha_hash)).any()

def criar_usuario(usuario, senha):
    senha_hash = hash_senha(senha)
    if os.path.exists(FILE_USUARIOS):
        df = pd.read_csv(FILE_USUARIOS)
        if usuario in df["usuario"].values:
            return False, "Usuário já existe."
        df = pd.concat([df, pd.DataFrame([{"usuario": usuario, "senha": senha_hash}])], ignore_index=True)
    else:
        df = pd.DataFrame([{"usuario": usuario, "senha": senha_hash}])
    df.to_csv(FILE_USUARIOS, index=False)
    return True, "Usuário criado com sucesso."

# --- TELA DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🔐 Login - Buscador Inteligente")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])
    
    with aba_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if verificar_usuario(usuario, senha):
                st.session_state["logado"] = True
                st.success("Login realizado com sucesso! Carregando aplicativo...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    
    with aba_cadastro:
        novo_usuario = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        if st.button("Criar Conta"):
            sucesso, msg = criar_usuario(novo_usuario, nova_senha)
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)
    st.stop()  # Impede carregamento do app sem login

# --- APLICATIVO PRINCIPAL (DEPOIS DO LOGIN) ---
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
        "campos": ["Analista", "Unidade", "Protocolo", "Incidente", "Causa", "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento", "SLA", "Pontos Importantes"]
    }
}

@st.cache_data
def carregar_dados():
    dados = {}
    try:
        dados[FILE_OPERADORAS] = pd.read_excel(FILE_OPERADORAS, engine='openpyxl')
        dados[FILE_DESIGNACOES] = pd.read_excel(FILE_DESIGNACOES, engine='openpyxl')
        dados[FILE_CHAMADOS] = pd.read_excel(FILE_CHAMADOS, engine='openpyxl')
        return dados
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo não encontrado - {e.filename}.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None

def buscar_palavra(df, palavra):
    if df is None or df.empty or not palavra:
        return pd.DataFrame()
    termo_busca = str(palavra).lower()
    mascara_final = pd.Series(False, index=df.index)
    for col in df.columns:
        try:
            mascara_coluna = df[col].astype(str).str.lower().str.contains(termo_busca, na=False)
            mascara_final = mascara_final | mascara_coluna
        except Exception:
            continue
    return df[mascara_final]

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

all_data = carregar_dados()

tab_busca, tab_adicionar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Novo Registro"])

with tab_busca:
    st.header("Ferramenta de Busca Rápida")
    if all_data:
        palavra = st.text_input("Digite uma palavra-chave para buscar (ex: MPLS, Oi):")
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
        st.warning("A busca está indisponível pois os arquivos não foram carregados.")

with tab_adicionar:
    st.header("Criar um Novo Registro")
    if not all_data:
        st.error("Os arquivos não foram carregados. Verifique e recarregue a página.")
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
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar registro: {erro_msg}")
