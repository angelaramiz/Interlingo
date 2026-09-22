package com.interlingo.app.llm

import com.interlingo.app.data.LearningApi
import com.interlingo.app.model.DiagnosticoPregunta
import com.interlingo.app.model.DiagnosticoResultado
import com.interlingo.app.model.EvaluacionResponse
import com.interlingo.app.model.EvaluacionResultado
import com.interlingo.app.model.Leccion
import com.interlingo.app.model.MetaResponse
import com.interlingo.app.model.Plan
import com.interlingo.app.model.PlanNivel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

class LocalEngine : LearningApi {

    private val json = Json { ignoreUnknownKeys = true }

    private data class MetaLocal(val tema: String, val idioma: String)

    private data class EvalInfo(
        val pregunta: String,
        val tipo: String,
        val respuestaCorrecta: String,
        val tema: String,
        val nivelId: Int,
        val idioma: String,
    )

    private val metaInfo = mutableMapOf<Int, MetaLocal>()
    private val nivelInfo = mutableMapOf<Int, PlanNivel>()
    private val evals = mutableMapOf<Int, EvalInfo>()
    private val historial = mutableListOf<String>()

    private var nextMetaId = 1
    private var nextNivelId = 1
    private var nextEvalId = 1

    private suspend inline fun <reified T> completeJson(user: String): T =
        withContext(Dispatchers.Default) {
            val prompt = PromptEngine.buildChatPrompt(PromptEngine.systemBase, user)
            val raw = LlmEngine.complete(prompt, 1536)
            json.decodeFromString<T>(PromptEngine.extractJson(raw))
        }

    override suspend fun crearMeta(texto: String, idiomaObjetivo: String): MetaResponse {
        val r = completeJson<MetaTemaRaw>(PromptEngine.interpretarMetaUser(texto, idiomaObjetivo))
        val id = nextMetaId++
        metaInfo[id] = MetaLocal(r.tema, idiomaObjetivo)
        return MetaResponse(meta_id = id, usuario_id = 1, tema = r.tema)
    }

    override suspend fun obtenerDiagnostico(metaId: Int): List<DiagnosticoPregunta> {
        val meta = metaInfo[metaId] ?: throw IllegalStateException("Meta desconocida")
        val r = completeJson<DiagnosticoResultado>(
            PromptEngine.diagnosticoUser(meta.tema, listOf(meta.tema), meta.idioma)
        )
        return r.preguntas
    }

    override suspend fun enviarDiagnostico(metaId: Int, respuestas: List<String>): Plan {
        val meta = metaInfo[metaId] ?: throw IllegalStateException("Meta desconocida")
        val diag = respuestas.joinToString("; ")
        val r = completeJson<PlanRaw>(
            PromptEngine.planUser(meta.tema, listOf(meta.tema), meta.idioma, diag)
        )
        val niveles = r.niveles.map { nv ->
            val id = nextNivelId++
            PlanNivel(
                id = id,
                numero = nv.numero,
                objetivo = nv.objetivo,
                tipo_actividad = nv.tipo_actividad,
                criterio_exito = nv.criterio_exito,
            ).also { nivelInfo[id] = it }
        }
        return Plan(niveles = niveles)
    }

    override suspend fun generarLeccion(nivelId: Int): Leccion {
        val nv = nivelInfo[nivelId] ?: throw IllegalStateException("Nivel desconocido")
        val meta = metaInfo.values.firstOrNull() ?: MetaLocal(nv.objetivo, "en")
        val nivelJson = "{\"numero\":${nv.numero},\"objetivo\":\"${nv.objetivo.escape()}\"}"
        return completeJson(
            PromptEngine.leccionUser(meta.tema, nivelJson, meta.idioma, "A1", nv.numero)
        )
    }

    override suspend fun generarEvaluacion(nivelId: Int): EvaluacionResponse {
        val nv = nivelInfo[nivelId] ?: throw IllegalStateException("Nivel desconocido")
        val meta = metaInfo.values.firstOrNull() ?: MetaLocal(nv.objetivo, "en")
        val nivelJson = "{\"numero\":${nv.numero},\"objetivo\":\"${nv.objetivo.escape()}\"}"
        val r = completeJson<EvalRaw>(
            PromptEngine.evaluacionUser(meta.tema, nivelJson, meta.idioma, "A1")
        )
        val id = nextEvalId++
        evals[id] = EvalInfo(r.pregunta, r.tipo, r.respuesta_correcta, meta.tema, nivelId, meta.idioma)
        return EvaluacionResponse(id = id, tipo = r.tipo, pregunta = r.pregunta, opciones = r.opciones)
    }

    override suspend fun responderEvaluacion(evaluacionId: Int, respuesta: String): EvaluacionResultado {
        val info = evals[evaluacionId] ?: throw IllegalStateException("Evaluacion desconocida")
        val corr = completeJson<CorrRaw>(
            PromptEngine.correccionUser(
                info.pregunta, info.tipo, info.respuestaCorrecta, respuesta, info.idioma
            )
        )
        val correcta = corr.correcta
        val ri = if (correcta) 1.0 else 0.0
        val rt = if (correcta) 1.0 else 0.0
        val tipoError = corr.tipo_error.ifBlank { "concepto" }
        val resultadoJson = "{\"tipo_error\":\"$tipoError\"}"
        val aj = completeJson<AjRaw>(
            PromptEngine.ajusteUser(resultadoJson, ri, rt, historial.joinToString("; "))
        )
        historial.add("$tipoError:${aj.decision}")
        return EvaluacionResultado(
            correcta = correcta,
            explicacion = corr.explicacion,
            tipo_error = tipoError,
            ruta_idioma_score = ri,
            ruta_tema_score = rt,
            decision = aj.decision,
        )
    }

    private fun String.escape(): String = replace("\"", "'")

    @Serializable
    private data class MetaTemaRaw(
        val tema: String,
        val conceptos: List<String> = emptyList(),
    )

    @Serializable
    private data class PlanNivelRaw(
        val numero: Int,
        val objetivo: String,
        val tipo_actividad: String = "",
        val criterio_exito: String = "",
    )

    @Serializable
    private data class PlanRaw(val niveles: List<PlanNivelRaw>)

    @Serializable
    private data class EvalRaw(
        val tipo: String = "opcion_multiple",
        val pregunta: String,
        val opciones: List<String>? = null,
        val respuesta_correcta: String = "",
    )

    @Serializable
    private data class CorrRaw(
        val explicacion: String = "",
        val tipo_error: String = "concepto",
        val correcta: Boolean = false,
    )

    @Serializable
    private data class AjRaw(
        val decision: String = "repetir",
        val justificacion: String = "",
        val nivel_cefr_ajustado: String = "A1",
    )
}
