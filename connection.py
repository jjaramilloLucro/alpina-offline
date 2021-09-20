import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
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


def getAllChallenges():
	db = firestore.client()
	ref = db.collection(u'challenges')
	query = ref.get()
	user = list()
	for doc in query:
		u = doc.to_dict()
		u['document_id'] = doc.id
		user.append(u)

	return user

def getChallenge(id):
	db = firestore.client()
	ref = db.collection(u'challenges').document(id)
	query = ref.get()
	user = query.to_dict()

	return user

def getUser(username):
	db = firestore.client()
	ref = db.collection(u'users').document(username)
	query = ref.get()
	user = query.to_dict()

	return user

def getAllInfaltables():
	db = firestore.client()
	ref = db.collection(u'infaltables')
	query = ref.get()
	user = [x.to_dict() for x in query]
	return user

def guardarResultadosImagen(respuesta):
	db = firestore.client()
	id = respuesta['session_id']
	doc_ref = db.collection(u'images')
	images = list()
	batch = db.batch()
	
	i = respuesta['respuestas']

	for x in range(len(i['imgs'])):
		doc = doc_ref.document()
		images.append({'img':i['imgs'][x],'id':doc.id})
		i['imgs'][x] = doc.id
		batch.set(doc,{"resp_id": id})

	batch.commit()
	respuesta['imagenes'] = images

def documento_temporal():
	db = firestore.client()
	query = db.collection(u'respuestas').document()
	return query.id

def guardarResultados(respuesta):
	db = firestore.client()
	ref = db.collection(u'respuestas').document(f'{respuesta["session_id"]}')
	query = ref.get()
	user = query.to_dict()
	if user:
		user['respuestas'].append(respuesta['respuestas'])
		ref.set(user)
	else:
		respuesta['respuestas'] = [respuesta['respuestas']]
		ref.set(respuesta)
    
def escribir_desafio(respuesta):
	db = firestore.client()
	ref = db.collection(u'challenges').document(f"{respuesta['document_id']}")
	ref.set(respuesta)

def actualizar_imagen(id, data, original, marcada):
	db = firestore.client()
	ref = db.collection(u'images').document(f"{id}")
	ref.update({
		"data":data,
		"url_original": original,
		"url_marcada": marcada
		})

def escribir_faltantes(id, productos):
	db = firestore.client()
	ref = db.collection(u'infaltables').document(f"{id}")
	ref.update({"productos":productos})