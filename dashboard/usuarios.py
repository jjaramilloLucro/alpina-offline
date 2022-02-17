import streamlit as st
import pandas as pd
import numpy as np
from dashboard import auxiliar as aux

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    us = usuarios.copy()
    st.dataframe(respuestas)
    st.dataframe(us)
    us['Activo'] = us['username'].isin(respuestas['uid'].unique())
    #usuarios[] = True
    us['group'] = us['group'].astype(str).apply(lambda x: eval(x)) 
    
    us = us.explode("group")
    st.dataframe(us)
    filtro_us = pd.merge(us, grupos, how='left', left_on='group', right_on='id')
    st.dataframe(filtro_us)
    a = filtro_us.groupby('username').name_y.apply(np.array).reset_index()
    st.dataframe(a)
    resp = pd.merge(us, a, how='left', on='username')
    resp.drop_duplicates('username',inplace=True)
    st.dataframe(resp)
    #filtro_us = pd.merge(resp, tiendas, how='left', left_on='username', right_on='user_id')
    #st.dataframe(filtro_us)
    t = tiendas.drop_duplicates(['user_id','city'])
    a = t.groupby('user_id').city.apply(np.array).reset_index()
    st.dataframe(a)
    filtro_us = pd.merge(resp, a, how='left', left_on='username', right_on='user_id')
    st.dataframe(filtro_us)
    def join_info(x):
        try:
            return ', '.join(x)
        except:
            return ''

    filtro_us['name_y'] = filtro_us['name_y'].apply(join_info)
    filtro_us['city'] = filtro_us['city'].apply(join_info)
    st.dataframe(filtro_us)
    filtro_us.to_csv('usuarios.csv',encoding='utf-16',index=False)
    st.download_button('Descargar Información',filtro_us.to_csv('usuarios.csv',encoding='utf-16',index=False),'usuarios.csv',mime='text/csv')
    
    
