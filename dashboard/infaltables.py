import streamlit as st
import pandas as pd
import Definitions

def main(usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos):
    cols = st.columns(3)
    cols[0].metric("Cantidad de Grupos",len(grupos))
    a = pd.merge(grupos[['id','name']],infaltables, how='outer', left_on='id', right_on= 'group_id')
    a['group_id'].fillna(-1,inplace=True)
    for index, row in a.iterrows():
        with st.expander(row['name']):
            if row['group_id'] != -1:
                st.dataframe(row['prods'])
            else:
                st.info("No hay faltantes para este grupo")
            
    a = a.explode('prods')
    prods = pd.concat([a, a['prods'].apply(pd.Series)], axis=1)
    df = pd.DataFrame(Definitions.classes_dict)
    df = df.unstack().reset_index(name='product')
    df = df.dropna()
    df.columns = ['brand','index','product']
    prods['is_in'] = prods['class'].isin(df['product'])
    cols[1].metric("Productos Infaltables", len(prods))
    b = prods.reset_index(drop=True)
    b = pd.merge(b,df, how='left', left_on='class', right_on='product')
    #b.to_csv('total.csv',encoding='utf-16',index=False)
    b = b[~b['is_in']]
    #b.to_csv('buscar.csv')
    #cols[2].metric("Productos No reconocidos", len(b))
    

