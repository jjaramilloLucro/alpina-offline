import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="img/favicon.ico"
)

from dashboard import connection
from dashboard.imagenes import main as imagenes_app
from dashboard.visitas import main as visitas_app
from dashboard.infaltables import main as infaltables_app
from dashboard.productos import main as productos_app
from dashboard.tiendas import main as tiendas_app

import pandas as pd

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

if 'auth' not in st.session_state:
	st.session_state['auth'] = None
	fecha = ''
	usuarios = pd.DataFrame()
	challenges = pd.DataFrame()
	respuestas = pd.DataFrame()
	imagenes = pd.DataFrame()
	infaltables = pd.DataFrame()
	faltantes = pd.DataFrame()
	tiendas = pd.DataFrame()
	grupos = pd.DataFrame()
	comentarios = pd.DataFrame()


if st.session_state['auth']:
    usuarios, challenges, respuestas, imagenes, infaltables, faltantes,\
				tiendas, grupos, fecha = connection.carga_inicial()

    cols = st.columns((8,3,1))

    if cols[2].button("Actualizar"):
        respuestas, imagenes, faltantes, fecha = connection.actualizar(respuestas, imagenes, faltantes, fecha)

    cols[1].metric("Ultima Actualización:", fecha.strftime('%d/%h/%Y %I:%M %p'))

    pages = {'Imágenes':imagenes_app, "Visitas":visitas_app, "Infaltables":infaltables_app, "Productos":productos_app, "Tiendas":tiendas_app}

    st.sidebar.image("img/Logo-2.png")
    choice = st.sidebar.radio("Menú: ",tuple(pages.keys()))
    
    pages[choice](usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos)

else:
    cols = st.columns((1,3,1))
    form = cols[1].form("login")
    c = form.empty()
    form.header("Autenticación")
    username = form.text_input("Username")
    password = form.text_input("Password",type="password")

    # Every form must have a submit button.
    submitted = form.form_submit_button("Entrar")
    if submitted:
        if password != 'admin123' or username not in [
            'j.jaramillo','g.lopez','l.parra','a.ramirez',
            'johanna.farias','juan.herrera','c.hernandez',
            'y.aguirre', 'v.ovalle', 'j.jay', 'c.zarate'
            ]:
            c.error("Usuario o contraseña incorrecto.")
        else:
            st.session_state['auth'] = username
            #connection.carga_inicial.clear()
            st.experimental_rerun()