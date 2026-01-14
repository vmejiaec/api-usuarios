import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST","127.0.0.1") 
DB_PORT = os.getenv("DB_PORT","13306")
DB_USER = os.getenv("DB_USER","victor")
DB_PASS = os.getenv("DB_PASS","pio")
DB_NAME = os.getenv("DB_NAME","demo")

DATABASE_URL = "mysql+pymysql://"\
               f"{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}" 

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800
)

app = FastAPI(title="APU Usuarios (demo)", version = "1.0.0")

# ---------- Esquemas (Pydantic) ---------- #
class UsuarioOut(BaseModel):
    id : int
    nombre: str
    email: EmailStr

class UsuarioIn(BaseModel):
    id: int | None = None
    nombre: str
    email: EmailStr

class UsuarioUpd(BaseModel):
    nombre: str
    email: EmailStr

# ---------- Endpoints ---------- #
@app.get("/test",tags=["test"])
def test():
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    return {"status":"ok"}

@app.get("/usuarios", response_model=List[UsuarioOut], tags=["usuarios"])
def listar_usuarios(
    q: Optional[str] = Query(None, description="Buscar por nombre o email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    sql = "select id, nombre, email from usuario "
    params={}
    if q:
        sql += " where nombre like :q or email like :q "
        params["q"]= f"%{q}%"
    sql += " order by id asc limit :limit offset :offset "
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {**params, "limit":limit, "offset":offset}).mappings().all()
        return [UsuarioOut(**row) for row in rows]
    
@app.get("/usuarios/{usuario_id}", response_model=UsuarioOut, tags=["usuarios"])
def obtener_usuario(usuario_id):
    sql = "select id, nombre, email from usuario where id = :id "
    params = {"id": usuario_id}
    with engine.connect() as conn:
        row = conn.execute(text(sql),params).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UsuarioOut(**row)

@app.post("/usuarios", response_model=UsuarioOut, status_code=201, tags=["usuarios"])
def crear_usuario(usuario: UsuarioIn):
    sqlins = "insert into usuario (nombre, email) values ( :nombre, :email)"
    sqlsel = "select id, nombre, email from usuario where id = :id "
    paramsins = {
        "nombre": usuario.nombre,
        "email": usuario.email
    }
    with engine.begin() as conn:
        res = conn.execute(text(sqlins), paramsins)
        new_id = res.lastrowid
        paramssel = {"id":new_id}
        row = conn.execute(text(sqlsel), paramssel).mappings().first()
        return UsuarioOut(**row)

@app.put("/usuarios/{usuario_id}", response_model=UsuarioOut, tags=["usuarios"])
def actualizar_usuario(usuario_id: int, datos: UsuarioUpd):
    sql_upd = "update usuario set nombre=:nombre, email=:email where id=:id"
    sql_sel = "select id, nombre, email from usuario where id=:id"
    with engine.begin() as conn:
        res = conn.execute(text(sql_upd), {"id": usuario_id, "nombre": datos.nombre, "email": datos.email})
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        row = conn.execute(text(sql_sel), {"id": usuario_id}).mappings().first()
        return UsuarioOut(**row)

@app.delete("/usuarios/{usuario_id}", status_code=204, tags=["usuarios"])
def eliminar_usuario(usuario_id: int):
    sql_del = "delete from usuario where id=:id"
    with engine.begin() as conn:
        res = conn.execute(text(sql_del), {"id": usuario_id})
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return Response(status_code=204)