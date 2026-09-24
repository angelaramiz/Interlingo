package com.interlingo.app.data

import com.interlingo.app.model.DiagnosticoPregunta
import com.interlingo.app.model.DiagnosticoResultado
import com.interlingo.app.model.DiagnosticoRespuestas
import com.interlingo.app.model.DiccionarioRequest
import com.interlingo.app.model.DiccionarioResponse
import com.interlingo.app.model.EvaluacionResponse
import com.interlingo.app.model.EvaluacionResultado
import com.interlingo.app.model.EvaluacionSubmit
import com.interlingo.app.model.Leccion
import com.interlingo.app.model.MetaRequest
import com.interlingo.app.model.MetaResponse
import com.interlingo.app.model.MetaResumen
import com.interlingo.app.model.Plan
import com.interlingo.app.model.PlanNivel
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

class ApiClient(
    private val baseUrl: String = "http://10.0.2.2:8000",
) : LearningApi {
    private val client = HttpClient {
        install(ContentNegotiation) {
            json(
                Json {
                    ignoreUnknownKeys = true
                    isLenient = true
                }
            )
        }
        install(HttpTimeout) {
            connectTimeoutMillis = 15000
            socketTimeoutMillis = 120000
            requestTimeoutMillis = 300000
        }
    }

    override suspend fun crearMeta(texto: String, idiomaObjetivo: String): MetaResponse =
        client.post("$baseUrl/api/meta") {
            contentType(ContentType.Application.Json)
            setBody(MetaRequest(texto = texto, idioma_objetivo = idiomaObjetivo))
        }.body()

    override suspend fun obtenerDiagnostico(metaId: Int): List<DiagnosticoPregunta> =
        client.get("$baseUrl/api/diagnostico/$metaId").body<DiagnosticoResultado>().preguntas

    override suspend fun enviarDiagnostico(metaId: Int, respuestas: List<String>): Plan =
        client.post("$baseUrl/api/diagnostico/$metaId/resultado") {
            contentType(ContentType.Application.Json)
            setBody(DiagnosticoRespuestas(respuestas = respuestas))
        }.body()

    override suspend fun generarLeccion(nivelId: Int): Leccion =
        client.post("$baseUrl/api/leccion/$nivelId").body()

    override suspend fun generarEvaluacion(nivelId: Int): EvaluacionResponse =
        client.post("$baseUrl/api/evaluacion/$nivelId/generar").body()

    override suspend fun responderEvaluacion(evaluacionId: Int, respuesta: String): EvaluacionResultado =
        client.post("$baseUrl/api/evaluacion/$evaluacionId/responder") {
            contentType(ContentType.Application.Json)
            setBody(EvaluacionSubmit(respuesta = respuesta))
        }.body()

    override suspend fun listarMetas(): List<MetaResumen> =
        client.get("$baseUrl/api/metas").body()

    override suspend fun obtenerNiveles(metaId: Int): List<PlanNivel> =
        client.get("$baseUrl/api/meta/$metaId/niveles").body()

    override suspend fun buscarDefinicion(
        palabra: String,
        idiomaObjetivo: String,
        idiomaNativo: String,
        contexto: String,
    ): DiccionarioResponse =
        client.post("$baseUrl/api/diccionario") {
            contentType(ContentType.Application.Json)
            setBody(
                DiccionarioRequest(
                    palabra = palabra,
                    idioma_objetivo = idiomaObjetivo,
                    idioma_nativo = idiomaNativo,
                    contexto = contexto,
                )
            )
        }.body()
}
