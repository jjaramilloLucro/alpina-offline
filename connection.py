import os, auxiliar
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
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
		doc = doc_ref.document(id + '-' + i['img_ids'][x])
		images.append({'img':i['imgs'][x],'id':id + '-' + i['img_ids'][x]})
		i['imgs'][x] = id + '-' + i['img_ids'][x]
		batch.set(doc,{"resp_id": id, 'created_at':auxiliar.time_now()})

	del i['img_ids']
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
		
	else:
		respuesta['respuestas'] = [respuesta['respuestas']]
		user = respuesta
		
	
	if 'tienda' in respuesta:
		user['tienda'] = respuesta['tienda'] 
	ref.set(user)
    
def escribir_desafio(respuesta):
	db = firestore.client()
	ref = db.collection(u'challenges').document(f"{respuesta['document_id']}")
	ref.set(respuesta)

def actualizar_imagen(id, data, original, marcada, error):
	db = firestore.client()
	ref = db.collection(u'images').document(f"{id}")
	ref.update({
		"data":data,
		"url_original": original,
		"url_marcada": marcada,
		'updated_at':auxiliar.time_now(),
		"error":error
		})

def escribir_faltantes(id, productos):
	db = firestore.client()
	ref = db.collection(u'infaltables').document(f"{id}")
	ref.update({"productos":productos})

def get_faltantes(id):
	db = firestore.client()
	ref = db.collection(u'infaltables').document(f"{id}")
	query = ref.get()
	user = query.to_dict()
	return user['productos']

def get_productos(session_id):
	db = firestore.client()
	doc_ref = db.collection(u'images')
	query = doc_ref.where(u'resp_id', u'==', f'{session_id}').stream()
			
	users = [doc.to_dict() for doc in query]
	reconocio = list()
	for user in users:
		if 'data' in user:
			prod = user['data']
			if isinstance(prod, list):
				[reconocio.append(x['obj_name']) for x in prod]
		else:
			return reconocio, False

	return reconocio, True

def get_respuestas(session_id):
	db = firestore.client()
	ref = db.collection(u'respuestas').document(f"{session_id}")
	query = ref.get()
	user = query.to_dict()
	return user

def get_imagen_marcada(id):
	db = firestore.client()
	ref = db.collection(u'images').document(f"{id}")
	query = ref.get()
	user = query.to_dict()
	return user

def escribir_usuario(user):
	db = firestore.client()
	ref = db.collection(u'users').document(f"{user['username']}")
	ref.set(user)

def get_urls(session_id):
	db = firestore.client()
	doc_ref = db.collection(u'images')
	query = doc_ref.where(u'resp_id', u'==', f'{session_id}').stream()

	users = [doc.to_dict() for doc in query]
	return [x['url_original'] for x in users if 'url_original' in x]