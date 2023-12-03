from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_read_main():
    response = client.get("/")
    print(response)
    assert response.status_code == 200

