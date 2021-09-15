import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time
from functools import lru_cache


#Conexion a Firebase Cloud Firestore
url = os.path.join('data','lucro-alpina-firebase-adminsdk-yeun4-0e168872c1.json')
cred = credentials.Certificate(url)
firebase_admin.initialize_app(cred, {
	'projectId': 'lucro-alpina',
})


db = firestore.client()

@lru_cache()
def return_db():
	return db

def getAllChallenges():
	print('Challenges')
	start_time = time.time()
	ref = db.collection(u'challenges')
	query = ref.get()
	print("Query time:")
	print("--- %s seconds ---" % (time.time() - start_time))
	user = list()
	for doc in query:
		u = doc.to_dict()
		u['document_id'] = doc.id
		user.append(u)

	print("Load time:")
	print("--- %s seconds ---" % (time.time() - start_time))
	return user

def getUser(username):
    ref = db.collection(u'users').document(username)
    query = ref.get()
    user = query.to_dict()

    return user

def getAllInfaltables():
	print('Infaltables')
	start_time = time.time()
	ref = db.collection(u'infaltables')
	query = ref.get()
	print("Query time:")
	print("--- %s seconds ---" % (time.time() - start_time))
	user = [x.to_dict() for x in query]
	print("Load time:")
	print("--- %s seconds ---" % (time.time() - start_time))
	return user

def guardarResultadosImagen(respuesta, id):
	start_time = time.time()
	db = firestore.client()

	doc_ref = db.collection(u'images')
	images = list()
	batch = db.batch()

	for i in respuesta['respuestas']:
		for x in i['imgs']:
			doc = doc_ref.document()
			images.append({'img':x['img'],'id':doc.id})
			x['img'] = doc.id
			batch.set(doc,{"resp_id": id})

	batch.commit()
	print("Write time:")
	print("--- %s seconds ---" % (time.time() - start_time))

	respuesta['imagenes'] = images

def documento_temporal():
	query = db.collection(u'respuestas').document()
	return query.id

def guardarResultados(respuesta, id):
    query = db.collection(u'respuestas').document(f'{id}')
    query.set(respuesta)
    
def escribir_desafio(respuesta):
	ref = db.collection(u'challenges').document(f"{respuesta['document_id']}")
	ref.set(respuesta)

def actualizar_imagen(id, data):
	ref = db.collection(u'images').document(f"{id}")
	ref.update({"data":data})