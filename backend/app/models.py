from sqlalchemy import Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=True)
    idioma_objetivo = Column(String(10), default="en")
    idioma_nativo = Column(String(10), default="es")
    nivel_cefr = Column(String(10), default="A1")

    metas = relationship("Meta", back_populates="usuario")


class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    texto = Column(Text)
    tema = Column(String(200))
    idioma_objetivo = Column(String(10), default="en")
    estado = Column(String(20), default="diagnostico")

    usuario = relationship("Usuario", back_populates="metas")
    niveles = relationship("Nivel", back_populates="meta", cascade="all, delete-orphan")
    trazas = relationship("Traza", back_populates="meta")


class Nivel(Base):
    __tablename__ = "niveles"

    id = Column(Integer, primary_key=True)
    meta_id = Column(Integer, ForeignKey("metas.id"))
    numero = Column(Integer)
    objetivo = Column(Text)
    tipo_actividad = Column(String(50), nullable=True)
    contenido = Column(Text)
    vocabulario = Column(JSON, default=list)
    criterio_exito = Column(Text)
    estado = Column(String(20), default="pendiente")

    meta = relationship("Meta", back_populates="niveles")
    evaluaciones = relationship("Evaluacion", back_populates="nivel", cascade="all, delete-orphan")


class Evaluacion(Base):
    __tablename__ = "evaluaciones"

    id = Column(Integer, primary_key=True)
    nivel_id = Column(Integer, ForeignKey("niveles.id"))
    tipo = Column(String(30))
    pregunta = Column(Text)
    opciones = Column(JSON, default=list)
    respuesta_correcta = Column(Text)
    respuesta_usuario = Column(Text, nullable=True)
    correcta = Column(Integer, default=0)
    ruta_idioma_score = Column(Float, default=0.0)
    ruta_tema_score = Column(Float, default=0.0)

    nivel = relationship("Nivel", back_populates="evaluaciones")


class Traza(Base):
    __tablename__ = "traza"

    id = Column(Integer, primary_key=True)
    meta_id = Column(Integer, ForeignKey("metas.id"))
    evaluacion_id = Column(Integer, ForeignKey("evaluaciones.id"), nullable=True)
    tipo_error = Column(String(20))
    detalle = Column(Text)
    decision = Column(String(30))

    meta = relationship("Meta", back_populates="trazas")


class AppVersion(Base):
    __tablename__ = "app_versions"

    clave = Column(String(50), primary_key=True)
    valor = Column(JSON, default=dict)
