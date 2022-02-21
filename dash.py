import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="img/favicon.ico"
)

from dashboard import connection
from dashboard.imagenes import main as imagenes_app
from dashboard.visitas import main as visitas_app
from dashboard.infaltables import main as infaltables_app
from dashboard.usuarios import main as usuarios_app

import pandas as pd

db = connection.get_session()

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

if 'inicial' not in st.session_state:
  st.session_state['inicial'] = True
  st.session_state['fecha'] = ''
  st.session_state['usuarios'] = pd.DataFrame()
  st.session_state['challenges'] = pd.DataFrame()
  st.session_state['respuestas'] = pd.DataFrame()
  st.session_state['imagenes'] = pd.DataFrame()
  st.session_state['infaltables'] = pd.DataFrame()
  st.session_state['faltantes'] = pd.DataFrame()
  st.session_state['tiendas'] = pd.DataFrame()
  st.session_state['grupos'] = pd.DataFrame()
  st.session_state['auth'] = False

if st.session_state['inicial']:
  st.session_state['usuarios'] , st.session_state['challenges'], st.session_state['respuestas'],\
    st.session_state['imagenes'] , st.session_state['infaltables'], st.session_state['faltantes'],\
     st.session_state['tiendas'] , st.session_state['grupos'], st.session_state['fecha'] = connection.carga_inicial(db)


if st.session_state['auth']:

  cols = st.columns((8,3,1))

  if cols[2].button("Actualizar"):
    st.session_state['inicial'] = False
    st.session_state['respuestas'], st.session_state['imagenes'], st.session_state['faltantes'], st.session_state['fecha'] = connection.actualizar(db, st.session_state['respuestas'], st.session_state['imagenes'], st.session_state['faltantes'], st.session_state['fecha'])

  cols[1].metric("Ultima Actualización:",st.session_state['fecha'].strftime('%d/%h/%Y %I:%M %p'))

  pages = {"Usuarios":usuarios_app,"Visitas":visitas_app,'Imagenes':imagenes_app, "Infaltables":infaltables_app}

  st.sidebar.image("img/Logo-2.png")
  choice = st.sidebar.radio("Menú: ",tuple(pages.keys()))

  try:
    pages[choice](st.session_state['usuarios'] , st.session_state['challenges'], st.session_state['respuestas'],
                  st.session_state['imagenes'] , st.session_state['infaltables'], st.session_state['faltantes'],
                  st.session_state['tiendas'] , st.session_state['grupos'])
  except:
    pass

else:
  cols = st.columns((1,3,1))
  form = cols[1].form("my_form")
  c = form.empty()
  form.header("Autenticación")
  username = form.text_input("Username")
  password = form.text_input("Password",type="password")

  # Every form must have a submit button.
  submitted = form.form_submit_button("Entrar")
  if submitted:
    if password != 'admin123':
      c.error("Usuario o contraseña incorrecto.")
    else:
      st.session_state['auth'] = True
      st.experimental_rerun()
