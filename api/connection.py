from api import auxiliar
from sqlalchemy.orm import Session
import models
import pandas as pd
from tqdm import tqdm

def get_user(db: Session, username):
	return db.query(models.User).filter(models.User.username == username).first().__dict__

def set_user(db: Session, user):
	db_new = models.User(**user)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def set_version(db: Session, username, version):
	db.query(models.User).filter(models.User.username == username).update({models.User.version: version})
	db.commit()
	return True

def get_grupo(db: Session, id):
	return db.query(models.Group).filter(models.Group.id.in_(id)).all()

def set_grupo(db: Session, grupo):
	db_new = models.Grupo(**grupo)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_challenge(db: Session, id):
	return db.query(models.Challenge).filter(models.Challenge.challenge_id == id).first().__dict__

def set_challenge(db: Session, desafio):
	db_new = models.Challenge(**desafio)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_tienda(db: Session, id):
	return db.query(models.Stores).filter(models.Stores.client_id == id).first().__dict__

def get_tienda_user(db: Session, username):
	return db.query(models.Stores.client_id, models.Stores.name, models.Stores.add_exhibition, models.Stores.day_route).filter(models.Stores.user_id == username).all()

def set_tienda(db: Session, tienda):
	db_new = models.Stores(**tienda)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_infaltables(db: Session, id_grupo):
	return db.query(models.Essentials).filter(models.Essentials.group_id == id_grupo).first().__dict__

def set_infaltables(db: Session, infaltables):
	db_new = models.Essentials(**infaltables)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_respuesta(db:Session, session_id):
	try:
		return db.query(models.Visit).filter(models.Visit.session_id == session_id).first().__dict__
	except:
		return None

def get_respuestas(db:Session, session_id):
	return db.query(models.Visit.session_id, models.Visit.id_task, models.Visit.imgs).filter(models.Visit.session_id == session_id).all()

def guardar_resultados(db:Session, respuesta):
	resp = models.Visit(**respuesta)
	db.add(resp)	
	db.commit()
	id = respuesta['session_id']
	for x in respuesta['imgs']:
		db_new = models.Images(resp_id= x,session_id= id, created_at=auxiliar.time_now())
		db.add(db_new)
		try:
			db.commit()
		except:
			db.rollback()

	return respuesta

def guardar_url_original(db:Session, resp_id, url):
	db.query(models.Images).filter(models.Images.resp_id == resp_id).update({models.Images.original_url: url})

def actualizar_imagen(db: Session, id, data, marcada, error):
	db.query(models.Images).filter(models.Images.resp_id == id).update({
		"data":data,
		"mark_url": marcada,
		'updated_at':auxiliar.time_now(),
		"error":error
		})

def termino(db: Session, session_id):
	existe = db.query(models.Images.session_id, models.Images.resp_id, models.Images.data).filter(models.Images.session_id == session_id).first()
	pendientes = db.query(models.Images.session_id, models.Images.resp_id, models.Images.data).filter(models.Images.session_id == session_id, models.Images.updated_at == None).first()
	return existe and not pendientes 

def validar(db: Session, session_id):
	validate = db.query(models.Images).filter(models.Images.session_id == session_id, models.Images.error != None).all()
	auxiliar.actualizar_imagenes(db, [{'img':v.original_url,'id':v.resp_id} for v in validate], session_id)

def get_reconocidos(db: Session, session_id):
	resp = get_images(db, session_id)
	recon = [x['obj_name'] for data in resp for x in data['data']]
	return  list(set(recon))

def get_infaltables_by_session(db:Session, session_id):
	respuesta = get_respuesta(db, session_id)
	return get_infaltables(db, respuesta['document_id'].split('__')[0])['prods']

def calculate_faltantes(db: Session, session_id):
	finish = termino(db, session_id)
	if not finish:
		return False, list()

	print('Empezando a validar...')
	validar(db, session_id)

	productos = get_infaltables_by_session(db, session_id)
	reconocidos = get_reconocidos(db, session_id)

	for prod in productos:
		prod['exist'] = prod['class'] in reconocidos

	return finish, productos

def get_faltantes(db:Session, session_id):
	try:
		return db.query(models.Missings).filter(models.Missings.session_id == session_id).first().__dict__
	except:
		return None

def set_faltantes(db:Session, session_id, faltantes):
	db_new = models.Missings(session_id=session_id, finished_at=auxiliar.time_now(), products=faltantes)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_images(db:Session, session_id):
	return db.query(models.Images.data,models.Images.session_id, models.Images.resp_id).filter(models.Images.session_id == session_id).all()

def get_image(db:Session, resp_id):
	return db.query(models.Images).filter(models.Images.resp_id == resp_id).all()

def existe_session(db: Session, session_id):
	return not db.query(models.Visit.session_id).filter(models.Visit.session_id == session_id).first()


def upload_stores(db: Session, csv_file):

	df = pd.read_csv(csv_file,sep=",").astype(str)
	print(df['day_route'].unique())

	df['day_route'] = df['day_route'].apply(eval)
	df['add_exhibition'] = df['add_exhibition'].apply(eval)
	rec= df.to_dict(orient='records')
	
	for store in tqdm(rec):
		try:
			set_tienda(db, store)
		except:
			db.rollback()
	
	return True
