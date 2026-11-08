# Bitácora · APK y servidor compartido

## 2026-11-08 · preparación de publicación en GitHub

- Cambio: se amplió `.gitignore` y se preparó la publicación de Windows, Android Free/Premium, servidor, pruebas y documentación.
- Motivo: conservar todo el código reconstruible en GitHub sin publicar claves, firmas, entornos, modelos, dependencias instaladas ni binarios generados.
- Archivos: raíz del proyecto, `android-studio`, `android-studio-v1.3`, `BITACORAS` y documentación central.
- Validación: pendiente revisar el índice preparado, escanear secretos, crear commit y comprobar el push remoto.
- Faltantes: los APK/EXE/ZIP se distribuirán como artefactos o Releases, no dentro del historial Git.

## 2026-11-08 · traslado a carpeta propia

- Cambio: Android, servidor, pruebas y artefactos se movieron con el proyecto completo a `PROYECTOS_IA_Y_DESARROLLO\Transcriptor`.
- Motivo: establecer una ubicación oficial independiente de ChatGPT y Antigravity.
- Archivos: `android-studio`, `android-studio-v1.3`, ZIP, APK y documentación.
- Validación: movimiento atómico en el mismo volumen; Git reconoce la nueva raíz. Desde ella pasan ediciones, interfaz, importación/transcripción y contrato FastAPI; los hashes de Free/Premium no cambiaron.
- Faltantes: mantener actualizado el diario reversible `68e9722d7335` y completar las pruebas físicas pendientes.

## 2026-11-08 · Android 1.4

- Cambio: se creó la bitácora permanente; se consolidó el manifiesto, instrucciones y estado del producto.
- Motivo: mantener trazabilidad separada para cambios compartidos de Free/Premium y del servidor.
- Archivos: `android-studio-v1.3/assets/index.html`, `src/`, `server/`, `tests/`, manifiestos y scripts de compilación.
- Validación: pruebas de interfaz, importación, contrato FastAPI, 187 comprobaciones Java, compilación/firma e instalación previa en BlueStacks.
- Faltantes: teléfono real con TTS, Qwen/Ollama real, APIs facturadas reales y VPS Hostinger real.

## Cambios acumulados de 1.4

- Importación de audio/video, grabación y URL HTTPS directa.
- Texto editable, reglas, original, historial, biblioteca y respaldo JSON.
- Borrado local de proyectos, historial, reglas, audio interno y credenciales.
- Servidor FastAPI con Whisper, Ollama/Qwen y Qwen3-TTS.
- Preparación de despliegue Docker/Caddy y ruta mínima `/live`.
- Corrección de identificadores de proyecto para impedir sobrescrituras en guardados rápidos.
