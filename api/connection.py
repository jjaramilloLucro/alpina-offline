import re
from api import auxiliar, access
from sqlalchemy.orm import Session
import models
import pandas as pd
from tqdm import tqdm
from sqlalchemy import exc
import time
from datetime import datetime, timedelta
import pytz
from sqlalchemy import between

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
		return user._asdict()

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
	return query.first()._asdict()


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
		return store._asdict()

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
		models.Stores.key_analitica
		).filter(
			models.Stores.store_key == id
			)
	store = query.first()
	if store:
		return store._asdict()


def get_cliente(db: Session, id):
	query = db.query(
		models.Clients.client_id,
    	models.Clients.name,
    	models.Clients.odv,
		).filter(
			models.Clients.client_id == id
			)
	client = query.first()
	if client:
		return client._asdict()


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
	return query.first()._asdict()

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
	return [a._asdict() for a in query.all()]


def get_infaltables_by_store(db: Session, store_key: str):
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
		).filter(
			models.Essentials.store_key == store_key
		)
	return [a._asdict() for a in query.all()]

def set_infaltables(db: Session, infaltables):
	query = db.query(models.Essentials).filter(models.Essentials.client_id == infaltables['client_id'])
	info = query.first()
	if info:
		query.update(infaltables)
		db_new = query.first()
		resp = query._asdict()
	else:
		db_new = models.Essentials(**infaltables)
		db.add(db_new)
		resp = db_new.__dict__
	
	db.commit()
	return resp

def get_respuesta(db:Session, session_id):
	try:
		return db.query(models.Visit).filter(models.Visit.session_id == session_id).first()._asdict()
	except:
		return None

def get_respuestas(db:Session, session_id):
	resps = db.query(
		models.Visit.session_id,
		models.Visit.created_at,
		models.Visit.imgs
		).filter(
			models.Visit.session_id == session_id
			).all()

	return [x._asdict() for x in resps]

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


def actualizar_size(db: Session, id, height, width):
	query = db.query(models.Images).filter(models.Images.resp_id == id)
	query.update({
		"width": width,
		"height": height
		})


def actualizar_subconsultas(db: Session, id, type_recon, info):
	query = db.query(
		models.Images_Recon
		).filter(
			models.Images_Recon.resp_id == id,
			models.Images_Recon.type_recon == type_recon
			)
	if query.first():
		query.update(info)
	else:
		db_new = models.Images_Recon(**info, resp_id = id)
		db.add(db_new)


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

def get_images_finished(db: Session, session_id):
	pendientes = db.query(models.Images.session_id,
	models.Images.resp_id,
	models.Images.data,
	models.Images.created_at
	).filter(models.Images.session_id == session_id,
		models.Images.original_url.is_not(None)
		)
	
	return pendientes.all()

def validar(db: Session, session_id, username):
	validate = db.query(models.Images).filter(
		models.Images.session_id == session_id,
		models.Images.mark_url.is_(None),
		models.Images.original_url.is_not(None)
		).all()
	auxiliar.actualizar_imagenes([{'img':v.original_url,'id':v.resp_id} for v in validate], session_id, username)


def get_name_product(obj_name):
	return obj_name['Nombre'] if isinstance(obj_name, dict) else obj_name

def get_reconocidos(db: Session, session_id):
	resp = get_images(db, session_id)
	try:
		recon = [get_name_product(x['obj_name']) for data in resp for x in data['data']]
		return  list(set(recon))
	except:
		return list()

def get_infaltables_by_session(db:Session, session_id):
	respuesta = get_respuesta(db, session_id)
	infaltables = get_infaltables_by_store(db, respuesta['store'])
	if not infaltables:
		return get_infaltables(db, respuesta['document_id'])
	return infaltables

def calculate_faltantes(db: Session, session_id, username):
	cant = 0
	while not termino(db, session_id) and cant < 3:
		print("Esperando Reconocimientos")
		time.sleep(2)
		cant += 1

	print('Empezando a validar...')
	validar(db, session_id, username)

	productos = get_infaltables_by_session(db, session_id)
	reconocidos = get_reconocidos(db, session_id)
	reconocidos = traducir_reconocidos(db, reconocidos)

	for prod in productos:
		prod['exist'] = prod['product_id'] in reconocidos

	return True, productos

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
		return [a._asdict() for a in query.all()]
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
		else:
			db_new = models.Missings(
						session_id=session_id,
						prod_id=prod['product_id'],
						exist=prod['exist']
					)
			db.add(db_new)
	
	db.commit()


