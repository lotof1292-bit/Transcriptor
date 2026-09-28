# Transcriptor

Aplicación de escritorio independiente para transcribir archivos de audio/video y enlaces públicos compatibles con yt-dlp. El reconocimiento se ejecuta localmente con Whisper; no requiere una API key. La primera ejecución descarga el modelo elegido.

También incluye resúmenes enfocados y traducción mediante un proveedor de IA compatible con chat (OpenAI, Groq, OpenRouter o endpoint compatible). La clave se almacena con el almacén seguro de credenciales de Windows. El usuario puede pedir, por ejemplo, que el resumen destaque ideas principales, acuerdos y tareas, cifras y fechas, argumentos o un enfoque propio. La traducción admite idiomas comunes y un idioma personalizado. Esas dos funciones envían el texto transcrito al proveedor configurado.

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
