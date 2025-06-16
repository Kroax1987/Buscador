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
    tab_login, tab_criar, tab_admin = st.tabs(["Entrar", "Criar Usuário", "Administração"])
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

    with tab_admin:
        usuarios = carregar_usuarios()
        st.write("Usuários cadastrados:")
        for user in usuarios:
            col1, col2 = st.columns([3,1])
            col1.write(user)
            if col2.button("Remover", key=user):
                usuarios.pop(user)
                salvar_usuarios(usuarios)
                st.success(f"Usuário '{user}' removido.")
                st.rerun()

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

# --- ABA DE BUSCA ---
with tab_busca:
    st.header("Busca por Palavra-chave")
    palavra = st.text_input("Digite uma palavra-chave para buscar nas planilhas:")
    filtro_data = st.date_input("Filtrar por Data (Chamados)", [], format="DD/MM/YYYY")
    filtro_analista = st.text_input("Filtrar por Analista (Chamados):")
    filtro_operadora = st.text_input("Filtrar por Operadora:")

    if st.button("🔍 Buscar") and palavra:
        for nome_arquivo, df in all_data.items():
            st.subheader(f"📄 Resultados em {nome_arquivo}:")
            df_temp = df.copy()
            if filtro_operadora:
                df_temp = df_temp[df_temp.apply(lambda row: filtro_operadora.lower() in str(row).lower(), axis=1)]
            if filtro_analista and "Analista" in df_temp.columns:
                df_temp = df_temp[df_temp["Analista"].str.contains(filtro_analista, case=False, na=False)]
            if filtro_data and "Data/Hora de Abertura" in df_temp.columns:
                datas = pd.to_datetime(df_temp["Data/Hora de Abertura"], errors='coerce')
                df_temp = df_temp[(datas.dt.date >= filtro_data[0]) & (datas.dt.date <= filtro_data[-1])]
            resultados = df_temp[df_temp.apply(lambda row: palavra.lower() in str(row).lower(), axis=1)]
            st.write(resultados if not resultados.empty else "Nenhum resultado encontrado.")

# --- ABA DE ADIÇÃO ---
with tab_adicionar:
    st.header("Novo Registro")
    CAMPOS = {
        "Chamados de Operadoras": {
            "arquivo": FILE_CHAMADOS,
            "campos": [
                "Analista", "Unidade", "Protocolo", "Incidente", "Causa",
                "Operadora", "Data/Hora de Abertura", "Data/Hora de Encerramento",
                "SLA", "Ultimos Status", "Prox. Status"
            ]
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
            if campo == "Analista":
                dados[campo] = st.session_state["usuario"]
            elif campo == "Incidente":
                dados[campo] = st.text_input(campo, placeholder="INC1234567")
            elif campo == "Causa":
                dados[campo] = st.selectbox(campo, ["Falha Massiva", "Rompimento de Fibra", "Perca de Pacote", "Alta Latencia", "Falha no Equipamento"])
            elif campo.startswith("Data/Hora"):
                dados[campo] = st.date_input(campo).strftime("%d/%m/%Y") + " " + st.time_input(campo).strftime("%H:%M:%S")
            elif campo == "SLA":
                sla = st.radio("SLA Atendido?", ["Sim", "Não"], horizontal=True)
                cor = "#ff4b4b" if sla == "Sim" else "#2ecc71"
                st.markdown(f"<span style='color: {cor}; font-weight: bold;'>SLA: {sla}</span>", unsafe_allow_html=True)
                dados[campo] = sla
            elif campo == "Ultimos Status" or campo == "Prox. Status":
                dados[campo] = st.text_area(campo)
            else:
                dados[campo] = st.text_input(campo)

        submit = st.form_submit_button("📂 Salvar Registro")

    if submit:
        sucesso, erro = adicionar_registro(arquivo, campos, dados)
        if sucesso:
            st.success("Registro salvo com sucesso!")
            isolada = "NÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃ¬ÃÂÃÃÂÃÂ¢ÃÂÃ¬ÃÂÃNÃÂÃÂ£O" if "isol" not in dados["Causa"].lower() else "SIM"
            msg = f"""
Boa tarde, aqui ÃÂ© o analista *{dados['Analista']}* Segue o caso abaixo para informaÃ§Ã£o:

*Unidade:* {dados['Unidade']}
*Unidade Isolada:* {isolada}
*Chamado Service Now⚠️:* {dados['Incidente']}
*Operadora:* {dados['Operadora']}
*Chamado Operadora:* {dados['Protocolo']}

*Ãltimo Status*: {dados['Ultimos Status']}

*PrÃ³x. Status:* {dados['Prox. Status']}
"""
            st.markdown("---")
            st.subheader("📤 Copie e cole no WhatsApp:")
            st.code(msg.strip(), language="markdown")
            st.balloons()
        else:
            st.error(f"Erro ao salvar: {erro}")
