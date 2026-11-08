# Transcriptor Studio 1.4 — Free y Premium

Aplicación Android basada en la fuente recuperada de la versión 1.3. Esta entrega genera dos paquetes instalables en paralelo: `mx.transcriptor.studio.free` y `mx.transcriptor.studio.premium`.
Android 8 o superior. No contiene claves API, modelos descargados ni saldo de servicios conectado.


## Ediciones

Free incluye grabación, edición, reglas, hasta 3 proyectos, 10 versiones por proyecto, voz Android y exportación local. Premium habilita proyectos y 30 versiones, transcripción, reescritura, traducción, resumen, preguntas, hablantes, claves propias de OpenAI/Google Gemini/Groq y el servidor propio. Las funciones Premium permanecen visibles en Free y explican por qué están bloqueadas.

Free no solicita permiso de Internet: micrófono, edición, reglas, proyectos y narración Android funcionan localmente. Premium sí declara Internet para el servidor propio y los proveedores elegidos por el usuario. Ninguna edición solicita acceso general al almacenamiento; importación y exportación usan el selector de documentos de Android.

La firma privada de la versión 1.3 no está disponible. Estas APK usan una firma de desarrollo y paquetes nuevos, por lo que no sustituyen la instalación anterior. Exporta un respaldo JSON para migrar texto, original, reglas e historial. Las claves y conexiones no se importan.

## Procesamiento con servidor propio o API personal

Premium ofrece tres modos: **Automático**, **API personal** y **Solo servidor propio**. Automático intenta el servidor cuando tiene dirección y token; si también existe una clave personal, la usa como respaldo cuando el servidor falla. No obliga a configurar una API externa para utilizar un servidor disponible. API personal permite elegir OpenAI, Google Gemini o Groq. Solo servidor propio nunca envía la tarea a una API externa. No incluyas claves del desarrollador dentro del APK.

OpenAI cubre texto, transcripción, separación de hablantes y voz expresiva. Groq cubre texto y transcripción. Gemini cubre reescritura, traducción, resumen y análisis; para transcribir con Gemini seleccionado se debe usar el servidor propio o cambiar temporalmente a OpenAI/Groq. La app conserva una sola clave de proveedor activa; al cambiar de proveedor pide guardar la clave correspondiente y nunca la incluye en el proyecto ni en el APK.

El servidor incluido usa faster-whisper para transcripción, Ollama con `qwen3:4b` para texto y Qwen3-TTS para voz. Las reglas, edición y voz Android siguen en el dispositivo.

Instala Ollama en la PC desde https://ollama.com/download e inicia su servicio. Ejecuta `ollama pull qwen3:4b`. El script Windows lo intenta si encuentra Ollama instalado. Después ejecuta `server/start-windows.ps1`, que prepara el entorno Python y el servicio. Desde Android configura dirección/token en Ajustes y usa Probar conexión. Esa comprobación verifica el servicio HTTP, no que la inferencia o los modelos ya estén listos.

La primera transcripción descarga el modelo Whisper; el primer uso de voz descarga Qwen. Para trabajar sin Internet, descarga previamente los tres motores/modelos en esa PC. Puedes definir `STUDIO_OFFLINE=1` para impedir descargas desde Hugging Face. Los enlaces a archivos externos naturalmente requieren conexión para descargarlos. El procesamiento no se hace dentro del APK; necesita conexión al servidor por red local o un acceso remoto configurado.

Configuración del servidor: `STUDIO_TEXT_MODEL` (por defecto `qwen3:4b`, previamente descargado en Ollama), `STUDIO_OLLAMA_URL` (por defecto `http://127.0.0.1:11434`), `STUDIO_ASR_MODEL` (`small`), `STUDIO_ASR_DEVICE` (`cpu`), `STUDIO_ASR_COMPUTE` (`int8` en CPU), además de las opciones Qwen descritas abajo. Para mejor precisión de transcripción puedes elegir un modelo mayor según la memoria disponible. El rendimiento debe medirse en el equipo real.

El servidor procesa una tarea pesada a la vez. Descarga las voces Qwen de memoria antes de pasar a texto o transcripción, y pide a Ollama liberar su modelo al terminar cada consulta. Eso reduce coexistencia de modelos; puede aumentar los tiempos de carga. No se garantiza que todos los modelos quepan en una PC concreta.

## Qué funciona en el código entregado

