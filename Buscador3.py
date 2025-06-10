import streamlit as st
import pandas as pd
import re
import os
import json
from datetime import datetime

# Arquivos de dados
FILE_OPERADORAS = "Operadoras.xlsx"
FILE_DESIGNACOES = "Circuitos e Designações.xlsx"
FILE_CHAMADOS = "Chamados Abertos Fechados.xlsx"
FILE_USUARIOS = "usuarios.json"

st.set_page_config(page_title="Buscador Inteligente", layout="wide")

# --- Funções de autenticação ---
def carregar_usuarios():
    if os.path.exists(FILE_USUARIOS):
        with open(FILE_USUARIOS, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(FILE_USUARIOS, "w") as f:
        json.dump(usuarios, f)

def autenticar(usuario, senha):
    usuarios = carregar_usuarios()
    return usuarios.get(usuario) == senha

def criar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario in usuarios:
        return False
    usuarios[usuario] = senha
    salvar_usuarios(usuarios)
    return True

# --- Tela de login ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    aba_login, aba_criar = st.tabs(["🔐 Login", "🆕 Criar Usuário"])
    with aba_login:
        st.subheader("Entrar")
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if autenticar(user, pwd):
                st.session_state.logado = True
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with aba_criar:
        st.subheader("Criar novo usuário")
        new_user = st.text_input("Novo usuário")
        new_pwd = st.text_input("Nova senha", type="password")
        if st.button("Criar Conta"):
            if criar_usuario(new_user, new_pwd):
                st.success("Usuário criado com sucesso. Faça login.")
            else:
                st.error("Usuário já existe.")
    st.stop()

# --- Dados e funções principais ---
st.title("💡 Buscador e Editor de Dados Operacionais")

@st.cache_data
def carregar_dados():
    dados = {}
    try:
        dados[FILE_OPERADORAS] = pd.read_excel(FILE_OPERADORAS, engine='openpyxl')
        dados[FILE_DESIGNACOES] = pd.read_excel(FILE_DESIGNACOES, engine='openpyxl')
        dados[FILE_CHAMADOS] = pd.read_excel(FILE_CHAMADOS, engine='openpyxl')
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None

def buscar_palavra(df, palavra):
    if df is None or df.empty or not palavra:
        return pd.DataFrame()
    termo = palavra.lower()
    return df[df.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)]

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

# Estrutura dos formulários
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

# --- Aplicação principal ---
all_data = carregar_dados()
tab_busca, tab_adicionar, tab_formatar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Registro", "💬 WhatsApp Formatado"])

with tab_busca:
    st.header("Busca Inteligente")
    palavra = st.text_input("Palavra-chave para busca:")
    if palavra:
        for nome, arquivo in {
            "🔌 Operadoras": FILE_OPERADORAS,
            "📡 Designações": FILE_DESIGNACOES,
            "📁 Chamados": FILE_CHAMADOS
        }.items():
            st.subheader(nome)
            df = all_data[arquivo]
            encontrados = buscar_palavra(df, palavra)
            if not encontrados.empty:
                st.dataframe(encontrados.style.applymap(lambda v: destacar_palavra(v, palavra)), use_container_width=True)
            else:
                st.info("Nenhum resultado encontrado.")

with tab_adicionar:
    st.header("Adicionar Registro")
    tipo = st.selectbox("Tipo de Dado", list(CAMPOS_FORMULARIOS.keys()))
    campos = CAMPOS_FORMULARIOS[tipo]["campos"]
    caminho = CAMPOS_FORMULARIOS[tipo]["arquivo"]
    with st.form(f"form_{tipo}"):
        novos_dados = {}
        for campo in campos:
            if "data/hora" in campo.lower():
                valor = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                novos_dados[campo] = st.text_input(campo, value=valor)
            elif campo.lower() in ["obs", "pontos importantes", "causa", "incidente"]:
                novos_dados[campo] = st.text_area(campo)
            else:
                novos_dados[campo] = st.text_input(campo)
        if st.form_submit_button("💾 Salvar"):
            ok, erro = adicionar_registro(caminho, campos, novos_dados)
            if ok:
                st.success("Registro salvo com sucesso.")
                st.cache_data.clear()
            else:
                st.error(f"Erro: {erro}")

with tab_formatar:
    st.header("Mensagens para WhatsApp")
    if FILE_CHAMADOS in all_data:
        df = all_data[FILE_CHAMADOS]
        for _, row in df.iterrows():
            analista = row.get("Analista", "Desconhecido")
            unidade = row.get("Unidade", "N/A")
            protocolo = row.get("Protocolo", "N/A")
            incidente = row.get("Incidente", "N/A")
            operadora = row.get("Operadora", "N/A")
            status = row.get("Pontos Importantes", "")
            encerramento = row.get("Data/Hora de Encerramento", "")
            isolada = "SIM" if "isol" in str(row.get("Causa", "")).lower() else "NÃO"

            encerramento_str = pd.to_datetime(encerramento).strftime("%d/%m/%Y %Hh%M") if pd.notna(encerramento) else "N/A"

            mensagem = f"""
Bom dia, aqui é o analista *{analista}*. Segue o caso abaixo para informação:

Unidade: *{unidade}* 📶  
Unidade Isolada: {isolada}  
Chamado Service No ⚠️: {incidente}  
Operadora: {operadora}  
Chamado Operadora: {protocolo}

Último Status: {status}  
Encerramento ✅: {encerramento_str}
""".strip()
            with st.expander(f"{unidade}", expanded=False):
                st.code(mensagem, language="markdown")
    else:
        st.warning("Arquivo de chamados não encontrado.")
