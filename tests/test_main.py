from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import main

# 1) Reemplazamos engine por uno en memoria (SQLite) antes de instanciar TestClient
main.engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# 2) Crear tabla y datos iniciales
with main.engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """))
    conn.execute(text("INSERT INTO usuario (nombre, email) VALUES ('Alice', 'alice@example.com')"))
    conn.execute(text("INSERT INTO usuario (nombre, email) VALUES ('Bob', 'bob@example.com')"))

client = TestClient(main.app)

def test_test_endpoint():
    r = client.get("/test")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_listar_usuarios():
    r = client.get("/usuarios")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(u["nombre"] == "Alice" for u in data)

def test_obtener_usuario():
    r = client.get("/usuarios/1")
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"

def test_crud_usuario():
    # crear
    payload = {"nombre": "Carol", "email": "carol@example.com"}
    r = client.post("/usuarios", json=payload)
    assert r.status_code == 201
    new_id = r.json()["id"]

    # actualizar
    r = client.put(f"/usuarios/{new_id}", json={"nombre": "Caroline", "email": "caroline@example.com"})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Caroline"

    # eliminar
    r = client.delete(f"/usuarios/{new_id}")
    assert r.status_code == 204

    # comprobar inexistente
    r = client.get(f"/usuarios/{new_id}")
    assert r.status_code == 404