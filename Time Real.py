import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Clima Real por Usuários", layout="centered")

USERS_FILE = "usuarios_clima.json"
POSTS_FILE = "relatos_climaticos.csv"

# ---------------------- Funções de Usuário ----------------------
def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USERS_FILE, "w") as f:
        json.dump(usuarios, f)

# ---------------------- Login/Cadastro ----------------------
def login():
    st.title("☁️ Clima Real por Usuários")
    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with aba_login:
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            usuarios = carregar_usuarios()
            if username in usuarios and usuarios[username] == senha:
                st.session_state.usuario = username
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    with aba_cadastro:
        novo_usuario = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")
        if st.button("Cadastrar"):
            usuarios = carregar_usuarios()
            if novo_usuario in usuarios:
                st.warning("Usuário já existe.")
            else:
                usuarios[novo_usuario] = nova_senha
                salvar_usuarios(usuarios)
                st.success("Usuário cadastrado com sucesso! Volte para Entrar.")

if "usuario" not in st.session_state:
    login()
    st.stop()

# ---------------------- Postagens ----------------------
def carregar_posts():
    if os.path.exists(POSTS_FILE):
        return pd.read_csv(POSTS_FILE)
    return pd.DataFrame(columns=["usuario", "data_hora", "cidade", "descricao"])

def salvar_post(post):
    df = carregar_posts()
    df = pd.concat([df, pd.DataFrame([post])], ignore_index=True)
    df.to_csv(POSTS_FILE, index=False)

# ---------------------- Interface Principal ----------------------
st.title("📍 Relatos do Clima em Tempo Real")

aba_feed, aba_novo = st.tabs(["🌦️ Feed", "➕ Novo Relato"])

with aba_feed:
    st.subheader("🔎 Veja relatos de outras pessoas")
    posts = carregar_posts()
    filtro_cidade = st.text_input("Filtrar por cidade:")
    if filtro_cidade:
        posts = posts[posts["cidade"].str.contains(filtro_cidade, case=False)]

    posts = posts.sort_values("data_hora", ascending=False)
    for _, row in posts.iterrows():
        with st.container():
            st.markdown(f"**📍 {row['cidade']}**")
            st.markdown(f"🗓️ {row['data_hora']}")
            st.markdown(f"🧑 {row['usuario']}")
            st.info(row["descricao"])

with aba_novo:
    st.subheader("📤 Compartilhe como está o clima agora")
    cidade = st.text_input("Cidade")
    descricao = st.text_area("Descreva o clima agora (Ex: Chuva fraca, muito sol, ventania, etc.)")
    if st.button("Enviar Relato"):
        if cidade and descricao:
            post = {
                "usuario": st.session_state.usuario,
                "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "cidade": cidade,
                "descricao": descricao
            }
            salvar_post(post)
            st.success("Relato enviado!")
            st.rerun()
        else:
            st.error("Preencha todos os campos para enviar.")
