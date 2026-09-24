from pydantic import BaseModel, Field
from typing import Optional


class MetaCreate(BaseModel):
    texto: str
    idioma_objetivo: str = "en"
    idioma_nativo: str = "es"


class MetaInterpretada(BaseModel):
    tema: str
    conceptos: list[str]
    nivel_cefr_estimado: str
    nivel_tema_estimado: int


class DiagnosticoPregunta(BaseModel):
    id: int
    pregunta: str
    opciones: list[str]


class DiagnosticoResultado(BaseModel):
    preguntas: list[DiagnosticoPregunta]


class DiagnosticoRespuestas(BaseModel):
    respuestas: list[str]


class PlanNivel(BaseModel):
    numero: int
    objetivo: str
    tipo_actividad: str
    criterio_exito: str


class Plan(BaseModel):
    niveles: list[PlanNivel]


class VocabularioItem(BaseModel):
    termino: str
    traduccion: str
    definicion: str = ""


class Leccion(BaseModel):
    titulo: str
    texto: str
    vocabulario: list[VocabularioItem] = []


class EvaluacionPregunta(BaseModel):
    tipo: str
    pregunta: str
    opciones: Optional[list[str]] = None
    respuesta_correcta: str


class EvaluacionSubmit(BaseModel):
    respuesta: str


class EvaluacionResultado(BaseModel):
    correcta: bool
    explicacion: str
    tipo_error: str = ""
    ruta_idioma_score: float
    ruta_tema_score: float
    decision: str


class MetaResumen(BaseModel):
    id: int
    texto: str = ""
    tema: str = ""
    idioma_objetivo: str = "en"
    estado: str = ""


class AppVersionResponse(BaseModel):
    versionCode: int = 1
    versionName: str = "0.1.0"
    apkUrl: str = "/static/interlingo.apk"


class DiccionarioRequest(BaseModel):
    palabra: str
    idioma_objetivo: str = "en"
    idioma_nativo: str = "es"
    contexto: str = ""


class DiccionarioResponse(BaseModel):
    termino: str
    traduccion: str
    definicion: str = ""
    ejemplo: str = ""
