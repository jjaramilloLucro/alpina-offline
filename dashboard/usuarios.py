import streamlit as st
import pandas as pd
import numpy as np
from dashboard import auxiliar as aux
import base64
from io import BytesIO

lucro = ['0','3202786141','3167568073','000','3133854997','3108743939','3102204572','3102714096','prueba','3158678002']

def convert_df(df,name):
    return df.to_csv(name,encoding='utf-16',index=False)


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data

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
    filtro_us = filtro_us.drop(['password','group','version','user_id','uid','isActive','role'],axis=1)
    filtro_us.columns = ['Teléfono','Nombre','Utilizó el App','Grupo','Ciudad','Fecha Último Registro','Rutero Asignado']
    filtro_us = filtro_us[['Teléfono','Nombre','Grupo','Ciudad','Rutero Asignado','Utilizó el App', 'Fecha Último Registro']]
    filtro_us = filtro_us[~filtro_us['Teléfono'].isin(lucro)]
    
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
    imgs = respuestas.copy()
    imgs = imgs[~imgs['uid'].isin(lucro)]
    imgs = imgs.explode("imgs")
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
    
    imgs = pd.merge(imgs, imagenes, how='left', left_on='imgs', right_on='resp_id')
    imgs = imgs.dropna(subset=['original_url'])
    imgs = imgs[imgs['error'].isna()]
    
    cols = st.columns(2)
    cols[0].metric("Tiendas",len(imgs[imgs['Canal']=="Tiendas"]), delta= '{0:.2f}%'.format(len(imgs[imgs['Canal']=="Tiendas"])/len(imgs) * 100), delta_color='off')
    cols[1].metric("Canal Moderno",len(imgs[imgs['Canal']=='Canal Moderno']), delta= '{0:.2f}%'.format(len(imgs[imgs['Canal']=='Canal Moderno'])/len(imgs) * 100), delta_color='off')
    cols = st.columns((3,1))
    temp = pd.pivot_table(imgs,index='uid',columns='Canal',values='imgs',aggfunc='count').reset_index()
    total = pd.DataFrame(columns=['Usuario','Canal Moderno','Tiendas'])
    total['Usuario'] = temp['uid']
    try:
        total['Tiendas'] = temp['Tiendas']
    except:
        total['Tiendas'] = 0
    try:
        total['Canal Moderno'] = temp['Canal Moderno']
    except:
        total['Canal Moderno'] = 0
    cols[0].dataframe(total)
    """
    df_xlsx = to_excel(total)
    
    cols[1].download_button(label='📥 Download Current Result',
                                data=df_xlsx ,
                                file_name= 'imagenes.xlsx')
    """
    name = 'imagenes.csv'
    cols[1].download_button('Descargar Información',open(name,'rb'),file_name=name,mime='text/csv',on_click=convert_df, kwargs={"df":total,"name":name})
    
    