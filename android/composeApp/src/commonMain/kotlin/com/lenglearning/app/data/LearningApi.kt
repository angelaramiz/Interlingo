package com.lenglearning.app.data

import com.lenglearning.app.model.DiagnosticoPregunta
import com.lenglearning.app.model.EvaluacionResponse
import com.lenglearning.app.model.EvaluacionResultado
import com.lenglearning.app.model.Leccion
import com.lenglearning.app.model.MetaResponse
import com.lenglearning.app.model.Plan

interface LearningApi {
    suspend fun crearMeta(texto: String, idiomaObjetivo: String): MetaResponse
    suspend fun obtenerDiagnostico(metaId: Int): List<DiagnosticoPregunta>
    suspend fun enviarDiagnostico(metaId: Int, respuestas: List<String>): Plan
    suspend fun generarLeccion(nivelId: Int): Leccion
    suspend fun generarEvaluacion(nivelId: Int): EvaluacionResponse
    suspend fun responderEvaluacion(evaluacionId: Int, respuesta: String): EvaluacionResultado
}