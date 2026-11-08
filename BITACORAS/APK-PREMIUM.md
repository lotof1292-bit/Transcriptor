# Bitácora · APK Premium

## 2026-11-08 · traslado a carpeta propia

- Cambio: fuente, servidor, pruebas y APK Premium quedaron bajo la ubicación oficial del proyecto.
- Motivo: separar Transcriptor de la carpeta histórica de ChatGPT.
- Archivos: `android-studio-v1.3`, servidor y documentación central.
- Validación: presencia del APK, servidor y fuente confirmada tras el movimiento.
- Faltantes: reinstalación física pendiente por el fallo de arranque de BlueStacks.

## 2026-11-08 · Premium 1.4

- Cambio: se creó la bitácora permanente y se consolidó el estado de procesamiento conectado.
- Motivo: registrar por separado las funciones que dependen de servidor, proveedor y futura licencia Premium.
- Archivos: `android-studio-v1.3/MainActivity.java`, interfaz, manifiesto Premium, servidor y pruebas.
- Validación: Premium se instaló en BlueStacks; se probaron transcripción Whisper real, reglas, historial, respaldo y borrado local. OpenAI/Gemini/Groq se validaron por protocolo y rutas simuladas, no con llamadas facturadas.
- Faltantes: pruebas reales de los tres proveedores, Qwen/Ollama, TTS en teléfono, VPS, cuentas/licencia/facturación y firma de producción.

## Capacidades vigentes

- Modo Automático: servidor propio primero y API personal opcional como respaldo.
- Modo API personal: OpenAI, Google Gemini o Groq mediante clave del usuario.
- Modo Solo servidor: no envía la tarea a API externa.
- Transcripción, reescritura, traducción, resumen, preguntas y separación de hablantes.
- Voz OpenAI y Qwen3-TTS en servidor propio.

## 2026-11-08 · recompilación de control

- Cambio: se recompilaron Free y Premium después de consolidar permisos y documentación.
- Motivo: asegurar que los artefactos correspondieran a la fuente actual.
- Archivos: `dist/Transcriptor-Studio-1.4-premium.apk`.
- Validación: pruebas completas aprobadas; `aapt` confirmó `INTERNET` y `RECORD_AUDIO`; SHA-256 `B1ACC3C3000E44249263359407FAA35A9CA6698B6C7CD8516AD093DB3100B27A`.
- Faltantes: reinstalación física pendiente porque BlueStacks mostró un error de inicio y se cerró.
