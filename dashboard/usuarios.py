import streamlit as st
import pandas as pd
import numpy as np
from dashboard import auxiliar as aux

lucro = ['Usuario Prueba','Luz Aguirre','Yamile Aguirre','Usuario 0','Juan Camilo Jaramillo','Giovanni Lopez','Carlos Martinez','Johannes Kling','Prueba','Carlos Hernandez','prueba']

def convert_df(df,name):
    return df.to_csv(name,encoding='utf-16',index=False)


def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    st.title("Usuarios")
    us = usuarios.copy()
    us['Activo'] = us['username'].isin(respuestas['uid'].unique())
    us['group'] = us['group'].astype(str).apply(lambda x: eval(x)) 
    us = us.explode("group")
    filtro_us = pd.merge(us, grupos, how='left', left_on='group', right_on='id')
    a = filtro_us.groupby('username').name_y.apply(np.array).reset_index()
    resp = pd.merge(us, a, how='left', on='username')
    resp.drop_duplicates('username',inplace=True)
    t = tiendas.drop_duplicates(['user_id','city'])
    a = t.groupby('user_id').city.apply(np.array).reset_index()
    filtro_us = pd.merge(resp, a, how='left', left_on='username', right_on='user_id')
    
    def join_info(x):
        try:
            return ', '.join(x)
        except:
            return ''

    filtro_us['name_y'] = filtro_us['name_y'].apply(join_info)
    filtro_us['city'] = filtro_us['city'].apply(join_info)
    br = pd.pivot_table(respuestas,'created_at',index='uid',aggfunc='max').reset_index()
    filtro_us = pd.merge(filtro_us, br, how='left', left_on='username', right_on='uid')
    filtro_us['created_at'] = filtro_us['created_at'].dt.strftime('%d-%m-%Y')
    filtro_us['assigned'] = ~filtro_us['user_id'].isna()
    filtro_us = filtro_us.drop(['password','group','version','user_id','uid'],axis=1)
    filtro_us.columns = ['Teléfono','Nombre','Utilizó el App','Grupo','Ciudad','Fecha Último Registro','Rutero Asignado']
    filtro_us = filtro_us[['Teléfono','Nombre','Grupo','Ciudad','Rutero Asignado','Utilizó el App', 'Fecha Último Registro']]
    filtro_us = filtro_us[~filtro_us['Nombre'].isin(lucro)]
    cols = st.columns(3)
    cols[0].metric("Usuarios Registrados",len(filtro_us))
    cols[1].metric("Usuarios Asignados",len(filtro_us[filtro_us['Rutero Asignado']]), delta= '{0:.2f}%'.format(len(filtro_us[filtro_us['Rutero Asignado']])/len(filtro_us) * 100), delta_color='off')
    cols[2].metric("Usuarios Activos",len(filtro_us[filtro_us['Utilizó el App']]), delta= '{0:.2f}%'.format(len(filtro_us[filtro_us['Utilizó el App']])/len(filtro_us) * 100), delta_color='off')
    filtro_us['Rutero Asignado'] = np.where(filtro_us['Rutero Asignado'], 'Si', 'No')
    filtro_us['Utilizó el App'] = np.where(filtro_us['Utilizó el App'], 'Si', 'No')
    st.dataframe(filtro_us)
    cols = st.columns((3,1))
    name = 'usuarios.csv'
    cols[1].download_button('Descargar Información',open(name,'rb'),file_name=name,mime='text/csv',on_click=convert_df, kwargs={"df":filtro_us,"name":name})
    st.title("Imagenes")
    imgs = respuestas.explode("imgs")
    imgs = imgs[~imgs['uid'].isin(lucro)]
    imgs = imgs.dropna()
    rango = (imgs['created_at'].min(), imgs['created_at'].max())

    date_selected = st.date_input("Fecha", rango, min_value= rango[0] , max_value=rango[1])
    try:
        inicio, fin = date_selected
    except:
        inicio, fin = date_selected[0], pd.Timestamp('today').floor('D').date() 
    mask = (imgs['created_at'].dt.date >= inicio) & (imgs['created_at'].dt.date <= fin)
    imgs = imgs[mask]

    imgs['grupo'], imgs['canal'] = zip(*imgs['document_id'].apply(lambda x: x.split("__")))
    imgs['Canal'] = 'Tiendas'
    imgs.loc[(imgs['canal']=="2") | (imgs['canal']=="1"),'Canal'] = 'Canal Moderno'
    cols = st.columns(2)
    cols[0].metric("Tiendas",len(imgs[imgs['Canal']=="Tiendas"]), delta= '{0:.2f}%'.format(len(imgs[imgs['Canal']=="Tiendas"])/len(imgs) * 100), delta_color='off')
    cols[1].metric("Canal Moderno",len(imgs[imgs['Canal']=='Canal Moderno']), delta= '{0:.2f}%'.format(len(imgs[imgs['Canal']=='Canal Moderno'])/len(imgs) * 100), delta_color='off')
    
    cols = st.columns((3,1))
    total = pd.pivot_table(imgs,index='uid',columns='Canal',values='imgs',aggfunc='count').reset_index()
    total.columns = ['Usuario','Canal Moderno','Tiendas']
    cols[0].dataframe(total)

    name = 'imagenes.csv'
    cols[1].download_button('Descargar Información',open(name,'rb'),file_name=name,mime='text/csv',on_click=convert_df, kwargs={"df":total,"name":name})