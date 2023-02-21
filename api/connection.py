from api import auxiliar, access
from sqlalchemy.orm import Session
import models
import pandas as pd
from tqdm import tqdm
from sqlalchemy import exc

def get_user(db: Session, username):
	user = db.query(
		models.User.uid,
		models.User.password,
		models.User.name,
		models.User.telephone,
		models.User.register_at,
		models.User.register_by,
		models.User.debug,
		models.User.isActive,
		models.User.deleted_at,
		models.User.deleted_by
		).filter(
			models.User.uid == username
			).first()
	if user:
		return dict(**user)

def get_all_user(db: Session):
	return db.query(models.User).all()

def set_user(db: Session, user):
	db_new = models.User(**user, isActive=True, debug=False)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def update_user(db:Session, info):
	query = db.query(models.User).filter(models.User.uid == info['uid'])
	query.update(info)
	db.commit()
	return query.first().__dict__


def get_grupos(db: Session):
	return db.query(models.Group).all()

def get_grupo(db: Session, id):
	return db.query(models.Group).filter(models.Group.id.in_(id)).all()

def set_grupo(db: Session, grupo):
	db_new = models.Group(**grupo)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__


def get_tienda(db: Session, id):
	query = db.query(
		models.Stores.store_key,
		models.Stores.client_id,
		models.Stores.zone_id,
		models.Stores.distributor_id,
		models.Stores.uid,
		models.Stores.name,
		models.Stores.city,
		models.Stores.address,
		models.Stores.category,
		models.Stores.tipology,
		models.Stores.channel,
		models.Stores.subchannel,
		models.Stores.leader,
		models.Stores.lat,
		models.Stores.lon,
		models.Stores.isActive,
		models.Stores.created_at,
		models.Stores.created_by,
		models.Stores.deleted_at,
		models.Stores.deleted_by,
		).filter(
			models.Stores.client_id == id
			)
	store = query.first()
	if store:
		return dict(**store)

def get_tienda_sql(db: Session, id):
	query = db.query(
		models.Stores.store_key,
		models.Stores.client_id,
		models.Stores.zone_id,
		models.Stores.distributor_id,
		models.Stores.uid,
		models.Stores.name,
		models.Stores.city,
		models.Stores.address,
		models.Stores.category,
		models.Stores.tipology,
		models.Stores.channel,
		models.Stores.subchannel,
		models.Stores.leader,
		models.Stores.lat,
		models.Stores.lon,
		models.Stores.isActive,
		models.Stores.created_at,
		models.Stores.created_by,
		models.Stores.deleted_at,
		models.Stores.deleted_by,
		).filter(
			models.Stores.store_key == id
			)
	store = query.first()
	if store:
		return dict(**store) 


def get_all_stores(db: Session):
	return db.query(models.Stores).all()

def get_tienda_user(db: Session, username):
	return db.query(models.Stores.client_id, models.Stores.name, models.Stores.add_exhibition, models.Stores.day_route, 
	models.Stores.channel, models.Stores.group, models.Stores.lat, models.Stores.lon, models.Stores.direction, models.Stores.store_key
	).filter(models.Stores.user_id == username).all()

def set_tienda(db: Session, tienda):
	db_new = models.Stores(**tienda, isActive=True)
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def update_tienda(db:Session, tienda):
	query = db.query(models.Stores).filter(models.Stores.store_key == tienda['store_key'])
	query.update(tienda)
	db.commit()
	return query.first().__dict__

def get_infaltables(db: Session, client_id: int):
	query = db.query(
			models.Product.product_id,
			models.Product.display_name.label("class"),
			models.Product.family,
			models.Product.category,
			models.Product.segment,
			models.Product.territory,
			models.Product.brand,
			models.Product.sku,
		).join(
			models.Essentials, models.Product.product_id == models.Essentials.prod_id
		).join(
			models.Clients, models.Essentials.client_id == models.Clients.client_id
		).filter(
			models.Clients.client_id == client_id
		)
	return [dict(**a) for a in query.all()]


