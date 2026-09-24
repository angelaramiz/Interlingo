package com.interlingo.app

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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.interlingo.app.data.ApiClient
import com.interlingo.app.data.LearningApi
import com.interlingo.app.llm.LlmEngine
import com.interlingo.app.llm.LocalEngine
import com.interlingo.app.llm.ModelDownloader
import com.interlingo.app.update.AppVersionInfo
import com.interlingo.app.update.UpdateManager
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {

    companion object {
        const val MODEL_URL =
            "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/" +
            "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
        const val MODEL_FILE = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    }

    private suspend fun isServerReachable(serverUrl: String): Boolean =
        withContext(Dispatchers.IO) {
            try {
                val conn = URL("$serverUrl/api/health").openConnection() as HttpURLConnection
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                conn.connect()
                conn.responseCode == HttpURLConnection.HTTP_OK
            } catch (e: Exception) {
                false
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val modelsDir = File(filesDir, "models")
        val serverUrl = BuildConfig.SERVER_URL
        setContent {
            MaterialTheme {
                var engine by remember { mutableStateOf<LearningApi?>(null) }
                var engineLabel by remember { mutableStateOf<String?>(null) }
                var progress by remember { mutableStateOf<Pair<Long, Long>?>(null) }
                var error by remember { mutableStateOf<String?>(null) }
                var updateInfo by remember { mutableStateOf<AppVersionInfo?>(null) }
                var updateStatus by remember { mutableStateOf<String?>(null) }
                var checkingUpdate by remember { mutableStateOf(false) }
                var downloadingUpdate by remember { mutableStateOf<Pair<Long, Long>?>(null) }
                val scope = rememberCoroutineScope()

                fun doCheckUpdate(manual: Boolean) {
                    if (checkingUpdate) return
                    checkingUpdate = true
                    if (manual) updateStatus = "Despertando servidor…"
                    scope.launch {
                        try {
                            val awake = UpdateManager.wakeUp(serverUrl) { attempt ->
                                if (manual) updateStatus = "Despertando servidor… (intento $attempt)"
                            }
                            if (!awake) {
                                if (manual) updateStatus = "No se pudo contactar al servidor"
                                return@launch
                            }
                            val latest = UpdateManager.checkForUpdate(serverUrl)
                            val local = UpdateManager.getLocalVersionCode(this@MainActivity)
                            if (latest != null && latest.versionCode > local) {
                                updateInfo = latest
                                updateStatus = null
                            } else if (manual) {
                                updateStatus = "Ya estás al día"
                            }
                        } catch (e: Exception) {
                            if (manual) updateStatus = "Sin conexión al servidor"
                        } finally {
                            checkingUpdate = false
                        }
                    }
                }

                LaunchedEffect(Unit) {
                    // Backend-first: si hay servidor, las sesiones se guardan y
                    // procesan en el backend (SQLite). Sin servidor, on-device.
                    if (isServerReachable(serverUrl)) {
                        engine = ApiClient(serverUrl)
                        engineLabel = "En línea · sesiones guardadas en el servidor"
                    } else {
                        try {
                            val downloader = ModelDownloader(modelsDir)
                            val modelFile = downloader.ensureModel(MODEL_URL, MODEL_FILE) { done, total ->
                                progress = done to total
                            }
                            val ok = LlmEngine.load(modelFile.absolutePath)
                            engine = if (ok) LocalEngine() else null
                            if (!ok) error = "No se pudo cargar el modelo en memoria"
                            else engineLabel = "Sin conexión · modo en dispositivo"
                        } catch (e: Exception) {
                            error = e.message ?: "Error de descarga del modelo"
                        }
                    }
                }

                LaunchedEffect(engine) {
                    if (engine != null) doCheckUpdate(manual = false)
                }

                Surface(modifier = Modifier.fillMaxSize()) {
                    when {
                        error != null -> ModelErrorScreen(error!!) { recreate() }
                        engine != null -> App(
                            api = engine!!,
                            onManualUpdate = { doCheckUpdate(manual = true) },
                            updateStatus = updateStatus,
                            engineLabel = engineLabel,
                        )
                        else -> ModelDownloadScreen(progress)
                    }
                }

                val info = updateInfo
                if (info != null) {
                    AlertDialog(
                        onDismissRequest = { updateInfo = null },
                        title = { Text("Nueva versión disponible") },
                        text = {
                            Column {
                                Text("Interlingo ${info.versionName} está lista para instalar.")
                                val dl = downloadingUpdate
                                if (dl != null) {
                                    Spacer(Modifier.height(12.dp))
                                    val (done, total) = dl
                                    val frac = if (total > 0) {
                                        (done.toFloat() / total.toFloat()).coerceIn(0f, 1f)
                                    } else {
                                        0f
                                    }
                                    LinearProgressIndicator(
                                        progress = { frac },
                                        modifier = Modifier.fillMaxWidth(),
                                    )
                                    Spacer(Modifier.height(4.dp))
                                    Text("${done / 1024 / 1024} MB / ${total / 1024 / 1024} MB")
                                }
                            }
                        },
                        confirmButton = {
                            Button(
                                onClick = {
                                    if (downloadingUpdate != null) return@Button
                                    scope.launch {
                                        try {
                                            val apkUrl = UpdateManager.resolveApkUrl(
                                                serverUrl, info.apkUrl
                                            )
                                            val apk = UpdateManager.downloadApk(
                                                this@MainActivity, apkUrl
                                            ) { done, total ->
                                                downloadingUpdate = done to total
                                            }
                                            downloadingUpdate = null
                                            updateInfo = null
                                            UpdateManager.installApk(this@MainActivity, apk)
                                        } catch (e: Exception) {
                                            downloadingUpdate = null
                                            updateStatus = "Error al descargar: ${e.message}"
                                            updateInfo = null
                                        }
                                    }
                                }
                            ) { Text("Descargar e instalar") }
                        },
                        dismissButton = {
                            TextButton(onClick = { updateInfo = null }) { Text("Después") }
                        },
                    )
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
        Text("Interlingo", style = MaterialTheme.typography.headlineLarge)
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
