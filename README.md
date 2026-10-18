# Transcriptor

Aplicación de escritorio para convertir audio, video y enlaces compatibles en texto, generar resúmenes y traducir resultados sin depender de servicios de IA en la nube.

## Características

- Transcripción local con Whisper mediante `faster-whisper`.
- Compatibilidad con MP3, WAV, M4A, AAC, FLAC, OGG, MP4, MKV, MOV y WEBM.
- Procesamiento de enlaces públicos compatibles con `yt-dlp`.
- Resúmenes orientados a ideas principales, acuerdos y tareas, cifras, fechas o argumentos.
- Traducción local con un modelo Qwen 3 cuantizado.
- Búsqueda, sustitución o eliminación de palabras completas en los resultados.
- Comprobación y descarga de actualizaciones desde GitHub Releases.

Los modelos y el texto procesado permanecen en el equipo. No se necesita una API key para transcribir, resumir o traducir.

## Instalación para desarrollo

Requisitos: Windows, Python 3.10 o posterior y FFmpeg disponible en el sistema.

```powershell
git clone https://github.com/lotof1292-bit/Transcriptor.git
cd Transcriptor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Modelos locales

La primera transcripción descarga el modelo Whisper seleccionado. Las funciones de resumen y traducción descargan una vez el modelo `Qwen3-0.6B-Q4_K_M.gguf` y lo guardan en `%LOCALAPPDATA%\Transcriptor\models`. Los usos posteriores pueden funcionar sin conexión.

## Distribución para Windows

Las versiones publicadas se entregan como un paquete ZIP autocontenido. Extrae todo el contenido en una carpeta y ejecuta `Transcriptor.exe`; el ejecutable necesita los archivos incluidos junto a él.

Consulta las versiones disponibles en [GitHub Releases](https://github.com/lotof1292-bit/Transcriptor/releases).

## Consideraciones

- El tiempo de procesamiento depende del modelo elegido, la duración del contenido y el hardware disponible.
- Los enlaces dependen de las reglas y cambios de cada plataforma; el contenido con autenticación o restricciones puede no estar disponible.
- Las carpetas de transcripciones, modelos y archivos temporales se mantienen fuera del repositorio para proteger datos personales y evitar binarios de gran tamaño.

## Estado

Versión de aplicación: `1.1.3`. Proyecto activo para Windows.
