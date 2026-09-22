package com.interlingo.app.update

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

@Serializable
data class AppVersionInfo(
    val versionCode: Int = 1,
    val versionName: String = "0.1.0",
    val apkUrl: String = "/static/interlingo.apk",
)

object UpdateManager {

    private val json = Json { ignoreUnknownKeys = true }

    fun getLocalVersionCode(context: Context): Int {
        return try {
            val info = context.packageManager.getPackageInfo(context.packageName, 0)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                info.longVersionCode.toInt()
            } else {
                @Suppress("DEPRECATION") info.versionCode
            }
        } catch (e: Exception) {
            1
        }
    }

    suspend fun checkForUpdate(serverUrl: String): AppVersionInfo? =
        withContext(Dispatchers.IO) {
            val conn = URL("$serverUrl/api/app-version").openConnection() as HttpURLConnection
            conn.connectTimeout = 10000
            conn.readTimeout = 10000
            conn.connect()
            if (conn.responseCode != HttpURLConnection.HTTP_OK) return@withContext null
            val body = conn.inputStream.bufferedReader().use { it.readText() }
            json.decodeFromString<AppVersionInfo>(body)
        }

    fun resolveApkUrl(serverUrl: String, apkUrl: String): String {
        val full = if (apkUrl.startsWith("/")) {
            serverUrl.trimEnd('/') + apkUrl
        } else {
            apkUrl
        }
        return "$full?t=${System.currentTimeMillis()}"
    }

    suspend fun downloadApk(
        context: Context,
        apkUrl: String,
        fileName: String = "interlingo.apk",
        onProgress: (downloadedBytes: Long, totalBytes: Long) -> Unit,
    ): File = withContext(Dispatchers.IO) {
        val conn = URL(apkUrl).openConnection() as HttpURLConnection
        conn.connectTimeout = 15000
        conn.readTimeout = 60000
        conn.connect()
        if (conn.responseCode != HttpURLConnection.HTTP_OK) {
            throw IllegalStateException("Descarga falló: HTTP ${conn.responseCode}")
        }
        val total = conn.contentLengthLong
        val dir = context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?: throw IllegalStateException("Sin acceso a descargas")
        dir.listFiles()?.forEach { if (it.name.endsWith(".apk")) it.delete() }
        val part = File(dir, "$fileName.part")
        onProgress(0L, total)
        conn.inputStream.use { input ->
            part.outputStream().use { output ->
                val buf = ByteArray(64 * 1024)
                var read: Int
                var done = 0L
                while (input.read(buf).also { read = it } != -1) {
                    output.write(buf, 0, read)
                    done += read
                    onProgress(done, total)
                }
            }
        }
        val out = File(dir, fileName)
        part.renameTo(out)
        out
    }

    fun installApk(context: Context, apk: File) {
        val uri: Uri = FileProvider.getUriForFile(
            context, "${context.packageName}.fileprovider", apk
        )
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
    }
}
