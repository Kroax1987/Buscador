import streamlit as st
import pandas as pd
import re
import os
import json
from datetime import datetime

# --- CONFIGURAÇÕES INICIAIS ---
FILE_OPERADORAS = "Operadoras.xlsx"
FILE_DESIGNACOES = "Circuitos e Designações.xlsx"
FILE_CHAMADOS = "Chamados Abertos Fechados.xlsx"
FILE_USUARIOS = "usuarios.json"

st.set_page_config(page_title="Buscador Inteligente", layout="wide")

# --- AUTENTICAÇÃO ---
def carregar_usuarios():
    if os.path.exists(FILE_USUARIOS):
        with open(FILE_USUARIOS, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(dados):
    with open(FILE_USUARIOS, "w") as f:
        json.dump(dados, f)

def login():
    st.title("🔐 Login")
    tab_login, tab_criar = st.tabs(["Entrar", "Criar Usuário"])
    with tab_login:
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            usuarios = carregar_usuarios()
            if username in usuarios and usuarios[username] == senha:
                st.session_state["usuario"] = username
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_criar:
        novo_user = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        if st.button("Criar usuário"):
            usuarios = carregar_usuarios()
            if novo_user in usuarios:
                st.warning("Usuário já existe.")
            else:
                usuarios[novo_user] = nova_senha
                salvar_usuarios(usuarios)
                st.success("Usuário criado com sucesso.")

if "usuario" not in st.session_state:
    login()
    st.stop()

# --- FUNÇÕES DE BUSCA E EDIÇÃO ---
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
    termo = str(palavra).lower()
    mascara = pd.Series(False, index=df.index)
    for col in df.columns:
        try:
            mascara |= df[col].astype(str).str.lower().str.contains(termo, na=False)
        except Exception:
            continue
    return df[mascara]

def destacar_palavra(val, palavra):
    if palavra and re.search(re.escape(palavra), str(val), re.IGNORECASE):
        return 'background-color: yellow; color: black;'
    return ''

def adicionar_registro(caminho, campos, dados):
    try:
        df = pd.read_excel(caminho, engine='openpyxl') if os.path.exists(caminho) else pd.DataFrame(columns=campos)
        for col in campos:
            if col not in df.columns:
                df[col] = None
        nova_linha = pd.DataFrame([dados])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_excel(caminho, index=False, engine='openpyxl')
        return True, None
    except Exception as e:
        return False, str(e)

# --- LÓGICA PRINCIPAL ---
all_data = carregar_dados()
st.title("💡 Buscador e Editor de Dados Operacionais")
tab_busca, tab_adicionar = st.tabs(["🔍 Buscar Dados", "➕ Adicionar Registro"])

with tab_busca:
    st.header("Busca Rápida")
    palavra = st.text_input("Palavra-chave:")
    if palavra and all_data:
        for titulo, arquivo in {
            "🔌 Operadoras": FILE_OPERADORAS,
            "📡 Designações": FILE_DESIGNACOES,
            "📁 Chamados": FILE_CHAMADOS
        }.items():
            with st.expander(titulo, expanded=True):
                df = all_data[arquivo]
                res = buscar_palavra(df, palavra)
                if not res.empty:
                    st.dataframe(res.style.applymap(lambda val: destacar_palavra(val, palavra)), use_container_width=True)
                else:
                    st.info("Nenhum resultado encontrado.")

with tab_adicionar:
    st.header("Novo Registro")
    CAMPOS = {
        "Chamados de Operadoras": {
            "arquivo": FILE_CHAMADOS,
            "campos": ["Analista", "Unidade", "Protocolo", "Incidente", "Causa", "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento", "SLA", "Pontos Importantes"]
        }
    }

    tipo = st.selectbox("Tipo de Registro", list(CAMPOS.keys()))
    info = CAMPOS[tipo]
    arquivo = info["arquivo"]
    campos = info["campos"]

    with st.form(f"form_{arquivo}"):
        st.subheader(tipo)
        dados = {}
        for campo in campos:
            if "Data/Hora" in campo:
                dados[campo] = st.text_input(campo, value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            elif campo.lower() in ["obs", "pontos importantes", "causa", "incidente"]:
                dados[campo] = st.text_area(campo)
            elif campo == "Analista":
                dados[campo] = st.session_state["usuario"]
            else:
                dados[campo] = st.text_input(campo)
        submit = st.form_submit_button("💾 Salvar Registro")

    if submit:
        sucesso, erro = adicionar_registro(arquivo, campos, dados)
        if sucesso:
            st.success("Registro salvo com sucesso!")
            # Geração da mensagem para WhatsApp
            encerramento = dados["Data/Hora de Encerramento"]
            isolada = "SIM" if "isol" in dados["Causa"].lower() else "NÃO"
            msg = f"""
Bom dia, aqui é o analista *{dados['Analista']}*. Segue o caso abaixo para informação:

Unidade: *{dados['Unidade']}* 📶  
Unidade Isolada: {isolada}  
Chamado Service No ⚠️: {dados['Incidente']}  
Operadora: {dados['Operadora']}  
Chamado Operadora: {dados['Protocolo']}

Último Status: {dados['Pontos Importantes']}  
Encerramento ✅: {encerramento}
"""
            st.markdown("---")
            st.subheader("📤 Copie e cole no WhatsApp:")
            st.code(msg.strip(), language="markdown")
            st.balloons()
        else:
            st.error(f"Erro ao salvar: {erro}")
