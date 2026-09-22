package com.lenglearning.app.model

import kotlinx.serialization.Serializable

@Serializable
data class MetaRequest(
    val texto: String,
    val idioma_objetivo: String = "en",
    val idioma_nativo: String = "es",
)

@Serializable
data class MetaResponse(
    val meta_id: Int,
    val usuario_id: Int,
    val tema: String,
)

@Serializable
data class DiagnosticoPregunta(
    val id: Int,
    val pregunta: String,
    val opciones: List<String> = emptyList(),
)

@Serializable
data class DiagnosticoResultado(
    val preguntas: List<DiagnosticoPregunta>,
)

@Serializable
data class DiagnosticoRespuestas(
    val respuestas: List<String>,
)

@Serializable
data class PlanNivel(
    val id: Int,
    val numero: Int,
    val objetivo: String,
    val tipo_actividad: String = "",
    val criterio_exito: String = "",
)

@Serializable
data class Plan(
    val niveles: List<PlanNivel>,
)

@Serializable
data class VocabularioItem(
    val termino: String,
    val traduccion: String,
    val definicion: String = "",
)

@Serializable
data class Leccion(
    val titulo: String,
    val texto: String,
    val vocabulario: List<VocabularioItem> = emptyList(),
)

@Serializable
data class EvaluacionResponse(
    val id: Int,
    val tipo: String,
    val pregunta: String,
    val opciones: List<String>? = null,
)

@Serializable
data class EvaluacionSubmit(
    val respuesta: String,
)

@Serializable
data class EvaluacionResultado(
    val correcta: Boolean,
    val explicacion: String = "",
    val tipo_error: String = "",
    val ruta_idioma_score: Double = 0.0,
    val ruta_tema_score: Double = 0.0,
    val decision: String = "",
)