def set_infaltables(db: Session, infaltables):
	query = db.query(models.Essentials).filter(models.Essentials.client_id == infaltables['client_id'])
	info = query.first()
	if info:
		query.update(infaltables)
		db_new = query.first()
	else:
		db_new = models.Essentials(**infaltables)
		db.add(db_new)
	
	db.commit()
	return db_new.__dict__

def get_respuesta(db:Session, session_id):
	try:
		return db.query(models.Visit).filter(models.Visit.session_id == session_id).first().__dict__
	except:
		return None

def get_respuestas(db:Session, session_id):
	return db.query(models.Visit.session_id, models.Visit.created_at, models.Visit.imgs).filter(models.Visit.session_id == session_id).all()

def guardar_resultados(db:Session, respuesta, id_cliente):
	resp = models.Visit(**respuesta, endpoint = id_cliente)
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

def actualizar_imagen(db: Session, id, data, marcada, error, ambiente):
	query = db.query(models.Images).filter(models.Images.resp_id == id)
	query.update({
		"data":data,
		"mark_url": marcada,
		'updated_at':auxiliar.time_now(),
		"error":error,
		"schema": ambiente
		})

def termino(db: Session, session_id):
	existe = db.query(
		models.Images.session_id,
		models.Images.resp_id,
		models.Images.data
		).filter(
			models.Images.session_id == session_id
			).first()

	pendientes = db.query(models.Images.session_id,
	models.Images.resp_id,
	models.Images.data,
	models.Images.created_at
	).filter(models.Images.session_id == session_id,
		models.Images.updated_at.is_(None)
		).first()

	return existe and not pendientes 

def validar(db: Session, session_id, username):
	validate = db.query(models.Images).filter(
		models.Images.session_id == session_id,
		models.Images.mark_url.is_(None),
		models.Images.original_url != None
		).all()
	auxiliar.actualizar_imagenes(db, [{'img':v.original_url,'id':v.resp_id} for v in validate], session_id, username)

def get_reconocidos(db: Session, session_id):
	resp = get_images(db, session_id)
	recon = [x['obj_name'] for data in resp for x in data['data']]
	return  list(set(recon))

def get_infaltables_by_session(db:Session, session_id):
	respuesta = get_respuesta(db, session_id)
	return get_infaltables(db, respuesta['document_id'])

def calculate_faltantes(db: Session, session_id, username):
	finish = termino(db, session_id)
	if not finish:
		return False, list()

	print('Empezando a validar...')
	validar(db, session_id, username)

	productos = get_infaltables_by_session(db, session_id)
	reconocidos = get_reconocidos(db, session_id)
	reconocidos = traducir_reconocidos(db, reconocidos)

	for prod in productos:
		prod['exist'] = prod['product_id'] in reconocidos

	return finish, productos

def get_faltantes(db:Session, session_id):
	query = db.query(
			models.Product.display_name.label("class"),
			models.Product.family,
			models.Product.category,
			models.Product.segment,
			models.Product.territory,
			models.Product.brand,
			models.Product.sku,
			models.Missings.exist
		).join(
			models.Product, models.Missings.prod_id == models.Product.product_id
		).filter(
			models.Missings.session_id == session_id
		)
	if query:
		return [dict(**a) for a in query.all()]
	else:
		return None
		


def delete_faltantes(db:Session, session_id):
	try:
		db.query(models.Missings).filter(models.Missings.session_id == session_id).delete()
		db.commit()
		return True
	except:
		return False


def set_faltantes(db:Session, session_id, faltantes):
	for prod in faltantes:
		query = db.query(
					models.Missings
				).filter(
					models.Missings.session_id == session_id,
					models.Missings.prod_id == prod['product_id']
					)
		if query.first():
			query.update(dict(finished_at=auxiliar.time_now(), exist=prod['exist']))
			db_new = query.first()
	else:
		for prod in faltantes:
			db_new = models.Missings(
					session_id=session_id,
					prod_id=prod['product_id'],
					exist=prod['exist']
				)
			db.add(db_new)
	
	db.commit()
	
	return db_new.__dict__

