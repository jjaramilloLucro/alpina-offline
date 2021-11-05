import streamlit as st
st.set_page_config(
  page_title="Dashboard Alpina Offline", layout="wide",
  page_icon="💲"
)



from imagenes import main as imagenes_app
from visitas import main as visitas_app
import dash_auxiliar as aux
#import plotly.express as px

usuarios, challenges, respuestas, imagenes, infaltables, faltantes = aux.carga_inicial()


pages = {'Imagenes':imagenes_app,"Visitas":visitas_app}

choice = st.sidebar.radio("Choice your page: ",tuple(pages.keys()))

pages[choice](usuarios, challenges, respuestas, imagenes, infaltables, faltantes)

