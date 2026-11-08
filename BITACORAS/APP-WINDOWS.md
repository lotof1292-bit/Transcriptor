# Bitácora · Aplicación Windows

## 2026-11-08 · pre-release Windows publicada

- Cambio: se publicó `v1.1.3-windows-preview` con `Transcriptor-Windows.zip`.
- Motivo: conservar el artefacto histórico sin confundirlo con la versión Windows validada anteriormente.
- Archivos: ZIP con 426 entradas y SHA-256 `8EFC76D3B9CAEDA77D0A670DBB8F34C9A65A14016A2773728E1EA269D42A3FFF`.
- Validación: todas las entradas del ZIP se leyeron completamente sin error; la Release está marcada como previa y advierte que falta una prueba limpia de extremo a extremo.
- Faltantes: ejecutar y validar transcripción, resumen y traducción empaquetados en una PC limpia.

## 2026-11-08 · traslado a carpeta propia

- Cambio: la aplicación Windows y su historial se movieron junto con todo Transcriptor a `PROYECTOS_IA_Y_DESARROLLO\Transcriptor`.
- Motivo: separar el producto de la carpeta histórica `ChatGPT\New project`.
- Archivos: proyecto completo, incluido `.git`, fuente, entorno y artefactos.
- Validación: movimiento atómico en el mismo volumen; Git reconoce la nueva raíz y `python -m py_compile main.py` pasa desde ella.
- Faltantes: validar nuevamente el empaquetado completo y el ejecutable Windows desde la ruta definitiva.

## 2026-11-08 · inventario de versión 1.1.3

- Cambio: se creó la bitácora permanente y se documentó el estado real de la aplicación Windows.
- Motivo: separar su evolución de Android Free/Premium y evitar que un ejecutable antiguo se confunda con una versión validada.
- Archivos: `main.py`, `requirements.txt`, `Transcriptor.spec`, `Transcriptor-Debug.spec`, `.github/workflows/release.yml`.
- Validación: se revisaron fuente, README, artefactos existentes y antecedentes de compilación.
- Faltantes: reconstruir el paquete actual, probarlo en una PC limpia y validar transcripción/resumen/traducción local de extremo a extremo. La última compilación final conocida fue bloqueada por falta de espacio y una contaminación de DLL ICU/Qt.

## Historial recuperado

- 1.1.3 añadió selección Whisper `tiny/base/small`, límites de hilos y workers, resumen guiado y reemplazo global.
- El flujo de GitHub Releases publica `Transcriptor-Windows.zip` para etiquetas `v*`.
- Los modelos locales viven fuera del repositorio en `%LOCALAPPDATA%\Transcriptor\models`.
