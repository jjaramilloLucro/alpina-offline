import streamlit as st
import pandas as pd

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    cols = st.columns(2)
    dias = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",4:"Viernes",5:"Sábado",6:"Domingo"}
    day = cols[1].radio(
        label="Día de la semana:",
        options= dias.keys(),
        format_func=lambda x: dias.get(x),
    )
    tiendas_copy = tiendas.copy()
    tiendas_copy = tiendas_copy.explode('day_route')
    tiendas_copy = tiendas_copy[tiendas_copy['zone_id']!='0']
    tiendas_copy = tiendas_copy[tiendas_copy['day_route']==day]

    usuarios_dia = pd.pivot_table(tiendas_copy,'client_id',index='user_id',aggfunc='count')
    otra_col = st.columns(4)
    otra_col[2].metric("Usuarios con Rutero ese día", len(usuarios_dia))
    otra_col[3].metric("Tiendas ese día", usuarios_dia.sum())
    usuarios_dia = usuarios_dia.reset_index()
    
    resp = respuestas.copy()
    resp = respuestas[respuestas['store'] == 'true']
    date_selected = cols[0].date_input("Fecha")
    mask = resp['created_at'].dt.date == date_selected
    user = cols[0].multiselect("Usuario",usuarios_dia['user_id'])
    filtro_us = resp[mask]
    if not user:
        user = usuarios_dia['user_id']
    filtro_us = filtro_us[filtro_us['uid'].isin(user)]
    st.write(len(filtro_us['uid'].unique()))
    st.dataframe(filtro_us)
    st.dataframe(tiendas_copy[tiendas_copy['user_id'].isin(user)])
    otra_col[0].metric("Tiendas Asignadas a ese Usuario", usuarios_dia[usuarios_dia['user_id'].isin(user)].sum()['client_id'])
    otra_col[1].metric("Tiendas Visitadas ese día", len(filtro_us['resp'].unique()))

    usabilidad = pd.pivot_table(filtro_us,'resp',index='uid',aggfunc=lambda x: len(x.unique()))
    usabilidad = usabilidad.reset_index()
    st.write(usabilidad)
    
    a = pd.merge(usuarios_dia,usabilidad, how='outer', left_on='user_id', right_on= 'uid')
    a = a[['user_id','client_id','resp']]
    a = a.fillna(0)
    a['Usabilidad'] = a['resp'] / a['client_id'] * 100
    #a.to_csv('reporte.csv')
    st.write(a)
    st.write(a['Usabilidad'].mean())