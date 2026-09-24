package com.interlingo.app

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.interlingo.app.data.LearningApi
import com.interlingo.app.model.DiagnosticoPregunta
import com.interlingo.app.model.DiccionarioResponse
import com.interlingo.app.model.EvaluacionResponse
import com.interlingo.app.model.EvaluacionResultado
import com.interlingo.app.model.Leccion as LeccionModel
import com.interlingo.app.model.MetaResumen
import com.interlingo.app.model.PlanNivel
import kotlinx.coroutines.launch

sealed interface UiState {
    data object Home : UiState
    data object Loading : UiState
    data class Diagnostico(
        val metaId: Int,
        val tema: String,
        val preguntas: List<DiagnosticoPregunta>,
    ) : UiState

    data class Plan(
        val niveles: List<PlanNivel>,
        val idiomaObjetivo: String = "en",
    ) : UiState

    data class Leccion(
        val niveles: List<PlanNivel>,
        val indice: Int,
        val leccion: LeccionModel,
        val idiomaObjetivo: String = "en",
    ) : UiState

    data class Evaluacion(
        val niveles: List<PlanNivel>,
        val indice: Int,
        val evaluacion: EvaluacionResponse,
        val idiomaObjetivo: String = "en",
    ) : UiState

    data class Resultado(
        val niveles: List<PlanNivel>,
        val indice: Int,
        val resultado: EvaluacionResultado,
        val idiomaObjetivo: String = "en",
    ) : UiState

    data class Error(val message: String) : UiState
}

private val idiomas = mapOf("en" to "Inglés", "es" to "Español", "fr" to "Francés")

