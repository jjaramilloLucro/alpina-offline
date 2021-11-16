import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="img/favicon.ico"
)

from dashboard import connection, auxiliar
from dashboard.imagenes import main as imagenes_app
from dashboard.visitas import main as visitas_app

db = connection.get_session()

usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha = connection.carga_inicial(db)
if 'fecha' not in st.session_state:
  st.session_state['fecha'] = fecha

cols = st.columns((8,3,1))

if cols[2].button("Actualizar"):
  respuestas, imagenes, faltantes, fecha = connection.actualizar(db, respuestas, imagenes, faltantes, st.session_state['fecha'])
  st.session_state['fecha'] = fecha

cols[1].metric("Ultima Actualización:",st.session_state['fecha'].strftime('%d/%h/%Y %I:%M %p'))

pages = {"Prueba":None,"Visitas":visitas_app,'Imagenes':imagenes_app}

st.sidebar.image("img/Logo-2.png")
choice = st.sidebar.radio("Menú: ",tuple(pages.keys()))

try:
  pages[choice](usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos)
except:
  pass


