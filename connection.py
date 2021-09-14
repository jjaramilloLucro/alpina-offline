import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time



#Conexion a Firebase Cloud Firestore
url = os.path.join('data','lucro-alpina-firebase-adminsdk-yeun4-0e168872c1.json')
cred = credentials.Certificate(url)
firebase_admin.initialize_app(cred, {
	'projectId': 'lucro-alpina',
})


db = firestore.client()

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
    ref = db.collection(u'admin').document(username)
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