def get_images(db:Session, session_id):
	imgs = db.query(
		models.Images.data,models.Images.session_id, models.Images.resp_id
		).filter(
			models.Images.session_id == session_id, models.Images.original_url != None
			).all()
	
	if not imgs:
		return []

	imgs = [x._asdict() for x in imgs]
	for img in imgs:
		if img['data']:
			real = [x for x in img['data'] if 'other' not in x['obj_name'].lower()]
			img['data'] = real
		
	return imgs

def get_promises_images(db:Session, session_id):
	imgs = db.query(
		models.Visit.imgs
		).filter(
			models.Visit.session_id == session_id
			).all()
	imgs = [x for img in imgs for x in img.imgs]

	return imgs
	

def get_image(db:Session, resp_id):
	return db.query(models.Images).filter(models.Images.resp_id == resp_id).all()

def existe_session(db: Session, session_id):
	return not db.query(models.Visit.session_id).filter(models.Visit.session_id == session_id).first()


def upload_stores(db: Session, csv_file):

	df = pd.read_csv(csv_file,sep=",")
	df = df.fillna(0)
	df = df.astype(str)
	print(df['day_route'].unique())

	df['day_route'] = df['day_route'].apply(eval)
	df['add_exhibition'] = df['add_exhibition'].apply(eval)
	
	rec= df.to_dict(orient='records')
	cargados = 0
	fallos = 0
	
	pbar = tqdm(total=len(rec))
	for i, store in enumerate(rec):
		try:
			t = get_tienda_sql(db, store['store_key'])
			if t:
				update_tienda(db, store)
			else:
				set_tienda(db, store)
			cargados += 1
			
		except exc.SQLAlchemyError as e:
			db.rollback()
			fallos += 1
			print(str(e))

		if i % 100 == 0:
			db.commit()
			pbar.update(100)

	pbar.close()
	db.commit()

	return f"Se realizaron {cargados} cargas. Y se presentaron {fallos} fallos."
	

def upload_users(db: Session, csv_file):

	df = pd.read_csv(csv_file,sep=",").astype(str)
	print(df['group'].unique())

	df['group'] = df['group'].apply(eval)
	df['password'] = df['password'].apply(lambda x: access.get_password_hash(x))
	print(df.head())
	#df['add_exhibition'] = df['add_exhibition'].apply(eval)
	rec= df.to_dict(orient='records')
	cargados = 0
	fallos = 0
	
	pbar = tqdm(total=len(rec))
	for i, store in enumerate(rec):
		try:
			t = get_user(db, store['username'])
			if t:
				update_user(db, store)
			else:
				set_user(db, store)
			cargados += 1
			
		except exc.SQLAlchemyError as e:
			db.rollback()
			fallos += 1
			print(str(e))

		if i % 100 == 0:
			db.commit()
			pbar.update(100)

	pbar.close()
	db.commit()

	return f"Se realizaron {cargados} cargas. Y se presentaron {fallos} fallos."
	
def set_comment(db: Session, comment):
	db_new = models.Comments(**comment, created_at=auxiliar.time_now())
	db.add(db_new)
	db.commit()
	db.refresh(db_new)

	return db_new.__dict__

def get_configs(db: Session):
	query = db.query(models.Configs).all()
	return {q.key:q.value for q in query}


def traducir_reconocidos(db: Session, reconocidos):
	info = db.query(
		models.Train_Product.prod_id
		).filter(
			models.Train_Product.train_name.in_(reconocidos)
			)
	return list(set([a.prod_id for a in info.all()]))


def get_product_by_train_name(db: Session, train_name:str):
	query = db.query(
		models.Product.product_id,
		models.Product.sku,
		models.Product.display_name,
		models.Product.ean,
		models.Train_Product.train_name,
	).join(
		models.Product, models.Train_Product.prod_id == models.Product.product_id
	).filter(
		models.Train_Product.train_name == train_name
	)

	return query.first()