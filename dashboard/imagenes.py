from datetime import datetime
import streamlit as st
import pandas as pd
from dashboard import auxiliar as aux
from datetime import datetime
import plotly.express as px

def main(usuarios, challenges, respuestas_original, imagenes, infaltables, faltantes, tiendas, grupos):
    def reset_session_id():
        st.session_state['session_id'] = ''
        st.session_state['resp_id'] = ''
        st.session_state['detail'] = ''

    if 'session_id' not in st.session_state:
        reset_session_id()

    respuestas = respuestas_original.copy()

    today = datetime.today()
    actual = (today, today )
    rango = (respuestas['created_at'].min().to_pydatetime(), respuestas['created_at'].max().to_pydatetime())

    usuario_filt = usuarios.copy()
    filtro_us = respuestas.copy()

    col1, col2, col3, col4, col5 = st.columns(5)
    usuario_selected = col1.multiselect("Usuario", usuarios['name'].unique(),on_change=reset_session_id)
    respuestas['challenge_id'] = respuestas['document_id'].apply(lambda x: x.split('__')[1])

    if usuario_selected:
        usuario_filt = usuarios[usuarios['name'].isin(usuario_selected)]
        filtro_us = filtro_us[filtro_us['uid'].isin(usuario_filt['username'])] 
    else:
        usuario_filt = usuarios
        filtro_us = filtro_us

    usuario_role = col2.multiselect("Rol", usuarios['role'].unique(),on_change=reset_session_id)

    if usuario_role:
        usuario_filt = usuarios[usuarios['role'].isin(usuario_role)]
        filtro_us = filtro_us[filtro_us['uid'].isin(usuario_filt['username'])] 


    canal_selected = col3.multiselect("Canal", challenges['name'].values,on_change=reset_session_id)
    if canal_selected:
        canal_filt = challenges[challenges['name'].isin(canal_selected)].astype(str)
        filtro_us = filtro_us[filtro_us['challenge_id'].isin(canal_filt['challenge_id'].values)]

    filt_tiend = tiendas[tiendas['user_id'].isin(usuario_filt['username'])][['client_id','name','user_id']]
    dict_tienda = {str(x['client_id']):str(x['client_id']) + ' - ' + str(x['name']) for _, x in filt_tiend.iterrows()}
    tienda_selected = col4.multiselect("Tienda", dict_tienda.keys(), None, format_func=lambda x: dict_tienda.get(x), on_change=reset_session_id)
    t = filtro_us[['session_id','store']].drop_duplicates()
    t['store_name'] = t['store'].apply(lambda x: dict_tienda.get(x))

    if tienda_selected:
        filtro_us = filtro_us[filtro_us['store'].isin(tienda_selected)]

    if filtro_us.empty:
        date_selected = col5.date_input("Fecha", None,on_change=reset_session_id)
        st.info("No hay información del Usuario.")
        return
    else:
        date_selected = col5.date_input("Fecha", actual, min_value= rango[0], max_value=actual[1], on_change=reset_session_id)
        if len(date_selected) > 1:
            inicio, fin = date_selected
            mask = (filtro_us['created_at'].dt.date >= inicio) & (filtro_us['created_at'].dt.date <= fin)
            filtro_us = filtro_us[mask]
    
    filtro = imagenes[imagenes['session_id'].isin(filtro_us['session_id'])]

    col1, col2, col3 = st.columns(3)
    col1.metric("Usuarios", len(usuario_filt))
    col2.metric("Visitas", len(filtro_us['session_id'].unique()))
    col3.metric("Fotografias", len(filtro))
    
    if filtro.empty:
        st.info("No hay información del Usuario.")
        return
    
    filtro_us = filtro_us.explode("imgs")

    #filtro_us.drop(['resp'],inplace=True, axis=1)
    filtro_us = pd.merge(filtro_us, t, how='left', on='session_id')
    filtro_us.dropna(inplace=True, subset=['imgs'])
    union = pd.merge(filtro, filtro_us, how='left', left_on='resp_id', right_on='imgs', suffixes=("_imagen", "_session"))
    union = pd.merge(union, usuarios[['username','name']], how='left', left_on='uid', right_on='username')
    union.sort_values(['created_at_imagen'], ascending=False, inplace=True)
    

    def write_map_slicer():
        inicio = list(range(1,len(union)+1,10))
        fin = list(range(10,len(union),10))
        fin.append(len(union))
        rango = [str(x[0]) + ' - '+str(x[1]) for x in zip(inicio,fin)]
        if len(rango) > 1:
            values = st.select_slider("Cantidad de Imágenes",rango)
            values = values.split(" - ")
        else:
            values = [min(1,len(union)),max(1,len(union))]

        st.write(f"Mostrando {values[0]} - {values[1]} de {len(union)} imágenes.")

        return values

    union['recon'] = union['data'].apply(lambda x: not(x==[] or not x))
    if st.checkbox("Errores de Máquina"):
        union_copy = union.copy()
        no_recon = 1 - union_copy['recon'].astype(int)
        no_rec = no_recon.sum()

        if no_rec <= 0:
            st.metric("Imágenes no Reconocidas", no_rec, delta= '{0:.2f}%'.format(no_rec/len(union_copy) * 100), delta_color='off')
            
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Imágenes no Reconocidas", no_rec, delta= '{0:.2f}%'.format(no_rec.sum()/len(union_copy) * 100), delta_color='off')
            bt1 = col1.button("Ver Imagenes no Reconocidas", on_click = reset_session_id )
            if bt1:
                union_copy = union_copy[union_copy['mark_url'].isna()]
                btn = st.button("Ver Todas las Imágenes")
            recon = union_copy[~union_copy['error'].isna()]
            col3.metric("Errores de la Máquina de Reconocimiento", len(recon), delta= '{0:.2f}%'.format(len(recon)/no_rec * 100), delta_color='off')
            if not recon.empty:
                bt2 = col3.button("Ver Errores de Máquina", on_click = reset_session_id )
                if bt2:
                    union = recon
                    btn = st.button("Ver Todas las Imágenes")
            serv = union_copy[union_copy['original_url'].isna()]
            col2.metric("Errores del Servidor", len(serv), delta= '{0:.2f}%'.format(len(serv)/no_rec * 100), delta_color='off')
            if not serv.empty:
                bt3 = col2.button("Ver Errores de Servidor", on_click = reset_session_id )
                if bt3:
                    union = serv
                    btn = st.button("Ver Todas las Imágenes")
            basura = union_copy[(~union_copy['mark_url'].isna()) & (no_recon.astype(bool))]
            col4.metric("Imagenes sin Reconocimiento", len(basura), delta= '{0:.2f}%'.format(len(basura)/no_rec * 100), delta_color='off')
            if not basura.empty:  
                bt4 = col4.button("Ver Imagenes sin Reconocimiento", on_click = reset_session_id )
                if bt4:
                    union = basura
                    btn = st.button("Ver Todas las Imágenes")
        
    else:
        union = union[union['recon']]

    union.reset_index(drop=True, inplace=True)
    if st.session_state['session_id'] == '':
        a = union
    else:
        a = union[union['session_id_imagen']==st.session_state['session_id']]
    total = union.dropna(subset=['lat','lon','name'])
    total = total[total['lat']>0]
    total.rename(columns={'name':'Nombre','store':'Tienda'},inplace=True)
    total['Fecha'] = total['created_at_session'].dt.strftime('%d/%h/%Y %I:%M %p')
    #st.dataframe(total[total['Nombre'].isna()])

    fig = px.scatter_mapbox(total, lat="lat", lon="lon", 
                color="Nombre",
                hover_name="username", hover_data=["Nombre", "Fecha", "resp_id"],
                )                
    fig.update_layout(mapbox_style="carto-positron")    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig,use_container_width=True)

    def mostrar_marcaciones_imagen(document_id, session_id):
        st.session_state['resp_id'] = document_id
        st.session_state['session_id'] = session_id

    c = st.container()

    values = write_map_slicer()

    for _, row in union.loc[int(values[0])-1:int(values[1]),:].iterrows():
        col1, col2, col3 = st.columns((1, 1, 2))
        try:
            f = row['created_at_imagen'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p') + ' - ' + row['updated_at'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p')
            mark_error = "No hubo marcación"
            info_error = "No hubo reconocimiento"
        except:
            f = row['created_at_imagen'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p') + ' - '
            mark_error = "No ha terminado de procesar"
            info_error = "No ha terminado de procesar"
        try:
            col1.image(row['original_url'], width=300)
        except:
            col1.markdown(f"No se puede ver la imagen <{row['original_url']}>")
        try:
            col2.image(row['mark_url'], width=300)
        except:
            col2.info(mark_error)
        try:
            data = pd.DataFrame(row['data'])
            col3.markdown(f"""
            **Session_id:** {row['resp_id']}<br>
            **Fotógrafo(a):** {row['name']}<br>
            **Fecha:** {f}<br>
            **Tienda:** {row['store_name']}
            """,True)
            if data.empty:
                col3.info(info_error)
                if row['error']:
                    col3.warning(row['error'])
            else:
                data['score'] = (data['score']*100).map('{0:.2f}%'.format)
                col3.button("Ver detalle",on_click= mostrar_marcaciones_imagen,  kwargs  = {"document_id":str(row['resp_id']), "session_id":str(row['session_id_imagen'])}, key= row['resp_id'])
                col3.dataframe(data[['obj_name','score']])
        except Exception as e:
            col3.markdown(f"""
            **Session_id:** {row['resp_id']}<br>
            **Fotógrafo(a):** {row['name']}<br>**Tienda:** {row['store_name']}
            """,True)
            col3.exception(e)

    def mostrar_prod_y_marc(dataframe, url, cols):
        prod_selected = cols[1].multiselect("", dataframe['obj_name'].unique())
        if prod_selected:
            dataframe = dataframe[dataframe['obj_name'].isin(prod_selected)]
        
        img, colors = aux.marcar_imagen(url,dataframe,st.session_state['resp_id'])
        cols[0].image(img)
        dataframe.rename(columns={"obj_name": "Producto"},inplace=True)
        dataframe.loc[:,'Color'] = ''
        cat = dataframe.drop_duplicates(subset=['Producto'])[['Color','Producto']]
        dataframe.loc[:,'Color'] = ''
        dataframe.loc[:,'score'] = (dataframe['score']*100).map('{0:.2f}%'.format)
        dataframe = dataframe[['Color','Producto','score']]

        def highlight_cols(x):
            #copy df to new - original data are not changed
            df = x.copy()
            df.loc[:,:] = ''
            df['Color'] =  x['Producto'].apply(lambda x:"background-color: #{:02x}{:02x}{:02x}".format(colors[x][0],colors[x][1],colors[x][2]) )

            #overwrite values grey color
            #return color df
            return df

        
        cols[1].dataframe(cat.style.apply(highlight_cols, axis=None))
        cols[1].write("Productos")
        cols[1].dataframe(dataframe.style.apply(highlight_cols, axis=None))

    def detail_detalle(val):
        st.session_state['detail'] = val
    
    def mostrar_detalle(container, dataframe):
        url = dataframe['original_url'].values
        dataframe = dataframe.explode('data')
        dataframe = pd.json_normalize(dataframe['data'])
        cols = container.columns(6)
        #cols[0].write(dataframe)
        cols[0].metric("Número de Detecciones", len(dataframe))
        cols[1].metric("Número de Productos", len(dataframe['obj_name'].unique()))
        others = dataframe[dataframe["obj_name"].str.lower().str.contains("other", na=False)]
        cols[2].metric("Número de Detecciones 'Other'", len(others))
        cols[3].metric("Número de Productos 'Other'", len(others['obj_name'].unique()))
        umbral = cols[4].slider("Umbral de Reconocimiento", value=0.95,format = "%f")
        debajo = dataframe[dataframe['score']<umbral]
        cols[5].metric("Productos debajo del Umbral", len(debajo['obj_name'].unique()))
        cols[1].button("Ver Productos",key=0, on_click= detail_detalle,kwargs  = {"val":'todo'})
        cols[5].button("Ver Productos",key=1, on_click= detail_detalle,kwargs  = {"val":'deb'})
        cols[3].button("Ver Others", on_click= detail_detalle, kwargs  = {"val":'oth'})
        container.markdown("*****")
        cols = container.columns((2, 1))
        if st.session_state['detail'] == 'deb':
            cols[1].write("Productos debajo del Umbral:")
            mostrar_prod_y_marc(debajo, url[0], cols)
        elif st.session_state['detail'] == 'oth':
            cols[1].write("Productos Others:")
            dataframe = others
            mostrar_prod_y_marc(others, url[0], cols)
        else:
            cols[1].write("Productos reconocidos:")
            mostrar_prod_y_marc(dataframe, url[0], cols)


    if st.session_state['resp_id'] == '':
        c.write("")
    else:
        a = union[union['resp_id']==st.session_state['resp_id']]
        c.markdown("*****")
        c.subheader(f"Detalle - {st.session_state['resp_id']}",'detail')
        mostrar_detalle(c,a)
        c.markdown("*****")
