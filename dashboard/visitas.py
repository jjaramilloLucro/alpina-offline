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

    
    #visitas = filtro['session_id'].unique()
    visitas = filtro_us.explode('respuestas')
    visitas2 = pd.json_normalize(visitas['respuestas'])
    visitas = pd.concat([visitas.reset_index(drop=True), visitas2.reset_index(drop=True)], axis=1)
    visitas.fillna('',inplace=True)
    visitas = visitas.explode('imgs')[['document_id','session_id','created_at','uid','tienda','lat','lon','id_preg','imgs']]
    visitas.dropna(inplace=True)
    visitas.sort_values(['created_at'], ascending=False, inplace=True)
    visitas = pd.merge(visitas, usuarios[['username','nombre']], how='left', left_on='uid', right_on='username')
    def extract_name_title(document_id,id_preg):
        challenge = challenges[challenges['document_id']==document_id]
        task = challenge.explode('tasks')
        task = pd.json_normalize(task['tasks'])
        preg = task[task['id']==id_preg]

        return challenge['name'].values[0], preg['title'].values[0]

    visitas['nombre_tienda'], visitas['title'] = zip(*visitas.apply(lambda x: extract_name_title(x['document_id'], x['id_preg']), axis=1))
    visitas['visita'] = visitas['nombre'] + ' - ' + visitas['tienda'] + ' - ' + visitas['created_at'].dt.strftime('%d/%h/%Y %I:%M %p') + " ("+ visitas['session_id'] + ")"
    """
    cols = st.columns(3)
    a = visitas.drop_duplicates(subset=['visita', 'session_id'], keep='first')[['visita', 'session_id','uid']]
    cols[0].dataframe(a)
    cols[0].write(a.shape)
    a = visitas.drop_duplicates(subset=['visita'], keep='first')[['visita', 'session_id','uid']]
    cols[1].dataframe(a)
    cols[1].write(a.shape)
    """
    cols = st.columns((4,1,1,1,1,1))
    visita_selected = cols[0].multiselect("Visita", visitas['visita'].unique(),on_change=reset_session_id)
    if visita_selected:
        visitas = visitas[visitas['visita'].isin(visita_selected)]
    
    cols[2].metric("Usuarios", len(visitas['uid'].unique()))
    cols[3].metric("Visitas", len(visitas['session_id'].unique()))
    cols[5].metric("Fotografias", len(visitas['imgs'].unique()))

    vis = visitas['visita'].unique()
    def write_slicer():
        inicio = list(range(1,len(vis)+1,10))
        fin = list(range(10,len(vis),10))
        fin.append(len(vis))
        rango = [str(x[0]) + ' - '+str(x[1]) for x in zip(inicio,fin)]
        if len(rango) > 1:
            values = st.select_slider("Cantidad de Visitas",rango)
            values = values.split(" - ")
        else:
            values = [min(1,len(vis)),max(1,len(vis))]

        st.write(f"Mostrando {values[0]} - {values[1]} de {len(vis)} visitas.")

        return values
    #no_ter = faltantes[visitas['session_id'].unique()]
    values = write_slicer()
    for visita in vis[int(values[0])-1:int(values[1])]:
        v = visitas[visitas['visita'] == visita]
        session = v['session_id'].values[0]
        v = pd.merge(v[['imgs','nombre_tienda','tienda','title','lat','lon','session_id','uid','nombre','created_at']], imagenes[['updated_at','document_id','url_marcada','url_original','error','data']], 
            how='left', left_on='imgs', right_on='document_id')
        
        with st.expander(f"Visita: {visita}"):
            seccion = v['title'].unique()
            try:
                falt = faltantes.loc[session,'faltantes']
                st.header("Faltantes")
                st.dataframe(falt)
            except:
                st.header("Faltantes")
                st.warning("No hay faltantes para esta visita")
            for s in seccion:
                defin = v[v['title']==s]
                st.header("Imagenes")
                st.subheader(s)
                for i, row in defin.iterrows():
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
                    **Fotógrafo(a):** {row['nombre']}<br>
                    **Fecha:** {row['updated_at'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p')}<br>
                    """,True)
                    if data.empty:
                        col3.info("No hubo reconocimiento")
                        if row['error']:
                            col3.warning(row['error'])
                    else:
                        data['score'] = (data['score']*100).map('{0:.2f}%'.format)
                        col3.dataframe(data[['obj_name','score']])
    
    #cols[4].metric("Visitas No Guardadas", len(no_ter), delta= '{0:.2f}%'.format(len(no_ter)/len(visitas['session_id'].unique()) * 100), delta_color='off')
    #cols[4].dataframe(no_ter)