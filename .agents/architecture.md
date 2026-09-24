# Interlingo — Arquitectura del Proyecto

## Concepto
Plataforma de **aprendizaje de idiomas basado en temas de interés**. El usuario no estudia el idioma con frases genéricas; aprende el idioma leyendo, respondiendo y creando contenido sobre temas que le interesan (ej: ETL, SaaS, finanzas, cocina).

## Principio central
El **tema es el vehículo**, el **idioma es la habilidad principal** que se entrena.

## Dos rutas de progreso simultáneas
- **Ruta de idioma**: vocabulario, longitud de frases, gramática, comprensión lectora, producción escrita, capacidad de explicar conceptos en el idioma objetivo.
- **Ruta de tema**: conceptos del dominio, complejidad técnica, casos prácticos, artefactos reales, resolución de problemas.

## Motor adaptativo
Evalúa ambas rutas y decide:
- Entiende el concepto técnico pero falla el idioma → baja la dificultad lingüística.
- Domina el idioma pero no el tema → simplifica la explicación técnica.

## Variables de contenido controladas por la IA
Nivel de idioma, % de vocabulario conocido, longitud de oraciones, conectores permitidos, cantidad de palabras nuevas, tipo de pregunta.

## Secuencia de actividades
1. Comprensión lectora
2. Producción guiada
3. Respuestas escritas
4. Explicación propia del tema en el idioma objetivo

## MVP (versión mínima)
Ciclo: **meta → diagnóstico → lección → evaluación → ajuste**
1. Usuario indica tema, idioma y objetivo.
2. IA genera plan adaptativo con 5 niveles.
3. Cada nivel: texto breve en el idioma objetivo, vocabulario clave, preguntas de comprensión, evaluación.
4. Sistema guarda resultados y ajusta el siguiente nivel.

Métrica principal: cuánto entiende y expresa el usuario en el idioma mientras estudia el tema.

## Stack técnico (MVP)
- **Frontend móvil**: Kotlin Multiplatform + Compose Multiplatform. Fase 1 solo Android; iOS se añade después (módulo compartido). Componentes: texto, opción múltiple, campo de escritura, tarjetas de traducción, barra de progreso.
- **Backend**: FastAPI. Recibe la meta, llama a OrcaRouter, aplica reglas de nivel, devuelve contenido estructurado en JSON.
- **Base de datos**: SQLite (MVP) → PostgreSQL (crecimiento). Guarda: usuario, meta, tema, nivel actual, conceptos dominados/débiles, evaluaciones, errores repetidos, contenido generado.
- **Motor de prompts**: plantillas separadas para interpretar meta, diagnóstico, plan, lección, evaluación, corrección, ajuste de nivel.
- **Salida estructurada**: JSON con campos como título, explicación, pregunta, opciones, respuesta correcta, nivel, palabras clave, criterio de éxito.
- **Evaluación automática**: opción múltiple y ordenar palabras con lógica simple; respuestas escritas con rúbrica (comprensión, vocabulario, claridad, uso técnico).
- **Memoria de adaptación**: registra qué falló y por qué (idioma vs concepto) para generar el apoyo adecuado.

## Motor de IA (configurable)
- `AI_PROVIDER=local` (por defecto): **Qwen3-4B-Instruct** con `llama-cpp-python` (CPU). Modelo en `D:\models\Qwen3-4B-Instruct-2507-Q4_K_M.gguf`.
- `AI_PROVIDER=orcarouter`: OrcaRouter con `ORCA_MODEL`.
- Dispatcher en `app/ai/inference.py`; el resto del backend no cambia.

## Inferencia on-device (app)
- llama.cpp compilado NDK (arm64-v8a) + puente JNI propio (`LlmEngine`).
- La app descarga el GGUF a `filesDir/models` en primer arranque (solo una vez).
- `LocalEngine` implementa el mismo `LearningApi` que `ApiClient` (backend se conserva como opción).
- El modelo Qwen3-4B cabe porque el dispositivo objetivo tiene 16 GB RAM (Snapdragon 8 Gen 3).

## Integraciones opcionales
Texto a voz, traducción al hacer clic, repetición espaciada, exportación de artefactos.

## UX/UI
Pantalla de inicio simple (campo de meta + botón comenzar), onboarding corto (2-3 preguntas si la meta es ambigua), vista de lección limpia (un foco por pantalla), interacción por nivel, feedback inmediato, diccionario integrado (clic = traducción sin salir), progreso visible simple, control de dificultad manual (fácil/adecuado/difícil), accesibilidad (contraste, tamaño de fuente, teclado, audio).

## Próximos pasos
1. Decidir stack definitivo (pendiente)
2. Esquema de base de datos (modelo de datos)
3. Plantillas del motor de prompts
4. Prototipo UI del ciclo MVP
