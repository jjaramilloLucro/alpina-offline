import streamlit as st
import pandas as pd
#import plotly.figure_factory as ff

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    #fig = px.line(df, x='date', y="GOOG")
    #st.plotly_chart(fig, use_container_width=True)

    def reset_session_id():
        st.session_state['session_id'] = ''

    if 'session_id' not in st.session_state:
        reset_session_id()
        
    col1, col2, col3 = st.columns(3)
    usuario_selected = col1.multiselect("Usuario", usuarios['name'].unique(),on_change=reset_session_id)

    if usuario_selected:
        usuario_filt = usuarios[usuarios['name'].isin(usuario_selected)]
        filtro_us = respuestas[respuestas['uid'].isin(usuario_filt['username'])] 
    else:
        usuario_filt = usuarios
        filtro_us = respuestas

    filt_tiend = tiendas[tiendas['user_id'].isin(usuario_filt['username'])]
    tienda_selected = col2.multiselect("Tienda", filt_tiend['name'].unique(),on_change=reset_session_id)

    if tienda_selected:
        filtro_us = filtro_us[filtro_us['resp'].isin(tienda_selected)]
        filtro = imagenes[imagenes['session_id'].isin(filtro_us['session_id'])]

    rango = (filtro_us['created_at'].min(), filtro_us['created_at'].max())

    if filtro_us.empty:
        date_selected = col3.date_input("Fecha", None,on_change=reset_session_id)
    else:
        date_selected = col3.date_input("Fecha", rango, min_value= rango[0] , max_value=rango[1],on_change=reset_session_id)
        try:
            inicio, fin = date_selected
        except:
            inicio, fin = date_selected[0], pd.Timestamp('today').floor('D').date() 
        mask = (filtro_us['created_at'].dt.date >= inicio) & (filtro_us['created_at'].dt.date <= fin)
        filtro_us = filtro_us[mask]
    
    filtro = imagenes[imagenes['session_id'].isin(filtro_us['session_id'])]

    col1, col2, col3 = st.columns(3)
    col1.metric("Usuarios", len(usuario_filt))
    col2.metric("Visitas", len(filtro_us), len(filtro_us[filtro_us['created_at'].dt.date >= pd.Timestamp('today').floor('D').date() ]))
    col3.metric("Fotografias", len(filtro), len(filtro[filtro['created_at'].dt.date >= pd.Timestamp('today').floor('D').date()  ]))
    
    if filtro_us.empty:
        date_selected = st.info("No hay información del Usuario.")
        return
    
    t = filtro_us[filtro_us['store']][['session_id','resp']]
    filtro_us = filtro_us.explode("imgs")
    filtro_us.drop(['resp'],inplace=True, axis=1)
    filtro_us = pd.merge(filtro_us, t, how='left', on='session_id')
    filtro_us.dropna(inplace=True, subset=['imgs'])
    union = pd.merge(filtro, filtro_us, how='left', left_on='resp_id', right_on='imgs', suffixes=("_imagen", "_session"))
    union = pd.merge(union, usuarios[['username','name']], how='left', left_on='uid', right_on='username')
    union.sort_values(['updated_at'], ascending=False, inplace=True)

    st.dataframe(union)