def get_images(db:Session, session_id):
	imgs = db.query(
		models.Images.data, models.Images.session_id, models.Images.resp_id
		).filter(
			models.Images.session_id == session_id, models.Images.original_url.is_not(None)
			).all()
	
	if not imgs:
		return []
		
	return [x._asdict() for x in imgs]


def get_images_with_error(db:Session, session_id):
	imgs = db.query(
		models.Images.data,models.Images.session_id, models.Images.resp_id
		).filter(
			models.Images.session_id == session_id, models.Images.error.is_not(None)
			).all()
	
	if not imgs:
		return []

	return imgs

def get_promises_images(db:Session, session_id):
	imgs = db.query(
		models.Images.resp_id, models.Images.session_id
		).filter(
			models.Images.session_id == session_id
			).all()

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
		models.Train_Product.train_product_id,
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


def set_bulk_recon(db: Session, list_data):
	try:
		db.bulk_insert_mappings(models.Recognitions, list_data)

	except exc.IntegrityError as e:
		error = str(e.orig).split("\n")
		error = error[-2]
		print(error)
		db.rollback()

def validar_fecha(fecha):
    patron = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(patron, fecha):
        return True
    else:
        return False
    

def dailyReport(db: Session, start_date, end_date):
	tz = pytz.timezone('America/Bogota')
	now = datetime.now(tz)
	now_utf5 = now.strftime('%Y-%m-%d')
	yesterday = now - timedelta(days=1)
	yesterday_utf5 = yesterday.strftime('%Y-%m-%d')
	#Validando el formato de la fecha que sea yyyy-mm-dd
	format_date = validar_fecha(start_date)
	format_date_end = validar_fecha(end_date)

	if start_date == "" and end_date == "":
		start_date = yesterday_utf5
		end_date = now_utf5
		format_date = True
		format_date_end = True
		diferencia = 1
	elif format_date and format_date_end:
		start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
		end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
		end_date =  end_date + timedelta(days=1)
		diferencia = end_date - start_date
		diferencia = diferencia.days
	
	if format_date and format_date_end and diferencia < 8:
		query = db.query(
					models.Visit.created_at,
					models.Visit.store,
					models.Visit.uid,
					models.Visit.session_id,
					models.Product.display_name,
					models.Product.family,
					models.Product.category,
					models.Product.territory,
					models.Product.brand,
					models.Product.segment,
					models.Product.sku,
					models.Missings.exist
				).select_from(
					models.Visit
				).join(
					models.Missings, models.Missings.session_id == models.Visit.session_id
				).join(
					models.Product, models.Missings.prod_id == models.Product.product_id
				).filter(
					models.Visit.created_at.between(start_date, end_date)
				).all()
	else:
		query = ""
	return query
	

def get_essentials_general(db: Session, store):
	query = db.query(
		models.Product.product_id,
		models.Product.display_name,
		models.Product.brand,
		models.Product.sku,
		models.Product.ean,
		models.Essentials_General.prod_id,
		models.Essentials_General.store_key,
		models.Essentials_General.type_of_prod
	).join(
		models.Product,
		models.Product.product_id == models.Essentials_General.prod_id
	).filter(
		models.Essentials_General.store_key == store
	)
	return query.all()



def get_store_by_session_id(db: Session, session_id):
	query = db.query(
		models.Visit.store,
		models.Visit.session_id
	).filter(
		models.Visit.session_id == session_id
	)

	return query.first()

def get_reconocidos_complete(db: Session, session_id):
	resp = get_images(db, session_id)
	recon = [x['obj_name'] for data in resp for x in data['data']]
	return list(set(recon))


def set_missings_general(db: Session, recons):
	resp = list()
	for recon in recons:
		db_new = models.Missings_General(**recon, finished_at=auxiliar.time_now())
		db.add(db_new)
		resp.append(db_new.__dict__)

	db.commit()
	return resp
