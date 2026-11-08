# Instrucciones de uso

## Android Free

1. Abre Transcriptor Studio Free y acepta el aviso de uso responsable.
2. Escribe o pega texto, o pulsa **Grabar** para crear una muestra que podrás conservar.
3. Corrige el editor manualmente o agrega reglas de búsqueda y reemplazo.
4. Guarda hasta tres proyectos en la biblioteca. Cada proyecto conserva hasta diez versiones.
5. En **Voz**, elige una voz instalada en Android, ajusta velocidad, tono y pausas, y genera el WAV.
6. Exporta el texto, audio o respaldo desde el selector de documentos de Android.

Free funciona localmente y no solicita permiso de Internet. La calidad de voz depende del motor TTS instalado en el teléfono.

## Android Premium

### Primer inicio

1. Abre **Ajustes**.
2. Elige un modo de procesamiento:
   - **Automático**: intenta primero el servidor propio y usa la API personal como respaldo si existe.
   - **API personal**: usa directamente el proveedor seleccionado.
   - **Solo servidor propio**: nunca envía la tarea a una API externa.
3. Para servidor propio, introduce su dirección HTTPS y token y pulsa **Probar conexión**.
4. Para API personal, selecciona OpenAI, Google Gemini o Groq, pega tu clave y activa el consentimiento conectado. Guardarla cifrada es opcional.

### Transcribir

1. Pulsa **Elegir audio o video**, graba desde la app o pega una URL HTTPS directa al archivo.
2. Pulsa **Transcribir**.
3. Revisa el resultado. El original queda separado del editor.
4. Si el archivo no contiene voz o el servicio falla, el texto que ya estaba abierto se conserva.

Los enlaces a páginas de YouTube o Facebook no son archivos directos; descarga primero un archivo compatible.

### Corregir, traducir y reescribir

1. Corrige a mano o aplica reglas de reemplazo.
2. En **Transformar**, elige reescritura o traducción.
3. Revisa la comparación antes/después y los avisos sobre nombres, cifras o fechas.
4. Aplica o descarta la propuesta. Puedes recuperar el original o una versión anterior.

### Resumen y preguntas

En **Herramientas**, genera un resumen o formula una pregunta sobre la transcripción. Revisa siempre el resultado: una respuesta sin advertencias no garantiza exactitud.

### Narración

- **Android**: usa las voces instaladas en el dispositivo.
- **OpenAI**: requiere clave propia y permite instrucciones de estilo.
- **Qwen**: requiere servidor propio. El diseño crea una voz por descripción; la clonación requiere una muestra autorizada de 3 a 30 segundos.

### Respaldo y borrado

- Exporta `proyecto-transcriptor.json` para conservar texto, original, reglas e historial.
- Las claves y tokens no se incluyen en el respaldo.
- **Borrar todos mis datos de la app** elimina proyectos, reglas, historial, grabaciones internas, audio generado y credenciales recordadas. No borra los archivos originales ubicados fuera de la app.

## Aplicación Windows

1. Extrae por completo el paquete de Windows.
2. Ejecuta `Transcriptor.exe` desde la carpeta extraída.
3. Selecciona un archivo o enlace compatible.
4. Elige el modelo Whisper según precisión y recursos disponibles.
5. Transcribe, revisa, resume o traduce.
6. Usa búsqueda y reemplazo para correcciones repetidas y exporta el resultado.

La primera ejecución de una función local puede descargar modelos. Los modelos se conservan bajo `%LOCALAPPDATA%\Transcriptor\models`.

## Formatos y límites actuales

- Android: MP3, MP4, M4A, WAV, WEBM y MPEG; hasta 24 MB por importación.
- Voz Android/OpenAI: hasta 60 000 caracteres por narración.
- Qwen3-TTS: hasta 12 000 caracteres por tarea.
- Traducción y reescritura Android: hasta 24 000 caracteres por tarea.
- Mantén la app abierta durante el procesamiento.
