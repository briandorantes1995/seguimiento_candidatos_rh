import uuid
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class Usuario(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    password: str = Field(index=True)
    user_type: str = Field(default="user",index=True)

class Login(SQLModel):
    email: str = Field(index=True)
    password: str = Field(index=True)

class Empresa(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rfc: str | None = Field(default=None, index=True)
    puestos: list["Puesto"] = Relationship(back_populates="empresa", cascade_delete=True)

class EmpresaUpdate(SQLModel):
    name: str | None = None
    rfc: str | None = None    

class Puesto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    salary: float | None = Field(default=None, index=True)
    stardate: str | None = Field(default=None, index=True)
    enddate: str | None = Field(default=None, index=True)
    candidatos: list["Candidato"] = Relationship(back_populates="puesto", cascade_delete=True)
    empresa_id: int | None = Field(default=None, foreign_key="empresa.id", ondelete="CASCADE")
    empresa: Empresa | None = Relationship(back_populates="puestos")

class PuestoUpdate(SQLModel):
    name: str | None = None
    salary: float | None = None
    stardate: str | None = None
    enddate: str | None = None    

class Candidato(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rfc: str | None = Field(default=None, index=True)
    puesto_id: int | None = Field(default=None, foreign_key="puesto.id", ondelete="CASCADE")
    puesto: Puesto | None = Relationship(back_populates="candidatos")

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
