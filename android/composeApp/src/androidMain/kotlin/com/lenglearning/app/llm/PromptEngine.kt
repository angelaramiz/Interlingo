package com.lenglearning.app.llm

object PromptEngine {
    private val languageNames = mapOf(
        "en" to "English",
        "es" to "Spanish",
        "fr" to "French",
        "pt" to "Portuguese",
        "de" to "German",
        "it" to "Italian",
    )

    private const val jsonInstruction =
        "Responde SOLO con un JSON válido, sin texto adicional, siguiendo exactamente el esquema indicado."

    const val systemBase =
        "Eres LengLearning, un motor adaptativo que enseña un idioma usando " +
        "un tema de interés como vehículo. El tema es el vehículo; el idioma " +
        "es la habilidad principal. Controlas dos rutas de progreso en paralelo: " +
        "ruta de idioma (vocabulario, gramática, comprensión, producción) y ruta " +
        "de tema (conceptos, complejidad técnica, casos prácticos). " +
        "IMPORTANTE: Todo el contenido que generes DEBE estar escrito en el " +
        "idioma objetivo que indique el usuario, nunca en otro idioma."

    fun lang(code: String): String = languageNames[code] ?: code

    fun buildChatPrompt(system: String, user: String): String =
        "<|im_start|>system\n$system<|im_end|>\n" +
        "<|im_start|>user\n$user<|im_end|>\n" +
        "<|im_start|>assistant\n"

    fun interpretarMetaUser(metaTexto: String, idioma: String): String =
        "Interpreta la meta libre del usuario y descomponla en tema, " +
        "conceptos clave, habilidades, artefactos y tareas reales.\n" +
        "Idioma objetivo (escribe el tema en este idioma): ${lang(idioma)}\n" +
        "Meta del usuario: $metaTexto\n\n" + jsonInstruction +
        "\nEsquema: {\"tema\": str, \"conceptos\": [str], " +
        "\"nivel_cefr_estimado\": str, \"nivel_tema_estimado\": int}"

    fun diagnosticoUser(tema: String, conceptos: List<String>, idioma: String): String =
        "Crea 3-5 preguntas breves de opción múltiple para estimar el " +
        "conocimiento previo del tema Y el nivel de idioma del usuario.\n" +
        "Tema: $tema\nConceptos: ${conceptos.joinToString(", ")}\n" +
        "Idioma objetivo (escribe las preguntas en este idioma): ${lang(idioma)}\n\n" +
        jsonInstruction +
        "\nEsquema: {\"preguntas\": [{\"id\": int, \"pregunta\": str, " +
        "\"opciones\": [str]}]}"

    fun planUser(tema: String, conceptos: List<String>, idioma: String, diag: String): String =
        "Genera un plan adaptativo de 5 niveles con dificultad progresiva. " +
        "Cada nivel combina la ruta de idioma y la ruta de tema. " +
        "Las actividades evolucionan: comprensión lectora → producción " +
        "guiada → respuestas escritas → explicación propia.\n" +
        "Tema: $tema\nConceptos: ${conceptos.joinToString(", ")}\n" +
        "Idioma objetivo: ${lang(idioma)}\n" +
        "Resultado del diagnóstico: $diag\n\n" + jsonInstruction +
        "\nEsquema: {\"niveles\": [{\"numero\": int, \"objetivo\": str, " +
        "\"tipo_actividad\": str, \"criterio_exito\": str}]}"

    fun leccionUser(tema: String, nivel: String, idioma: String, nivelCefr: String, nivelTema: Int): String =
        "Crea una lección breve en el idioma objetivo. " +
        "Controla: nivel de idioma, % de vocabulario conocido, longitud " +
        "de oraciones, conectores permitidos, cantidad de palabras nuevas " +
        "y tipo de pregunta.\n" +
        "Tema: $tema\nNivel del plan: $nivel\n" +
        "Nivel de idioma (CEFR): $nivelCefr\nNivel de tema: $nivelTema\n" +
        "Idioma objetivo (escribe TODO el contenido en este idioma): ${lang(idioma)}\n\n" +
        jsonInstruction +
        "\nEsquema: {\"titulo\": str, \"texto\": str, " +
        "\"vocabulario\": [{\"termino\": str, \"traduccion\": str, " +
        "\"definicion\": str}]}"

    fun evaluacionUser(tema: String, nivel: String, idioma: String, nivelCefr: String): String =
        "Crea una pregunta de evaluación acorde al nivel. Si el nivel es " +
        "básico usa opción múltiple; en niveles avanzados pide respuesta " +
        "escrita o explicación propia del tema en el idioma objetivo.\n" +
        "Tema: $tema\nNivel del plan: $nivel\n" +
        "Nivel de idioma (CEFR): $nivelCefr\n" +
        "Idioma objetivo (escribe la pregunta y opciones en este idioma): ${lang(idioma)}\n\n" +
        jsonInstruction +
        "\nEsquema: {\"tipo\": str, \"pregunta\": str, " +
        "\"opciones\": [str] o null, \"respuesta_correcta\": str}"

    fun correccionUser(
        pregunta: String,
        tipo: String,
        correcta: String,
        usuario: String,
        idioma: String,
    ): String =
        "Corrige la respuesta y explica brevemente por qué es correcta o " +
        "incorrecta. Señala si el fallo fue de idioma o de concepto.\n" +
        "Pregunta: $pregunta\nTipo: $tipo\n" +
        "Respuesta correcta: $correcta\n" +
        "Respuesta del usuario: $usuario\n" +
        "Idioma objetivo: ${lang(idioma)}\n\n" + jsonInstruction +
        "\nEsquema: {\"explicacion\": str, \"tipo_error\": \"idioma\" | " +
        "\"concepto\", \"correcta\": bool}"

    fun ajusteUser(
        resultado: String,
        rutaIdioma: Double,
        rutaTema: Double,
        historial: String,
    ): String =
        "Decide la siguiente acción para el nivel siguiente. " +
        "Si falla el idioma → baja dificultad lingüística. " +
        "Si falla el concepto → simplifica la explicación técnica. " +
        "Si ambos van bien → profundiza o avanza.\n" +
        "Resultado de la evaluación: $resultado\n" +
        "Ruta idioma score: $rutaIdioma\nRuta tema score: $rutaTema\n" +
        "Historial del usuario: $historial\n\n" + jsonInstruction +
        "\nEsquema: {\"decision\": \"avanzar\" | \"repetir\" | " +
        "\"simplificar\" | \"profundizar\", \"justificacion\": str, " +
        "\"nivel_cefr_ajustado\": str}"

    fun extractJson(raw: String): String {
        val cleaned = raw.trim()
        val start = cleaned.indexOf('{')
        val end = cleaned.lastIndexOf('}')
        if (start == -1 || end == -1 || end < start) return cleaned
        return cleaned.substring(start, end + 1)
    }
}
