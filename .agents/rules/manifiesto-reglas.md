# Reglas del Proyecto — Interlingo

## Lenguaje y contenido
- El contenido educativo (textos, preguntas, feedback) siempre en el **idioma objetivo** de la lección.
- La comunicación con el desarrollador puede hacerse en español.

## Contenido generado por IA
- La IA responde siempre en **JSON estructurado** (nunca texto libre sin formato).
- Variables controladas por nivel: longitud de oraciones, vocabulario nuevo, conectores permitidos, tipo de pregunta, % de palabras conocidas.

## Calidad y adaptación
- Feedback inmediato con explicación breve (por qué es correcto/incorrecto).
- Toda decisión de nivel (avanzar / repetir / simplificar / profundizar) queda registrada en la traza.
- Diagnosticar el fallo: si es por idioma → apoyo lingüístico; si es por concepto → explicación más simple.

## Seguridad
- No exponer claves de API en el código ni en el repositorio.
