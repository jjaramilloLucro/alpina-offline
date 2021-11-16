import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="img/favicon.ico"
)

from dashboard import connection
from dashboard.imagenes import main as imagenes_app
from dashboard.visitas import main as visitas_app

import pandas as pd

db = connection.get_session()

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

if st.session_state['inicial']:
  st.session_state['usuarios'] , st.session_state['challenges'], st.session_state['respuestas'],\
    st.session_state['imagenes'] , st.session_state['infaltables'], st.session_state['faltantes'],\
     st.session_state['tiendas'] , st.session_state['grupos'], st.session_state['fecha'] = connection.carga_inicial(db)


cols = st.columns((8,3,1))

if cols[2].button("Actualizar"):
  st.session_state['inicial'] = False
  st.session_state['respuestas'], st.session_state['imagenes'], st.session_state['faltantes'], st.session_state['fecha'] = connection.actualizar(db, st.session_state['respuestas'], st.session_state['imagenes'], st.session_state['faltantes'], st.session_state['fecha'])

cols[1].metric("Ultima Actualización:",st.session_state['fecha'].strftime('%d/%h/%Y %I:%M %p'))

pages = {"Visitas":visitas_app,'Imagenes':imagenes_app}

st.sidebar.image("img/Logo-2.png")
choice = st.sidebar.radio("Menú: ",tuple(pages.keys()))

"""
if st.button('Guardar'):
    my_bar = st.progress(0)
    total = len(a)
    #st.write(respuestas)
    c = st.empty()
    try:
        for i,session_id in enumerate(a):
            final, faltantes = api.calculate_faltantes(db, session_id)
            if final:
              api.set_faltantes(db, session_id, faltantes)
            my_bar.progress((i+1)/total)
            c.write(f"Completado {i+1} de {total}.")
    except Exception as e:
        st.exception(e)
        db.rollback()
        st.write(f"Restaurado!!")

"""   

try:
  pages[choice](st.session_state['usuarios'] , st.session_state['challenges'], st.session_state['respuestas'],
                st.session_state['imagenes'] , st.session_state['infaltables'], st.session_state['faltantes'],
                st.session_state['tiendas'] , st.session_state['grupos'])
except:
  pass


