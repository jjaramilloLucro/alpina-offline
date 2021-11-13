import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="img/favicon.ico"
)

from dashboard import connection
from dashboard.general import main as general_app
from dashboard.imagenes import main as imagenes_app
from dashboard.visitas import main as visitas_app

db = connection.get_session()
if 'rerun_counter' not in st.session_state:
    st.session_state['rerun_counter'] = 0

usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha = connection.actualizar(db, st.session_state['rerun_counter'])
if 'fecha' not in st.session_state:
    st.session_state['fecha'] = fecha

cols = st.columns((8,3,1))

if cols[2].button("Actualizar"):
  st.session_state['rerun_counter'] += 1
  usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha = connection.actualizar(db, st.session_state['rerun_counter'])
  st.session_state['fecha'] = fecha

cols[1].metric("Ultima Actualización:",st.session_state['fecha'])

pages = {'General':general_app,"Visitas":visitas_app,'Imagenes':imagenes_app}

st.sidebar.image("img/Logo-2.png")
choice = st.sidebar.radio("Menú: ",tuple(pages.keys()))

pages[choice](usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos)



