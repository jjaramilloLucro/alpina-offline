from fastapi.testclient import TestClient
import configs
from main import app
from functools import lru_cache


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