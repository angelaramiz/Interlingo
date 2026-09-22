package com.lenglearning.app.llm

import java.io.File
import java.net.HttpURLConnection
import java.net.URL

class ModelDownloader(private val modelsDir: File) {

    suspend fun ensureModel(
        url: String,
        fileName: String,
        onProgress: (downloadedBytes: Long, totalBytes: Long) -> Unit,
    ): File = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        modelsDir.mkdirs()
        val out = File(modelsDir, fileName)
        if (out.exists() && out.length() > 0) return@withContext out

        val part = File(modelsDir, "$fileName.part")
        val conn = URL(url).openConnection() as HttpURLConnection
        conn.connect()
        val total = conn.contentLengthLong
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
        part.renameTo(out)
        out
    }
}
