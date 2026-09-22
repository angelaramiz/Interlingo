package com.interlingo.app.llm

class LlmEngine private constructor() {
    companion object {
        private val instance = LlmEngine()

        init {
            System.loadLibrary("llm_bridge")
        }

        fun load(modelPath: String, nCtx: Int = 2048): Boolean {
            return instance.nativeLoadModel(modelPath, nCtx) != 0L
        }

        fun complete(prompt: String, maxTokens: Int = 1536): String {
            return instance.nativeComplete(0L, prompt, maxTokens)
        }

        fun stop() {
            instance.nativeStop(0L)
        }

        fun free() {
            instance.nativeFreeModel(0L)
        }
    }

    private external fun nativeLoadModel(path: String, nCtx: Int): Long
    private external fun nativeComplete(ptr: Long, prompt: String, maxTokens: Int): String
    private external fun nativeStop(ptr: Long)
    private external fun nativeFreeModel(ptr: Long)
}
