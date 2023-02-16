from fastapi.testclient import TestClient
import configs
from main import app
from functools import lru_cache
import requests
import time


test_settings = configs.get_test_settings()
client = TestClient(app)

####################################### Report Configs #######################################
def pytest_html_report_title(report):
    report.title = "My very own title!"


####################################### Unit Test #######################################

def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.text == 'true'

def test_login():
    response = client.post("/token", files = {
        'username': (None, test_settings.TEST_USER),
        'password': (None, test_settings.TEST_PWD),
		'client_id': (None, test_settings.TEST_CLIENT_ID),
		'client_secret': (None, test_settings.TEST_CLIENT_SECRET),
    })
    assert response.status_code == 200
    resp = response.json()
    assert resp.get("token_type",None) == "bearer"
    assert resp.get("access_token", None) != None

@lru_cache()
def get_token():
    response = client.post("/token", files = {
        'username': (None, test_settings.TEST_USER),
        'password': (None, test_settings.TEST_PWD),
		'client_id': (None, test_settings.TEST_CLIENT_ID),
		'client_secret': (None, test_settings.TEST_CLIENT_SECRET),
    })
    resp = response.json()
    return resp.get("access_token")


def test_get_session_id():
    # Unauthorized
    response = client.get("/")
    assert response.status_code == 401

    # Authorized
    token = get_token()
    response = client.get("/",headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.text != None

####################################### Flow Test #######################################
def test_set_answer():
    # Authorized
    token = get_token()
    response = client.get("/",headers={"Authorization": f"Bearer {token}"})
    session_id = response.text
    test_resp_ok = {
            "session_id": session_id,
            "uid": "prueba",
            "document_id": "77",
            "lat": 6.2745088,
            "lon": -75.5788499,
            "store": "103507-545PR-77",
            "imgs": ["123"]
            }
    test_resp_no = {
            "session_id": session_id,
            "uid": "prueba",
            "document_id": "777",
            "lat": 6.2745088,
            "lon": -75.5788499,
            "store": "103507-545PR-77",
            "imgs": ["123"]
            }

    # Unauthorized
    response = client.post("/answer", data = test_resp_ok)
    assert response.status_code == 401

    # Authorized
    response = client.post("/answer",headers={"Authorization": f"Bearer {token}"}, json = test_resp_no)
    assert response.status_code == 404

    response = client.post("/answer",headers={"Authorization": f"Bearer {token}"}, json = test_resp_ok)

    assert response.status_code == 200
    assert response.json() != None

def test_set_image():
    # Authorized
    token = get_token()
    response = client.get("/",headers={"Authorization": f"Bearer {token}"})
    session_id = response.text
    test_resp_ok = {
            "session_id": session_id,
            "uid": "prueba",
            "document_id": "77",
            "lat": 6.2745088,
            "lon": -75.5788499,
            "store": "103507-545PR-77",
            "imgs": ["123"]
            }
    test_resp_no = {
            "session_id": session_id,
            "uid": "prueba",
            "document_id": "13465",
            "lat": 6.2745088,
            "lon": -75.5788499,
            "store": "103507-545PR-77",
            "imgs": ["123"]
            }

    # Unauthorized
    response = client.post("/answer", data = test_resp_ok)
    assert response.status_code == 401

    # Authorized
    response = client.post("/answer",headers={"Authorization": f"Bearer {token}"}, json = test_resp_no)
    assert response.status_code == 404

    response = client.post("/answer",headers={"Authorization": f"Bearer {token}"}, json = test_resp_ok)

    assert response.status_code == 200
    assert response.json() != None

    url = "https://storage.googleapis.com/lucro-alpina-admin_alpina-media/original_images/prueba/prueba_integracion/123.jpg"
    image = {('imgs', ('123.jpg', requests.get(url).content, 'image/jpeg'))}

    response = client.post(f"/answer/{session_id}", headers={"Authorization": f"Bearer {token}"}, files = image)

    assert response.status_code == 200
    resp = response.json() 
    assert resp != None
    assert len(resp) == 1

    """
    termino = False
    while not termino:
        time.sleep(2)
        resp_missings = client.get(f"/missings?session_id={session_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp_missings.status_code == 200
        info = resp_missings.json()
        termino = info['finish']

    assert "missings" in info
    assert len(info["missings"]) == 2
    """

