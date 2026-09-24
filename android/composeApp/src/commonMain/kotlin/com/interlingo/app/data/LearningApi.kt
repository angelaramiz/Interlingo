package com.interlingo.app.data

import com.interlingo.app.model.DiagnosticoPregunta
import com.interlingo.app.model.DiccionarioResponse
import com.interlingo.app.model.EvaluacionResponse
import com.interlingo.app.model.EvaluacionResultado
import com.interlingo.app.model.Leccion
import com.interlingo.app.model.MetaResponse
import com.interlingo.app.model.MetaResumen
import com.interlingo.app.model.Plan
import com.interlingo.app.model.PlanNivel

interface LearningApi {
    suspend fun crearMeta(texto: String, idiomaObjetivo: String): MetaResponse
    suspend fun obtenerDiagnostico(metaId: Int): List<DiagnosticoPregunta>
    suspend fun enviarDiagnostico(metaId: Int, respuestas: List<String>): Plan
    suspend fun generarLeccion(nivelId: Int): Leccion
    suspend fun generarEvaluacion(nivelId: Int): EvaluacionResponse
    suspend fun responderEvaluacion(evaluacionId: Int, respuesta: String): EvaluacionResultado
    suspend fun listarMetas(): List<MetaResumen>
    suspend fun obtenerNiveles(metaId: Int): List<PlanNivel>
    suspend fun buscarDefinicion(
        palabra: String,
        idiomaObjetivo: String = "en",
        idiomaNativo: String = "es",
        contexto: String = "",
    ): DiccionarioResponse
}