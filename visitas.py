import streamlit as st
import pandas as pd

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes):
    def reset_session_id():
        st.session_state['session_id'] = ''

    if 'session_id' not in st.session_state:
        reset_session_id()

    col1, col2, col3 = st.columns(3)
    usuario_selected = col1.multiselect("Usuario", usuarios['nombre'].unique(),on_change=reset_session_id)


    if usuario_selected:
        usuario_filt = usuarios[usuarios['nombre'].isin(usuario_selected)] 
        filtro_us = respuestas[respuestas['uid'].isin(usuario_filt['username'])] 
    else:
        usuario_filt = usuarios
        filtro_us = respuestas

    tienda_selected = col2.multiselect("Tienda", filtro_us['tienda'].unique(),on_change=reset_session_id)


    if tienda_selected:
        filtro_us = filtro_us[filtro_us['tienda'].isin(tienda_selected)]
        filtro = imagenes[imagenes['resp_id'].isin(filtro_us['session_id'])]

    elif usuario_selected:
        filtro = imagenes[imagenes['resp_id'].isin(filtro_us['session_id'])]
    else:
        filtro = imagenes

    rango = (filtro['created_at'].min(), filtro['created_at'].max())
    date_selected = col3.date_input("Fecha", rango, min_value= rango[0] , max_value=rango[1],on_change=reset_session_id)
    try:
        inicio, fin = date_selected
    except:
        inicio, fin = date_selected[0], pd.Timestamp('today').floor('D').date() 
    mask = (filtro_us['created_at'].dt.date >= inicio) & (filtro_us['created_at'].dt.date <= fin)
    filtro_us = filtro_us[mask]
    filtro = imagenes[imagenes['resp_id'].isin(filtro_us['session_id'])]

    
    #visitas = filtro['session_id'].unique()
    visitas = filtro_us.explode('respuestas')
    visitas2 = pd.json_normalize(visitas['respuestas'])
    visitas = pd.concat([visitas.reset_index(drop=True), visitas2.reset_index(drop=True)], axis=1)
    visitas.fillna('',inplace=True)
    tiendas = visitas.explode('resp')[['session_id','resp']]
    tiendas.dropna(inplace=True)
    visitas = visitas.explode('imgs')[['document_id','session_id','created_at','uid','tienda','lat','lon','id_preg','imgs']]
    visitas = pd.merge(visitas, tiendas, how='left', on='session_id')
    tiendas.dropna(inplace=True)
    st.dataframe(visitas)
    st.write(visitas.shape)
    
    st.dataframe(tiendas)
    st.write(tiendas.shape)
    st.dataframe(pd.pivot_table(filtro_us,values='tienda',index='session_id',aggfunc='count'))
    st.dataframe(pd.pivot_table(visitas,values='imgs',index='session_id',aggfunc='count'))
    