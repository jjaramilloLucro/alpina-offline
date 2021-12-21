import streamlit as st
import pandas as pd

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    st.write(infaltables)
    st.write(grupos)
    a = pd.join(infaltables,grupos[['id','name']], how='left', left_on='group_id', right_on= 'id')

    st.write(a)
        