@Composable
fun App(
    api: LearningApi,
    onManualUpdate: () -> Unit = {},
    updateStatus: String? = null,
    engineLabel: String? = null,
) {
    MaterialTheme {
        var state by remember { mutableStateOf<UiState>(UiState.Home) }
        var metaTexto by remember { mutableStateOf("") }
        var idioma by remember { mutableStateOf("en") }
        var sesiones by remember { mutableStateOf<List<MetaResumen>?>(null) }
        val scope = rememberCoroutineScope()

        androidx.compose.runtime.LaunchedEffect(Unit) {
            sesiones = try {
                api.listarMetas()
            } catch (e: Exception) {
                emptyList()
            }
        }

        Surface(modifier = Modifier.fillMaxSize()) {
            when (val s = state) {
                UiState.Home -> HomeScreen(
                    metaTexto = metaTexto,
                    idioma = idioma,
                    onMetaChange = { metaTexto = it },
                    onIdiomaChange = { idioma = it },
                    onManualUpdate = onManualUpdate,
                    updateStatus = updateStatus,
                    engineLabel = engineLabel,
                    sesiones = sesiones,
                    onContinuarSesion = { sesion ->
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val niveles = api.obtenerNiveles(sesion.id)
                                if (niveles.isNotEmpty()) {
                                    UiState.Plan(niveles, sesion.idioma_objetivo)
                                } else {
                                    val preguntas = api.obtenerDiagnostico(sesion.id)
                                    UiState.Diagnostico(sesion.id, sesion.tema, preguntas)
                                }
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                    onComenzar = {
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val meta = api.crearMeta(metaTexto, idioma)
                                val preguntas = api.obtenerDiagnostico(meta.meta_id)
                                UiState.Diagnostico(meta.meta_id, meta.tema, preguntas)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                UiState.Loading -> LoadingScreen()

                is UiState.Diagnostico -> DiagnosticoScreen(
                    tema = s.tema,
                    preguntas = s.preguntas,
                    onTerminar = { respuestas ->
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val plan = api.enviarDiagnostico(s.metaId, respuestas)
                                UiState.Plan(plan.niveles, idioma)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                is UiState.Plan -> PlanScreen(
                    niveles = s.niveles,
                    onIniciarNivel = { indice ->
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val leccion = api.generarLeccion(s.niveles[indice].id)
                                UiState.Leccion(s.niveles, indice, leccion, s.idiomaObjetivo)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                is UiState.Leccion -> LeccionScreen(
                    niveles = s.niveles,
                    indice = s.indice,
                    leccion = s.leccion,
                    onBuscarPalabra = { palabra ->
                        api.buscarDefinicion(palabra, s.idiomaObjetivo)
                    },
                    onEvaluacion = {
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val ev = api.generarEvaluacion(s.niveles[s.indice].id)
                                UiState.Evaluacion(s.niveles, s.indice, ev, s.idiomaObjetivo)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                is UiState.Evaluacion -> EvaluacionScreen(
                    niveles = s.niveles,
                    indice = s.indice,
                    evaluacion = s.evaluacion,
                    onResponder = { respuesta ->
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val resultado = api.responderEvaluacion(s.evaluacion.id, respuesta)
                                UiState.Resultado(s.niveles, s.indice, resultado, s.idiomaObjetivo)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                is UiState.Resultado -> ResultadoScreen(
                    niveles = s.niveles,
                    indice = s.indice,
                    resultado = s.resultado,
                    onContinuar = {
                        val avanzar = s.resultado.decision in listOf("avanzar", "profundizar")
                        val siguiente = if (avanzar && s.indice + 1 < s.niveles.size) s.indice + 1 else s.indice
                        scope.launch {
                            state = UiState.Loading
                            state = try {
                                val leccion = api.generarLeccion(s.niveles[siguiente].id)
                                UiState.Leccion(s.niveles, siguiente, leccion, s.idiomaObjetivo)
                            } catch (e: Exception) {
                                UiState.Error(mensajeError(e))
                            }
                        }
                    },
                )

                is UiState.Error -> ErrorScreen(
                    message = s.message,
                    onReintentar = { state = UiState.Home },
                )
            }
        }
    }
}

@Composable
private fun HomeScreen(
    metaTexto: String,
    idioma: String,
    onMetaChange: (String) -> Unit,
    onIdiomaChange: (String) -> Unit,
    onComenzar: () -> Unit,
    onManualUpdate: () -> Unit = {},
    updateStatus: String? = null,
    engineLabel: String? = null,
    sesiones: List<MetaResumen>? = null,
    onContinuarSesion: (MetaResumen) -> Unit = {},
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = "Interlingo", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(8.dp))
        Text(text = "Aprende un idioma mientras aprendes lo que te interesa")
        if (engineLabel != null) {
            Spacer(Modifier.height(4.dp))
            Text(engineLabel, style = MaterialTheme.typography.bodySmall)
        }
        Spacer(Modifier.height(24.dp))
        OutlinedTextField(
            value = metaTexto,
            onValueChange = onMetaChange,
            label = { Text("¿Qué quieres aprender?") },
            placeholder = { Text("Ej: hacer un ETL desde cero") },
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(16.dp))
        IdiomaSelector(idioma, onIdiomaChange)
        Spacer(Modifier.height(24.dp))
        Button(
            onClick = onComenzar,
            enabled = metaTexto.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Comenzar")
        }
        Spacer(Modifier.height(16.dp))
        OutlinedButton(
            onClick = onManualUpdate,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Buscar actualización")
        }
        if (updateStatus != null) {
            Spacer(Modifier.height(8.dp))
            Text(updateStatus, style = MaterialTheme.typography.bodySmall)
        }
        if (sesiones == null) {
            Spacer(Modifier.height(16.dp))
            Text("Cargando sesiones…", style = MaterialTheme.typography.bodySmall)
        } else if (sesiones.isNotEmpty()) {
            Spacer(Modifier.height(24.dp))
            Text("Mis sesiones", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            sesiones.forEach { sesion ->
                Card(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    onClick = { onContinuarSesion(sesion) },
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(
                            sesion.tema.ifBlank { sesion.texto },
                            style = MaterialTheme.typography.titleSmall,
                        )
                        if (sesion.estado.isNotBlank()) {
                            Text(
                                "Estado: ${sesion.estado}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        Spacer(Modifier.height(4.dp))
                        Text("Continuar →", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun IdiomaSelector(idioma: String, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column {
        OutlinedButton(onClick = { expanded = true }, modifier = Modifier.fillMaxWidth()) {
            Text("Idioma objetivo: ${idiomas[idioma] ?: idioma}")
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            idiomas.forEach { (code, name) ->
                DropdownMenuItem(text = { Text(name) }, onClick = {
                    onChange(code)
                    expanded = false
                })
            }
        }
    }
}

@Composable
private fun LoadingScreen() {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CircularProgressIndicator()
        Spacer(Modifier.height(16.dp))
        Text("Generando contenido…")
    }
}

@Composable
private fun DiagnosticoScreen(
    tema: String,
    preguntas: List<DiagnosticoPregunta>,
    onTerminar: (List<String>) -> Unit,
) {
    var indice by remember { mutableStateOf(0) }
    var seleccion by remember { mutableStateOf("") }
    val respuestas = remember { mutableListOf<String>() }

    val pregunta = preguntas.getOrNull(indice)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Text("Tema detectado: $tema", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))
        Text("Pregunta ${indice + 1} de ${preguntas.size}")
        Spacer(Modifier.height(16.dp))
        if (pregunta == null) {
            Text("No se pudo generar el diagnóstico.")
        } else {
            Text(pregunta.pregunta, style = MaterialTheme.typography.bodyLarge)
            Spacer(Modifier.height(8.dp))
            pregunta.opciones.forEach { opcion ->
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    RadioButton(
                        selected = seleccion == opcion,
                        onClick = { seleccion = opcion },
                    )
                    Text(opcion)
                }
            }
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = {
                    respuestas.add(seleccion)
                    seleccion = ""
                    if (indice + 1 < preguntas.size) {
                        indice += 1
                    } else {
                        onTerminar(respuestas.toList())
                    }
                },
                enabled = seleccion.isNotEmpty(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (indice + 1 < preguntas.size) "Siguiente" else "Generar plan")
            }
        }
    }
}

@Composable
private fun PlanScreen(niveles: List<PlanNivel>, onIniciarNivel: (Int) -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Text("Tu plan de aprendizaje", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))
        niveles.forEachIndexed { indice, nivel ->
            Card(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("Nivel ${nivel.numero}", style = MaterialTheme.typography.titleMedium)
                    Text(nivel.objetivo)
                    if (nivel.tipo_actividad.isNotBlank()) {
                        Text(nivel.tipo_actividad, style = MaterialTheme.typography.bodySmall)
                    }
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { onIniciarNivel(indice) }, modifier = Modifier.fillMaxWidth()) {
                        Text("Empezar nivel")
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun LeccionScreen(
    niveles: List<PlanNivel>,
    indice: Int,
    leccion: LeccionModel,
    onEvaluacion: () -> Unit,
    onBuscarPalabra: suspend (String) -> DiccionarioResponse,
) {
    val scope = rememberCoroutineScope()
    var palabraSel by remember { mutableStateOf<String?>(null) }
    var definicion by remember { mutableStateOf<DiccionarioResponse?>(null) }
    var buscando by remember { mutableStateOf(false) }
    var errorDic by remember { mutableStateOf<String?>(null) }

    fun buscar(palabra: String) {
        val limpia = palabra.trim('.', ',', ';', ':', '!', '?', '"', '\'', '(', ')')
        if (limpia.isBlank()) return
        palabraSel = limpia
        definicion = null
        errorDic = null
        buscando = true
        scope.launch {
            try {
                definicion = onBuscarPalabra(limpia)
            } catch (e: Exception) {
                errorDic = mensajeError(e)
            } finally {
                buscando = false
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        BarraProgreso(niveles, indice)
        Spacer(Modifier.height(16.dp))
        Text(leccion.titulo, style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Toca una palabra para ver su traducción",
            style = MaterialTheme.typography.bodySmall,
        )
        Spacer(Modifier.height(4.dp))
        FlowRow {
            leccion.texto.split(" ").forEach { palabra ->
                Text(
                    text = "$palabra ",
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.clickable { buscar(palabra) },
                )
            }
        }
        if (leccion.vocabulario.isNotEmpty()) {
            Spacer(Modifier.height(16.dp))
            Text("Vocabulario clave", style = MaterialTheme.typography.titleMedium)
            leccion.vocabulario.forEach { item ->
                Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Text(item.termino, style = MaterialTheme.typography.titleSmall)
                        Text(item.traduccion, style = MaterialTheme.typography.bodyMedium)
                        if (item.definicion.isNotBlank()) {
                            Text(item.definicion, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
        Spacer(Modifier.height(24.dp))
        Button(onClick = onEvaluacion, modifier = Modifier.fillMaxWidth()) {
            Text("Ir a la evaluación")
        }
    }
    if (palabraSel != null) {
        AlertDialog(
            onDismissRequest = { palabraSel = null },
            title = { Text(palabraSel ?: "") },
            text = {
                Column {
                    when {
                        buscando -> Text("Buscando traducción…")
                        errorDic != null -> Text(errorDic ?: "")
                        definicion != null -> {
                            Text(
                                definicion?.traduccion ?: "",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            if (definicion?.definicion?.isNotBlank() == true) {
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    definicion?.definicion ?: "",
                                    style = MaterialTheme.typography.bodyMedium,
                                )
                            }
                            if (definicion?.ejemplo?.isNotBlank() == true) {
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    definicion?.ejemplo ?: "",
                                    style = MaterialTheme.typography.bodySmall,
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { palabraSel = null }) { Text("Cerrar") }
            },
        )
    }
}

@Composable
private fun EvaluacionScreen(
    niveles: List<PlanNivel>,
    indice: Int,
    evaluacion: EvaluacionResponse,
    onResponder: (String) -> Unit,
) {
    var seleccion by remember { mutableStateOf("") }
    var respuestaTexto by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        BarraProgreso(niveles, indice)
        Spacer(Modifier.height(16.dp))
        Text("Evaluación del nivel", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))
        Text(evaluacion.pregunta, style = MaterialTheme.typography.bodyLarge)
        Spacer(Modifier.height(8.dp))
        val opciones = evaluacion.opciones
        if (opciones != null && opciones.isNotEmpty()) {
            opciones.forEach { opcion ->
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    RadioButton(
                        selected = seleccion == opcion,
                        onClick = { seleccion = opcion },
                    )
                    Text(opcion)
                }
            }
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = { onResponder(seleccion) },
                enabled = seleccion.isNotEmpty(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Responder")
            }
        } else {
            OutlinedTextField(
                value = respuestaTexto,
                onValueChange = { respuestaTexto = it },
                label = { Text("Escribe tu respuesta") },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = { onResponder(respuestaTexto) },
                enabled = respuestaTexto.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Responder")
            }
        }
    }
}

@Composable
private fun ResultadoScreen(
    niveles: List<PlanNivel>,
    indice: Int,
    resultado: EvaluacionResultado,
    onContinuar: () -> Unit,
) {
    val avanzar = resultado.decision in listOf("avanzar", "profundizar")
    val haySiguiente = indice + 1 < niveles.size

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        BarraProgreso(niveles, indice)
        Spacer(Modifier.height(16.dp))
        Text(
            text = if (resultado.correcta) "¡Correcto!" else "No es correcto",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(8.dp))
        Text(resultado.explicacion, style = MaterialTheme.typography.bodyLarge)
        Spacer(Modifier.height(16.dp))
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp)) {
                Text("Idioma: ${puntaje(resultado.ruta_idioma_score)} / 1.0")
                Text("Tema: ${puntaje(resultado.ruta_tema_score)} / 1.0")
                if (resultado.tipo_error.isNotBlank()) {
                    Text("Fallo detectado: ${resultado.tipo_error}")
                }
                Spacer(Modifier.height(8.dp))
                Text("Decisión del motor: ${decisionTexto(resultado.decision)}")
            }
        }
        Spacer(Modifier.height(24.dp))
        Button(onClick = onContinuar, modifier = Modifier.fillMaxWidth()) {
            Text(
                when {
                    !resultado.correcta -> "Repetir nivel"
                    haySiguiente -> "Siguiente nivel"
                    else -> "¡Completaste el plan!"
                }
            )
        }
    }
}

@Composable
private fun BarraProgreso(niveles: List<PlanNivel>, indice: Int) {
    val progreso = if (niveles.isEmpty()) 0f else (indice + 1).toFloat() / niveles.size.toFloat()
    Column(Modifier.fillMaxWidth()) {
        LinearProgressIndicator(progress = { progreso }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(4.dp))
        Text("Nivel ${indice + 1} de ${niveles.size}", style = MaterialTheme.typography.bodySmall)
    }
}

private fun mensajeError(e: Exception): String {
    val m = e.message ?: ""
    return when {
        "500" in m -> "El servidor no pudo generar el contenido. Reintenta en un momento."
        "404" in m -> "La sesión ya no existe en el servidor."
        "Timeout" in m || "timeout" in m -> "Tardó demasiado en responder. Revisa tu conexión y reintenta."
        m.startsWith("Expected response body") -> "Respuesta inesperada del servidor. Reintenta."
        m.isBlank() -> "Error de conexión"
        else -> m
    }
}

private fun puntaje(v: Double): String = String.format("%.2f", v)

private fun decisionTexto(d: String): String = when (d) {
    "avanzar" -> "Avanzar al siguiente nivel"
    "profundizar" -> "Profundizar el tema"
    "repetir" -> "Repetir el nivel"
    "simplificar" -> "Simplificar la dificultad"
    else -> d
}

@Composable
private fun ErrorScreen(message: String, onReintentar: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Algo salió mal", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text(message)
        Spacer(Modifier.height(16.dp))
        Button(onClick = onReintentar) { Text("Volver al inicio") }
    }
}
