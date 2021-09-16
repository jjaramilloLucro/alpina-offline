import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time
from functools import lru_cache
import google.auth


credential_path = os.path.join('data','lucro-alpina-20a098d1d018.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
credentials_BQ, your_project_id = google.auth.default(
	scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

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
	start_time = time.time()
	ref = db.collection(u'challenges')
	query = ref.get()
	user = list()
	for doc in query:
		u = doc.to_dict()
		u['document_id'] = doc.id
		user.append(u)

	return user

def getUser(username):
    ref = db.collection(u'users').document(username)
    query = ref.get()
    user = query.to_dict()

    return user

def getAllInfaltables():
	start_time = time.time()
	ref = db.collection(u'infaltables')
	query = ref.get()
	user = [x.to_dict() for x in query]
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

def actualizar_imagen(id, data, original, marcada):
	ref = db.collection(u'images').document(f"{id}")
	ref.update({
		"data":data,
		"url_original": original,
		"url_marcada": marcada
		})