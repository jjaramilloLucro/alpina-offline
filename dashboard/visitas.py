import streamlit as st
import pandas as pd

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
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

    if filtro_us.empty:
        st.info("No hay información del Usuario.")
        return

    t = filtro_us[filtro_us['store']][['session_id','resp']]
    filtro_us = filtro_us.explode("imgs")
    filtro_us.drop(['resp'],inplace=True, axis=1)
    filtro_us = pd.merge(filtro_us, t, how='left', on='session_id')
    filtro_us.dropna(inplace=True, subset=['imgs'])
    visitas = pd.merge(filtro_us, usuarios[['username','name']], how='left', left_on='uid', right_on='username')
    visitas.sort_values(['created_at'], ascending=False, inplace=True)

    def extract_name_title(document_id,id_preg):
        group_id = document_id.split('__')[0]
        group = grupos[grupos['id']==int(group_id)]
        challenge_id = document_id.split('__')[1]
        challenge = challenges[challenges['challenge_id']==int(challenge_id)]
        task = challenge.explode('tasks')
        task = pd.json_normalize(task['tasks'])
        preg = task[task['id']==id_preg]

        return group['name'].values[0], preg['title'].values[0]
    visitas['nombre_desafio'], visitas['title'] = zip(*visitas.apply(lambda x: extract_name_title(x['document_id'], x['id_task']), axis=1))
    visitas.fillna({'resp':''},inplace=True)
    visitas['visita'] = visitas['name'] + ' - ' + visitas['resp'] + " ("+ visitas['session_id'] + ")"

    col = st.columns((4,1,1,1,1,1))
    visita_selected = col[0].multiselect("Visita", visitas['visita'].unique(),on_change=reset_session_id)
    if visita_selected:
        visitas = visitas[visitas['visita'].isin(visita_selected)]
    
    col[2].metric("Usuarios", len(visitas['uid'].unique()))
    col[3].metric("Visitas", len(visitas['session_id'].unique()))
    fal = faltantes.reset_index()
    fal = fal[fal['session_id'].isin(visitas['session_id'].unique())]
    cont = len(visitas['session_id'].unique()) - len(fal)
    col[4].metric("Visitas No Guardadas", cont, delta= '{0:.2f}%'.format(cont/len(visitas['session_id'].unique()) * 100), delta_color='off')
    col[5].metric("Fotografias", len(visitas['imgs'].unique()))

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
        v = pd.merge(v[['imgs','nombre_desafio','resp','title','lat','lon','session_id','uid','name','created_at']], imagenes[['updated_at','resp_id','mark_url','original_url','error','data']], 
            how='left', left_on='imgs', right_on='resp_id')
        fecha = v['created_at'].max()
        with st.expander(f"Visita: {visita} - {fecha.strftime('%d/%h/%Y %I:%M %p')}"):
            seccion = v['title'].unique()
            try:
                col2 = st.columns(3)
                col2[0].metric("Imagenes", len(v))
                
                falt = pd.DataFrame(faltantes.loc[session,'products'])
                falt.rename(columns={"class": "Producto"},inplace=True)
                cols = st.columns(2)
                cols[0].header("Faltantes")
                f = falt.loc[~falt['exist'],'Producto']
                col2[1].metric("Faltantes", len(f), delta= '{0:.2f}%'.format(len(f)/len(falt) * 100))
                cols[0].dataframe(f)
                
                cols[1].header("Reconocidos")
                f = falt.loc[falt['exist'],'Producto']
                col2[2].metric("Reconocidos", len(f), delta= '{0:.2f}%'.format(len(f)/len(falt) * 100))
                cols[1].dataframe(f)
            except Exception as e:
                st.header("Faltantes")
                st.warning("No hay faltantes para esta visita")
            st.header("Imagenes")
            for s in seccion:
                defin = v[v['title']==s]
                st.subheader(s)
                for i, row in defin.iterrows():
                    col1, col2, col3 = st.columns((1, 1, 2))
                    try:
                        col1.image(row['original_url'], width=300)
                    except:
                        col1.markdown(f"No se puede ver la imagen <{row['original_url']}>")
                    try:
                        col2.image(row['mark_url'], width=300)
                    except:
                        col2.info("No hubo marcación")
                    try:
                        data = pd.DataFrame(row['data'])
                        col3.markdown(f"""
                        **Fotógrafo(a):** {row['name']}<br>
                        **Fecha:** {row['updated_at'].to_pydatetime().strftime('%d/%h/%Y %I:%M %p')}<br>
                        """,True)
                        if data.empty:
                            col3.info("No hubo reconocimiento")
                            if row['error']:
                                col3.warning(row['error'])
                        else:
                            data['score'] = (data['score']*100).map('{0:.2f}%'.format)
                            data.rename(columns={"obj_name": "Producto"}, inplace=True)
                            col3.dataframe(data[['Producto','score']])
                    except Exception as e:
                        col3.exception(e)
    
    