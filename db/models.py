import os
import uuid
from datetime import UTC, datetime, date
from dotenv import load_dotenv
from pydantic import field_validator
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine
from enum import Enum

load_dotenv()


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserType(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    RECRUITER = "reclutador"

class DocumentType(str, Enum):
    CURP = "CURP"
    ACTA_NACIMIENTO = "Acta de Nacimiento" 
    INE = "INE"
    COMPROBANTE_DOMICILIO ="Comprobante de Domicilio"
    RFC = "RFC"
    NSS= "NSS"
    ESTADO_CUENTA= "Estado de Cuenta"
    COMPROBANTE_ESTUDIOS="Comprobante de Estudios"
    INE_FAMILIAR= "Ine de un Familiar"
    COMPROBANTE_DOMICILIO_FAMILIAR="Comprobante de Domicilio de un Familiar"
    CARTA_ANTECEDENTES="Carta de no Antecedentes Penales"
    LICENCIA ="Permiso de Conducir"


class TimestampMixin(SQLModel):
    __abstract__ = True

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column_kwargs={"onupdate": utc_now}
    )


# ---------------------------------------------------------------------------
# Usuario
# ---------------------------------------------------------------------------

class Usuario(TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    avatar: str | None = Field(default=None)
    password: str
    user_type: UserType = Field(default=UserType.RECRUITER)
    empresas: list["Empresa"] = Relationship(back_populates="creador")


class UsuarioUpdate(SQLModel):
    name: str | None = None
    avatar: str | None = None


class UsuarioCreate(SQLModel):
    name: str
    email: str
    password: str
    user_type: UserType = UserType.RECRUITER


class PasswordChange(SQLModel):
    current_password: str
    new_password: str


class AdminUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    user_type: UserType | None = None
    password: str | None = None


class Login(SQLModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------

class Empresa(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rfc: str | None = Field(default=None, index=True, unique=True)
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    creador: Usuario | None = Relationship(back_populates="empresas")
    puestos: list["Puesto"] = Relationship(back_populates="empresa", cascade_delete=True)


class EmpresaCreate(SQLModel):
    name: str
    rfc: str | None = None


class EmpresaUpdate(SQLModel):
    name: str | None = None
    rfc: str | None = None


# ---------------------------------------------------------------------------
# Puesto
# ---------------------------------------------------------------------------

class Puesto(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    salary: float | None = Field(default=None, index=True)
    start_date: date | None = Field(default=None, index=True)
    end_date: date | None = Field(default=None, index=True)
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    empresa_id: int | None = Field(default=None, foreign_key="empresa.id", ondelete="CASCADE")
    empresa: Empresa | None = Relationship(back_populates="puestos")
    postulaciones: list["Postulacion"] = Relationship(back_populates="puesto", cascade_delete=True)


class PuestoCreate(SQLModel):
    name: str
    salary: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    empresa_id: int


class PuestoUpdate(SQLModel):
    name: str | None = None
    salary: float | None = None
    start_date: date | None = None
    end_date: date | None = None


# ---------------------------------------------------------------------------
# Candidato
# ---------------------------------------------------------------------------

class Candidato(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str | None = Field(default=None, index=True, unique=True)
    telefono: str | None = Field(default=None, index=True)
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    postulaciones: list["Postulacion"] = Relationship(back_populates="candidato", cascade_delete=True)
    papeleria: list["Papeleria"] = Relationship(back_populates="candidato", cascade_delete=True)


class CandidatoCreate(SQLModel):
    name: str
    email: str | None = None
    telefono: str | None = None


class CandidatoUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    telefono: str | None = None


# ---------------------------------------------------------------------------
# Postulacion
# ---------------------------------------------------------------------------

class Postulacion(TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str | None = Field(default=None, index=True)
    first_contact: date = Field(default_factory=date.today)
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    candidato_id: int = Field(foreign_key="candidato.id", ondelete="CASCADE")
    puesto_id: int = Field(foreign_key="puesto.id", ondelete="CASCADE")
    candidato: Candidato | None = Relationship(back_populates="postulaciones")
    puesto: Puesto | None = Relationship(back_populates="postulaciones")
    entrevistas: list["Entrevista"] = Relationship(back_populates="postulacion", cascade_delete=True)


class PostulacionCreate(SQLModel):
    candidato_id: int
    puesto_id: int
    status: str | None = None


class PostulacionUpdate(SQLModel):
    status: str | None = None
    puesto_id: int | None = None


# ---------------------------------------------------------------------------
# Entrevista
# ---------------------------------------------------------------------------

class Entrevista(TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    date: datetime | None = Field(default=None, index=True)
    encargado: str = Field(index=True)
    comentarios: str
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    postulacion_id: int = Field(foreign_key="postulacion.id", ondelete="CASCADE")
    postulacion: Postulacion | None = Relationship(back_populates="entrevistas")


class EntrevistaCreate(SQLModel):
    date: datetime | None = None
    encargado: str
    comentarios: str
    postulacion_id: int

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



# ---------------------------------------------------------------------------
# Papeleria
# ---------------------------------------------------------------------------

class Papeleria(TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_type: DocumentType
    file_name: str
    file_url: str
    created_by: uuid.UUID = Field(foreign_key="usuario.id")
    candidato_id: int = Field(foreign_key="candidato.id", ondelete="CASCADE")
    candidato: Candidato | None = Relationship(back_populates="papeleria")


class PapeleriaCreate(SQLModel):
    candidato_id: int
    document_type: DocumentType
    file_name: str
    file_url: str


class PapeleriaUpdate(SQLModel):
    document_type: DocumentType | None = None
    file_name: str | None = None
    file_url: str | None = None


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=2,
        max_overflow=0,
        pool_pre_ping=True,
        connect_args={"options": "-c prepared_statement_cache_size=0"},
    )
else:
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session