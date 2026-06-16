import uuid
from datetime import UTC,datetime,date
from pydantic import field_validator
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine
from enum import Enum

def utc_now() -> datetime:
    return datetime.now(UTC)

class UserType(str, Enum):
    ADMIN = "admin"
    USER = "user"


class TimestampMixin(SQLModel):
    __abstract__ = True

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now}
    )

class Usuario(TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    password: str
    user_type: UserType = Field(default=UserType.USER)


class Login(SQLModel):
    email: str
    password: str

class Empresa(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rfc: str | None = Field(default=None, index=True, unique=True)
    puestos: list["Puesto"] = Relationship(back_populates="empresa", cascade_delete=True)


class EmpresaUpdate(SQLModel):
    name: str | None = None
    rfc: str | None = None    

class Puesto(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    salary: float | None = Field(default=None, index=True)
    start_date: date | None = Field(default=None, index=True)
    end_date: date | None = Field(default=None, index=True)
    candidatos: list["Candidato"] = Relationship(back_populates="puesto", cascade_delete=True)
    empresa_id: int | None = Field(default=None, foreign_key="empresa.id", ondelete="CASCADE")
    empresa: Empresa | None = Relationship(back_populates="puestos")

class PuestoUpdate(SQLModel):
    name: str | None = None
    salary: float | None = None
    start_date: date | None = None
    end_date: date | None = None    


class Candidato(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    status: str | None = Field(default=None, index=True)
    first_contact: date = Field(default_factory=date.today)
    puesto_id: int | None = Field(default=None, foreign_key="puesto.id", ondelete="CASCADE")
    puesto: Puesto | None = Relationship(back_populates="candidatos")
    entrevistas: list["Entrevista"] = Relationship(back_populates="candidato", cascade_delete=True)

class CandidatoUpdate(SQLModel):
    name: str | None = None
    status: str | None = None
    puesto_id: int | None = None

class Entrevista(TimestampMixin,table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date: datetime | None = Field(default=None, index=True)
    encargado: str = Field(index=True)
    comentarios: str
    candidato_id: int | None = Field(default=None, foreign_key="candidato.id", ondelete="CASCADE")
    candidato: Candidato | None = Relationship(back_populates="entrevistas")

class EntrevistaCreate(SQLModel):
    date: datetime | None = None
    encargado: str
    comentarios: str
    candidato_id: int 

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class EntrevistaUpdate(SQLModel):
    date: datetime | None = None
    encargado: str | None = None
    comentarios: str | None = None    





sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