- Editar/pegar texto; copiar, compartir y exportar TXT.
- Guardado local del proyecto, original conservado y últimas 30 versiones.
- Borrado desde la app de proyectos, reglas, historial, grabaciones internas, audio generado y credenciales recordadas.
- Reglas persistentes de búsqueda/reemplazo, palabra completa y mayúsculas.
- Transcribir un archivo compatible de hasta 24 MB o una URL HTTPS directa sin redirección.
- Reescritura y traducción a un idioma escrito por el usuario, mediante Ollama local u OpenAI, Gemini o Groq con clave propia.
- Identificación de entidades, protección literal de datos detectados/cifras y revisión semántica.
- Propuestas con comparación antes/después; aplicar o descartar. Se bloquean propuestas con marcadores perdidos o duplicados. Una revisión sin avisos no garantiza exactitud.
- Voz Android: seleccionar voces instaladas, velocidad, tono y exportación WAV.
- Voz OpenAI: instrucciones de estilo, acento y emoción; audio WAV unido por segmentos.
- Cliente Qwen y servidor Python para diseñar/clonar voces en un equipo propio.
- Aviso inicial de uso responsable y declaración de permiso al usar clonación.

## Uso inicial

1. Instala el APK. Es una app nueva y no sustituye a la versión 0.1.
2. Puedes editar texto y usar reglas sin API.
3. Para procesar en tu servidor propio configura su dirección y token. Si eliges API personal, selecciona OpenAI, Gemini o Groq, agrega la clave correspondiente y habilita las funciones conectadas; esa alternativa puede tener costo y no incluye saldo.
4. La clave activa puede guardarse cifrada con Android Keystore, opcionalmente. El token del servidor propio permanece solo en la sesión.
5. Mantén la app abierta durante las tareas. No hay un servicio de generación en segundo plano.
6. En Voz > Qwen puedes exportar este código y el servidor como ZIP.

## Motores y límites reales

- Android: la calidad depende del TTS y de la voz instalados. Algunas voces requieren red. No soporta dirección emocional independiente ni clonación.
- OpenAI: usa /v1/audio/speech con gpt-4o-mini-tts por defecto. La documentación anuncia su retirada el 6 de enero de 2027: será necesaria una actualización a la API nueva, no solo cambiar el nombre del modelo. Los modelos de texto y transcripción son configurables.
- Google Gemini: usa `models.generateContent` para tareas de texto y JSON, con `gemini-3.8-flash` como valor inicial; no se usa todavía para transcribir ni narrar dentro de esta app.
- Groq: usa Chat Completions para texto y `audio/transcriptions` para audio. Los valores iniciales son `openai/gpt-oss-20b` y `whisper-large-v3-turbo`, editables en Ajustes.
- Qwen: diseño 1.7B VoiceDesign y clonación 0.6B Base por defecto; el modelo de clonación puede configurarse como 1.7B. Diez idiomas, no todos los idiomas posibles. Los modelos se descargan en el servidor al primer uso. No se ejecutan dentro del APK.
- Android/OpenAI: hasta 60 000 caracteres por narración. Qwen: hasta 12 000 por tarea. Reescritura/traducción: hasta 24 000 caracteres por tarea, con hasta tres consultas de IA.
- Se inserta la pausa elegida entre segmentos. La puntuación dirige las pausas interiores.
- Diseño Qwen: la identidad puede variar entre segmentos; crea una muestra corta y úsala luego como referencia de clonación si buscas continuidad.
- Clonación Qwen: muestra limpia de 3–30 segundos, hasta 8 MB. Texto de referencia recomendado; sin él se usa x-vector-only, que puede reducir calidad. Se hereda el estilo de la muestra; no se promete control emocional adicional en el modo Base.
- Cancelar en el teléfono interrumpe la espera, pero no garantiza detener una generación que ya esté ejecutándose en un servidor.

## Instalar el servidor propio en Windows

Requiere Python 3.12 de 64 bits. Recomendable un equipo con GPU NVIDIA compatible y memoria suficiente; el consumo y velocidad deben medirse en el equipo real. No se ha validado una cifra de VRAM o rendimiento para este proyecto. CPU se admite como alternativa, pero puede ser muy lenta. Prevén varios GB de descarga y espacio; el equipo puede no tener memoria suficiente.

Abre PowerShell en `server` y ejecuta `./start-windows.ps1`. El script crea un entorno virtual, instala dependencias y genera un token aleatorio en `server-token.txt`. No modifica por sí solo la política de ejecución de PowerShell ni las reglas del firewall. Si Windows bloquea esos pasos, revisa la configuración para esa red. Si falla la instalación de PyTorch, instala una compilación compatible con tu CPU/GPU según la guía oficial de PyTorch.

Servidor: puerto 8790, un solo proceso. En el APK introduce `http://IP-PRIVADA-DE-TU-PC:8790` y el token impreso. Ambos equipos deben poder comunicarse en esa red. El HTTP local no está cifrado; para acceso remoto debe usarse HTTPS con un certificado reconocido por Android y un proxy seguro. Nunca publiques este servidor de pruebas directamente sin endurecerlo.

Alternativa Linux/macOS: crea un entorno Python 3.12, instala `server/requirements.txt`, define `STUDIO_TOKEN` (mínimo 24 caracteres aleatorios) y ejecuta `uvicorn server:app --host 0.0.0.0 --port 8790 --workers 1` desde `server`.

