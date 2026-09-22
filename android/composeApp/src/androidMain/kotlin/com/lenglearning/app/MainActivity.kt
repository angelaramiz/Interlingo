package com.lenglearning.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.lenglearning.app.data.LearningApi
import com.lenglearning.app.llm.LlmEngine
import com.lenglearning.app.llm.LocalEngine
import com.lenglearning.app.llm.ModelDownloader
import java.io.File

class MainActivity : ComponentActivity() {

    companion object {
        const val MODEL_URL =
            "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/" +
            "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
        const val MODEL_FILE = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val modelsDir = File(filesDir, "models")
        setContent {
            MaterialTheme {
                var engine by remember { mutableStateOf<LearningApi?>(null) }
                var progress by remember { mutableStateOf<Pair<Long, Long>?>(null) }
                var error by remember { mutableStateOf<String?>(null) }

                LaunchedEffect(Unit) {
                    try {
                        val downloader = ModelDownloader(modelsDir)
                        val modelFile = downloader.ensureModel(MODEL_URL, MODEL_FILE) { done, total ->
                            progress = done to total
                        }
                        val ok = LlmEngine.load(modelFile.absolutePath)
                        engine = if (ok) LocalEngine() else null
                        if (!ok) error = "No se pudo cargar el modelo en memoria"
                    } catch (e: Exception) {
                        error = e.message ?: "Error de descarga del modelo"
                    }
                }

                Surface(modifier = Modifier.fillMaxSize()) {
                    when {
                        error != null -> ModelErrorScreen(error!!) { recreate() }
                        engine != null -> App(engine!!)
                        else -> ModelDownloadScreen(progress)
                    }
                }
            }
        }
    }
}

@Composable
private fun ModelDownloadScreen(progress: Pair<Long, Long>?) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("LengLearning", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(16.dp))
        Text("Descargando el modelo de IA (solo la primera vez)…")
        Spacer(Modifier.height(16.dp))
        if (progress != null) {
            val (done, total) = progress
            val frac = if (total > 0) (done.toFloat() / total.toFloat()).coerceIn(0f, 1f) else 0f
            LinearProgressIndicator(progress = { frac }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(8.dp))
            Text("${done / 1024 / 1024} MB / ${total / 1024 / 1024} MB")
        } else {
            Text("Preparando…")
        }
    }
}

@Composable
private fun ModelErrorScreen(message: String, onRetry: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("No se pudo iniciar el modelo", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text(message)
        Spacer(Modifier.height(16.dp))
        Button(onClick = onRetry) { Text("Reintentar") }
    }
}
