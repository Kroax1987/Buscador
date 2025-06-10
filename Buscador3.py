import streamlit as st
import requests
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime
import pytz

# --- CONFIGURAÇÕES ---

OPENWEATHER_API_KEY = "SUA_API_KEY_OPENWEATHER"
FIREBASE_CRED_PATH = "caminho/para/seu/firebase_cred.json"

# Inicializa Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- FUNÇÕES DE AUTENTICAÇÃO ---

def signup_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user.uid, None
    except Exception as e:
        return None, str(e)

def login_user(email, password):
    # Firebase Admin SDK não suporta login diretamente
    # Para simplificar, usaremos login falso via Firestore (não seguro para produção)
    user_ref = db.collection('users').document(email)
    doc = user_ref.get()
    if doc.exists and doc.to_dict().get("password") == password:
        return doc.id, None
    else:
        return None, "Email ou senha incorretos"

def save_user_to_firestore(email, password):
    user_ref = db.collection('users').document(email)
    user_ref.set({"password": password})

# --- FUNÇÕES DO APP DE CLIMA ---

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={OPENWEATHER_API_KEY}&lang=pt_br"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        weather = {
            "cidade": data['name'],
            "pais": data['sys']['country'],
            "temp": data['main']['temp'],
            "umidade": data['main']['humidity'],
            "vento": data['wind']['speed'],
            "descricao": data['weather'][0]['description'].capitalize(),
            "icone": data['weather'][0]['icon'],
            "hora_atual": datetime.utcfromtimestamp(data['dt'] + data['timezone']).strftime('%Y-%m-%d %H:%M:%S')
        }
        return weather
    else:
        return None

def post_message(user_email, mensagem, cidade):
    doc_ref = db.collection("messages").document()
    doc_ref.set({
        "user": user_email,
        "message": mensagem,
        "city": cidade,
        "timestamp": datetime.utcnow()
    })

def get_messages(city):
    msgs_ref = db.collection("messages").where("city", "==", city).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20)
    docs = msgs_ref.stream()
    return [(doc.to_dict()["user"], doc.to_dict()["message"], doc.to_dict()["timestamp"]) for doc in docs]

# --- STREAMLIT UI ---

st.set_page_config(page_title="App Clima Colaborativo", layout="centered")

if "login_state" not in st.session_state:
    st.session_state.login_state = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

st.title("🌦️ App Clima Colaborativo")

if not st.session_state.login_state:
    st.subheader("🔐 Login ou Cadastro")

    tab1, tab2 = st.tabs(["Login", "Cadastro"])

    with tab1:
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Senha", type="password", key="login_password")
        if st.button("Entrar"):
            user, err = login_user(login_email, login_password)
            if user:
                st.session_state.login_state = True
                st.session_state.user_email = login_email
                st.success("Logado com sucesso!")
                st.experimental_rerun()
            else:
                st.error(f"Erro no login: {err}")

    with tab2:
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Senha", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirme a senha", type="password", key="signup_password_confirm")
        if st.button("Cadastrar"):
            if signup_password != signup_password_confirm:
                st.error("As senhas não coincidem.")
            elif len(signup_password) < 6:
                st.error("Senha deve ter ao menos 6 caracteres.")
            else:
                uid, err = signup_user(signup_email, signup_password)
                if uid:
                    save_user_to_firestore(signup_email, signup_password)
                    st.success("Usuário cadastrado com sucesso! Faça login.")
                else:
                    st.error(f"Erro no cadastro: {err}")

else:
    # Usuário logado - Tela principal
    st.sidebar.write(f"Logado como: **{st.session_state.user_email}**")
    if st.sidebar.button("Logout"):
        st.session_state.login_state = False
        st.session_state.user_email = ""
        st.experimental_rerun()

    city = st.text_input("Digite sua cidade para ver o clima:", "Campinas")
    if city:
        weather = get_weather(city)
        if weather:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(f"http://openweathermap.org/img/wn/{weather['icone']}@4x.png")
            with col2:
                st.markdown(f"### {weather['cidade']}, {weather['pais']}")
                st.markdown(f"**{weather['descricao']}**")
                st.markdown(f"Temperatura: {weather['temp']}°C")
                st.markdown(f"Umidade: {weather['umidade']}%")
                st.markdown(f"Vento: {weather['vento']} m/s")
                st.markdown(f"Última atualização: {weather['hora_atual']}")

            st.markdown("---")
            st.subheader("Relatos colaborativos do tempo")
            mensagem = st.text_area("Compartilhe algo sobre o tempo na sua cidade:")
            if st.button("Enviar relato"):
                if mensagem.strip() == "":
                    st.error("Escreva algo antes de enviar.")
                else:
                    post_message(st.session_state.user_email, mensagem, city)
                    st.success("Relato enviado!")

            msgs = get_messages(city)
            for user, msg, ts in msgs:
                ts_local = ts.replace(tzinfo=pytz.UTC).astimezone()
                st.markdown(f"**{user}** - {ts_local.strftime('%d/%m/%Y %H:%M:%S')}")
                st.markdown(f"> {msg}")
                st.markdown("---")
        else:
            st.error("Cidade não encontrada ou problema na API.")
