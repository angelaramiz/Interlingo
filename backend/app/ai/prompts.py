import json

from ..config import settings

LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "de": "German",
    "it": "Italian",
}

JSON_INSTRUCTION = (
    "Responde SOLO con un JSON válido, sin texto adicional, "
    "siguiendo exactamente el esquema indicado."
)


def _lang(idioma: str) -> str:
    return LANGUAGE_NAMES.get(idioma, idioma)


def system_base() -> str:
    return (
        "Eres LengLearning, un motor adaptativo que enseña un idioma usando "
        "un tema de interés como vehículo. El tema es el vehículo; el idioma "
        "es la habilidad principal. Controlas dos rutas de progreso en paralelo: "
        "ruta de idioma (vocabulario, gramática, comprensión, producción) y ruta "
        "de tema (conceptos, complejidad técnica, casos prácticos). "
        "IMPORTANTE: Todo el contenido que generes DEBE estar escrito en el "
        "idioma objetivo que indique el usuario, nunca en otro idioma."
    )


def interpretar_meta(meta_texto: str, idioma: str) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Interpreta la meta libre del usuario y descomponla en tema, "
                "conceptos clave, habilidades, artefactos y tareas reales.\n"
                f"Idioma objetivo (escribe el tema en este idioma): {_lang(idioma)}\n"
                f"Meta del usuario: {meta_texto}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"tema\": str, \"conceptos\": [str], "
                "\"nivel_cefr_estimado\": str, \"nivel_tema_estimado\": int}"
            ),
        },
    ]


def diagnostico(tema: str, conceptos: list[str], idioma: str) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Crea 3-5 preguntas breves de opción múltiple para estimar el "
                "conocimiento previo del tema Y el nivel de idioma del usuario.\n"
                f"Tema: {tema}\nConceptos: {', '.join(conceptos)}\n"
                f"Idioma objetivo (escribe las preguntas en este idioma): {_lang(idioma)}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"preguntas\": [{\"id\": int, \"pregunta\": str, "
                "\"opciones\": [str]}]}"
            ),
        },
    ]


def plan(tema: str, conceptos: list[str], idioma: str, diag: str) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Genera un plan adaptativo de 5 niveles con dificultad progresiva. "
                "Cada nivel combina la ruta de idioma y la ruta de tema. "
                "Las actividades evolucionan: comprensión lectora → producción "
                "guiada → respuestas escritas → explicación propia.\n"
                f"Tema: {tema}\nConceptos: {', '.join(conceptos)}\n"
                f"Idioma objetivo: {_lang(idioma)}\n"
                f"Resultado del diagnóstico: {diag}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"niveles\": [{\"numero\": int, \"objetivo\": str, "
                "\"tipo_actividad\": str, \"criterio_exito\": str}]}"
            ),
        },
    ]


def leccion(tema: str, nivel: dict, idioma: str, nivel_cefr: str, nivel_tema: int) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Crea una lección breve en el idioma objetivo. "
                "Controla: nivel de idioma, % de vocabulario conocido, longitud "
                "de oraciones, conectores permitidos, cantidad de palabras nuevas "
                "y tipo de pregunta.\n"
                f"Tema: {tema}\nNivel del plan: {json.dumps(nivel)}\n"
                f"Nivel de idioma (CEFR): {nivel_cefr}\nNivel de tema: {nivel_tema}\n"
                f"Idioma objetivo (escribe TODO el contenido en este idioma): {_lang(idioma)}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"titulo\": str, \"texto\": str, "
                "\"vocabulario\": [{\"termino\": str, \"traduccion\": str, "
                "\"definicion\": str}]}"
            ),
        },
    ]


def evaluacion_pregunta(tema: str, nivel: dict, idioma: str, nivel_cefr: str) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Crea una pregunta de evaluación acorde al nivel. Si el nivel es "
                "básico usa opción múltiple; en niveles avanzados pide respuesta "
                "escrita o explicación propia del tema en el idioma objetivo.\n"
                f"Tema: {tema}\nNivel del plan: {json.dumps(nivel)}\n"
                f"Nivel de idioma (CEFR): {nivel_cefr}\n"
                f"Idioma objetivo (escribe la pregunta y opciones en este idioma): {_lang(idioma)}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"tipo\": str, \"pregunta\": str, "
                "\"opciones\": [str] o null, \"respuesta_correcta\": str}"
            ),
        },
    ]


def correccion(
    pregunta: str,
    tipo: str,
    respuesta_correcta: str,
    respuesta_usuario: str,
    idioma: str,
) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Corrige la respuesta y explica brevemente por qué es correcta o "
                "incorrecta. Señala si el fallo fue de idioma o de concepto.\n"
                f"Pregunta: {pregunta}\nTipo: {tipo}\n"
                f"Respuesta correcta: {respuesta_correcta}\n"
                f"Respuesta del usuario: {respuesta_usuario}\n"
                f"Idioma objetivo: {_lang(idioma)}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"explicacion\": str, \"tipo_error\": \"idioma\" | "
                "\"concepto\", \"correcta\": bool}"
            ),
        },
    ]


def ajuste(
    resultado: str,
    ruta_idioma_score: float,
    ruta_tema_score: float,
    historial: str,
) -> list[dict]:
    return [
        {"role": "system", "content": system_base()},
        {
            "role": "user",
            "content": (
                "Decide la siguiente acción para el nivel siguiente. "
                "Si falla el idioma → baja dificultad lingüística. "
                "Si falla el concepto → simplifica la explicación técnica. "
                "Si ambos van bien → profundiza o avanza.\n"
                f"Resultado de la evaluación: {resultado}\n"
                f"Ruta idioma score: {ruta_idioma_score}\nRuta tema score: {ruta_tema_score}\n"
                f"Historial del usuario: {historial}\n\n"
                + JSON_INSTRUCTION
                + "\nEsquema: {\"decision\": \"avanzar\" | \"repetir\" | "
                "\"simplificar\" | \"profundizar\", \"justificacion\": str, "
                "\"nivel_cefr_ajustado\": str}"
            ),
        },
    ]


def build_messages(template: list[dict], **kwargs) -> list[dict]:
    return [dict(m) for m in template]