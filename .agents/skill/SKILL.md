# Arquitectura de Directorios

Esta skill documenta la arquitectura estándar de un directorio `.agents/` para proyectos que usan IA como copiloto. Cubre: estructura de archivos, CodeGraph, skills, memoria del agente y mapeo del proyecto.

---

## Estructura de Directorios

```
proyecto/
├── .agents/                    # ← Directorio raíz de la arquitectura
│   ├── skill/                  # Skills reutilizables (capacidades del agente)
│   │   └── ...
│   ├── tasks.md                # Tareas activas del agente
│   ├── input.md                # Input pendiente del desarrollador
│   ├── rules/                  # Reglas persistentes
│   │   └── ...
│   ├── roles/                  # Definiciones de rol
│   │   └── ...
│   ├── meetings/               # Decisiones de reuniones
│   │   └── decisions/
│   └── history/                # Historial completado
├── .codegraph/                 # Índice de código para búsqueda semántica
│   ├── codegraph.db            # Base de datos SQLite del índice
│   ├── ...
│   └── daemon.pid              # PID del daemon de indexación
├── .opencode/                  # Configuración de OpenCode (si se usa)
│   ├── opencode.jsonc          # Configuración principal
│   └── ...
├── AGENTS.md                   # Archivo de referencia central del agente
└── CLAUDE.md                   # Instrucciones para Claude