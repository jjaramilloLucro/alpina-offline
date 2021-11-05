import streamlit as st
import pandas as pd
import dash_auxiliar as aux

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
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Usuarios", len(usuario_filt))
    col2.metric("Visitas", len(filtro_us), len(filtro_us[filtro_us['created_at'].dt.date >= pd.Timestamp('today').floor('D').date() ]))
    col3.metric("Fotografias", len(filtro), len(filtro[filtro['created_at'].dt.date >= pd.Timestamp('today').floor('D').date()  ]))

    union = pd.merge(filtro, filtro_us, how='left', left_on='resp_id', right_on='session_id', suffixes=("_imagen", "_session"))
    union = pd.merge(union, usuarios[['username','nombre']], how='left', left_on='uid', right_on='username')
    union.sort_values(['updated_at'], ascending=False, inplace=True)

    def write_map_slicer():
        inicio = list(range(1,len(union)+1,10))
        fin = list(range(10,len(union),10))
        fin.append(len(union))
        rango = [str(x[0]) + ' - '+str(x[1]) for x in zip(inicio,fin)]
        if len(rango) > 1:
            values = st.select_slider("Cantidad de Imágenes",rango)
            values = values.split(" - ")
        else:
            values = [min(1,len(union)),len(union)]

        st.write(f"Mostrando {values[0]} - {values[1]} de {len(union)} imágenes.")

        return values

    no_rec = int(union['url_marcada'].isna().sum())

    if no_rec <= 0:
        st.metric("Imágenes no Reconocidas", no_rec, delta= '{0:.2f}%'.format(no_rec/len(union) * 100), delta_color='off')
        
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Imágenes no Reconocidas", no_rec, delta= '{0:.2f}%'.format(no_rec/len(union) * 100), delta_color='off')
        recon = union[union['error']=="No hubo reconocimiento"]
        col2.metric("Errores de la Máquina de Reconocimiento", len(recon), delta= '{0:.2f}%'.format(len(recon)/no_rec * 100), delta_color='off')
        serv = union[(union['error']!="No hubo reconocimiento") & (union['error'].notnull())]
        col3.metric("Errores del Servidor", len(serv), delta= '{0:.2f}%'.format(len(serv)/no_rec * 100), delta_color='off')
        basura = union[(union['url_marcada'].isna()) & (union['error'].isna())]
        col4.metric("Imagenes sin Reconocimiento", len(basura), delta= '{0:.2f}%'.format(len(basura)/no_rec * 100), delta_color='off')
            
        bt1 = col1.button("Ver Imagenes no Reconocidas", on_click = reset_session_id )
        bt2 = col2.button("Ver Errores de Máquina", on_click = reset_session_id )
        bt3 = col3.button("Ver Errores de Servidor", on_click = reset_session_id )
        bt4 = col4.button("Ver Imagenes sin Reconocimiento", on_click = reset_session_id )

        if bt1:
            union = union[union['url_marcada'].isna()]
            btn = st.button("Ver Todas las Imágenes")
        if bt2:
            union = recon
            btn = st.button("Ver Todas las Imágenes")
        if bt3:
            union = serv
            btn = st.button("Ver Todas las Imágenes")
        if bt4:
            union = basura
            btn = st.button("Ver Todas las Imágenes")

    union.reset_index(drop=True, inplace=True)
    if st.session_state['session_id'] == '':
        a = union
    else:
        s_id = st.session_state['session_id'].split("-")[0]
        a = union[union['session_id']==s_id]

    respuestas = a[['document_id_imagen','session_id','respuestas']].explode('respuestas')
    imgs = pd.json_normalize(respuestas['respuestas'])
    imgs = imgs.explode('imgs').dropna()
    total = pd.merge(respuestas, imgs[['lat','lon','imgs']], how='left', left_on='document_id_imagen', right_on='imgs')
    total['lat'] = pd.to_numeric(total['lat'],downcast='float')
    total['lon'] = pd.to_numeric(total['lon'],downcast='float')
    total = total.dropna()

    st.map(total)

    def mostrar_marcaciones_imagen(document_id):
        st.session_state['session_id'] = document_id
    c = st.container()

    values = write_map_slicer()

    for index, row in union.loc[int(values[0])-1:int(values[1]),:].iterrows():
        col1, col2, col3 = st.columns((1, 1, 2))
        try:
            col1.image(row['url_original'], width=300)
        except:
            col1.markdown(f"No se puede ver la imagen <{row['url_original']}>")
        try:
            col2.image(row['url_marcada'], width=300)
        except:
            col2.info("No hubo marcación")
        data = pd.DataFrame(row['data'])
        col3.markdown(f"""
        **Session_id:** {row['document_id_imagen']}<br>
        **Fotógrafo(a):** {row['nombre']}<br>
        **Fecha:** {row['created_at_imagen'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p')} - {row['updated_at'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p')}<br>
        **Tienda:** {row['tienda']}
        """,True)
        if data.empty:
            col3.info("No hubo reconocimiento")
            if row['error']:
                col3.warning(row['error'])
        else:
            data['score'] = (data['score']*100).map('{0:.2f}%'.format)
            col3.button("Ver detalle",on_click= mostrar_marcaciones_imagen,  kwargs  = {"document_id":str(row['document_id_imagen'])}, key= row['document_id_imagen'])
            col3.dataframe(data[['obj_name','score']])

    def mostrar_detalle(container, dataframe):
        url = dataframe['url_original'].values
        dataframe = dataframe.explode('data')
        dataframe = pd.json_normalize(dataframe['data'])
        cols = container.columns((2, 1, 1))
        #cols[0].write(dataframe)
        cols[1].metric("Número de Detecciones", len(dataframe))
        cols[1].metric("Número de Productos", len(dataframe['obj_name'].unique()))
        others = dataframe[dataframe["obj_name"].str.lower().str.contains("other", na=False)]
        cols[2].metric("Número de Detecciones 'Other'", len(others))
        cols[2].metric("Número de Productos 'Other'", len(others['obj_name'].unique()))
        umbral = cols[1].slider("Umbral de Reconocimiento", value=0.95,format = "%f")
        debajo = dataframe[dataframe['score']<umbral]
        cols[2].metric("Productos debajo del Umbral", len(debajo['obj_name'].unique()))
        bt_deb = cols[2].button("Ver Productos")
        bt_otr = cols[2].button("Ver Others")
        if bt_deb:
            img, colors = aux.marcar_imagen(url[0],debajo,st.session_state['session_id'])
            cols[2].write("Productos debajo del Umbral:")
            cols[2].dataframe(debajo)
        elif bt_otr:
            img, colors = aux.marcar_imagen(url[0],others,st.session_state['session_id'])
            cols[2].write("Productos Others:")
            cols[2].dataframe(others)
        else:
            img, colors = aux.marcar_imagen(url[0],dataframe,st.session_state['session_id'])
        cols[0].image(img)
        cols[1].write("Productos reconocidos:")
        cols[1].dataframe(dataframe)

    if st.session_state['session_id'] == '':
        c.write("")
    else:
        a = union[union['document_id_imagen']==st.session_state['session_id']]
        c.markdown("*****")
        c.subheader(f"Detalle - {st.session_state['session_id']}",'detail')
        mostrar_detalle(c,a)
        c.markdown("*****")
