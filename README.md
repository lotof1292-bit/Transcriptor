# Transcriptor

Aplicación de escritorio independiente para transcribir archivos de audio/video y enlaces públicos compatibles con yt-dlp. El reconocimiento se ejecuta localmente con Whisper; no requiere una API key. La primera ejecución descarga el modelo Whisper elegido.

También incluye un modelo de lenguaje local Qwen 3 para resúmenes enfocados y traducción. No requiere API key ni envía el texto a un servicio externo. La primera vez que se usa descarga el modelo cuantizado (aproximadamente 500 MB) y lo guarda en `%LOCALAPPDATA%\Transcriptor\models`; los usos siguientes funcionan sin conexión. Para resumir se puede priorizar ideas principales, acuerdos y tareas, cifras y fechas, argumentos o un enfoque propio. La traducción admite idiomas comunes y uno personalizado.

La función **Quitar o cambiar palabra** edita todas las apariciones de una palabra completa en la transcripción, resumen y traducción; dejar vacío el reemplazo elimina las apariciones. No usa IA.

## Iniciar en Windows

```powershell
cd Transcriptor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Acepta archivos MP3, WAV, M4A, AAC, FLAC, OGG, MP4, MKV, MOV y WEBM. Para enlaces, el acceso depende de las reglas del sitio; plataformas que exijan inicio de sesión, bloqueen descargas o cambien su sistema pueden no funcionar. El primer uso descarga el modelo Whisper seleccionado y el procesamiento depende de la memoria y velocidad del equipo.