Para un VPS de Hostinger usa `server/DEPLOY-HOSTINGER.md`. Incluye Docker, Ollama con volumen persistente, caché de modelos, una sonda mínima `/live` y un ejemplo de Caddy para HTTPS. El puerto 8790 queda ligado únicamente a `127.0.0.1`; no debe publicarse directamente en Internet. El despliegue real requiere dominio, acceso al VPS y medir sus recursos con los modelos elegidos.

La transcripción escribe el archivo recibido en un temporal y lo borra al finalizar. Las muestras de clonación se procesan en memoria, sin retenerse deliberadamente. No se registra deliberadamente el contenido de las peticiones. Los modelos descargados permanecen en la caché de Hugging Face. El APK guarda la última narración en su almacenamiento privado hasta que se sustituye o se desinstala. El borrado comercial de datos y su procedimiento aún no están completos.

## Antes de vender — pendiente, no implementado

- Definir titular del servicio, domicilio y contacto, países, soporte y modelo de precios.
- Términos de uso, aviso de privacidad, consentimiento/revocación y procedimiento de reclamación, revisados para el negocio real.
- Autorizaciones de clonación que permitan acreditar alcance, duración, identidad y revocación. La casilla del prototipo es una declaración, no una verificación ni autorización de un tercero.
- Cuentas, facturación, cuotas, claves exclusivamente en backend y borrado remoto/de cuentas. El borrado local dentro de la app ya está implementado.
- Reporte de contenido dentro de la app, tratamiento de reportes, medidas contra abuso y requisitos de tienda.
- Auditoría de licencias y dependencias, modelos exactos, derechos sobre muestras y contenido.
- Pruebas reales de calidad, seguridad, dispositivos, carga, costos y recuperación.
- Firma comercial privada y permanente, actualizaciones, privacidad pública y revisión de publicación.

El aviso «no asumimos responsabilidad» no garantiza exención ni reemplaza obligaciones legales. No es una versión lista para cobrar o publicar.

## Validación realizada

Compilación Java, empaquetado y firma de Free/Premium; 187 comprobaciones de protección de datos, Unicode, reemplazos, fragmentación y WAV; pruebas de interfaz para ediciones, importación, grabación, prioridad de URL, historial, proveedores BYOK, modo automático con servidor sin API externa y conservación del editor; y contrato del servidor con inferencia simulada. Docker Compose validó la topología de VPS, volúmenes, límite de memoria y publicación de 8790 únicamente en loopback; el motor Docker local estaba apagado y los contenedores no se ejecutaron. En BlueStacks se instalaron ambas ediciones, se importó un WAV, se grabó un M4A y se transcribió realmente con faster-whisper `tiny` en CPU. También se descargó y transcribió una URL HTTPS directa, con el resultado esperado `This is a test.`. Una grabación sin voz devolvió error 422 sin borrar el texto abierto. En el dispositivo se comprobó además la edición manual, la vista previa y aplicación de una regla, la restauración desde el historial y la recuperación del original. Se exportó e importó físicamente un respaldo JSON que conservó texto, original, una regla y seis versiones sin incluir secretos. El borrado local se ejecutó físicamente: reinició Premium como instalación limpia y respetó el respaldo externo de Descargas. BlueStacks no tiene motor TTS instalado, por lo que la generación Android/WAV debe confirmarse en un teléfono con motor de voz; la app ahora distingue este caso de una inicialización pendiente. No se ejecutó inferencia Qwen/Ollama real ni llamadas facturadas a OpenAI, Gemini o Groq. El caché local encontrado para Whisper `small` estaba incompleto y no se eliminó. Se fija PyAV <19 por compatibilidad con faster-whisper 1.2.1.

## Fuentes técnicas

- https://github.com/SYSTRAN/faster-whisper
- https://docs.ollama.com/api/chat
- https://github.com/QwenLM/Qwen3-TTS
- https://developers.openai.com/api/docs/guides/text-to-speech
- https://developers.openai.com/api/docs/guides/speech-to-text
- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://ai.google.dev/api/generate-content
- https://console.groq.com/docs/openai
- https://console.groq.com/docs/speech-to-text

## Código y reconstrucción

`src/`: aplicación Android y utilidades. `assets/index.html`: interfaz local, sin scripts externos.
`server/`: servicio Qwen. `tests/`: pruebas. `build.sh`: construcción manual con JDK 17 y Android SDK platform 35 / build-tools 35.0.0. Usa un almacén de firma propio. El APK de prueba no contiene la clave de firma.

El código propio se entrega al usuario del proyecto para modificarlo. No se incluyen los pesos de Qwen ni código de sus librerías dentro del APK; el servidor los instala por separado. Sus respectivas licencias siguen siendo aplicables. El nombre de una tecnología no implica respaldo de su proveedor.

Las URL del selector son https://platform.openai.com/api-keys, https://aistudio.google.com/apikey, https://console.groq.com/keys y https://elevenlabs.io/app/settings/api-keys. Cada empresa puede pedir inicio de sesión o cambiar su panel.
