# Transcriptor Studio 1.1 — Free y Premium

Aplicación Android separada de Transcriptor v0.1. La compilación produce dos APK instalables en paralelo:

- `mx.transcriptor.studio.free`: grabación, edición, reglas, 3 proyectos locales, 10 versiones por proyecto, voz Android y exportación local.
- `mx.transcriptor.studio.premium`: todo lo anterior sin los límites locales, más transcripción, resumen, análisis, hablantes, traducción, reescritura y voz OpenAI/Qwen.

Android 8 o superior. No contiene claves API, modelos descargados ni un servicio contratado.

## Qué funciona en el código entregado

- Editar/pegar texto; copiar, compartir y exportar TXT.
- Guardado local del proyecto, original conservado y últimas 30 versiones.
- Reglas persistentes de búsqueda/reemplazo, palabra completa y mayúsculas.
- Transcribir un archivo compatible de hasta 24 MB o una URL HTTPS directa sin redirección.
- Grabar desde el micrófono y usar la grabación como fuente del proyecto.
- Resumir y hacer preguntas sobre una transcripción sin sustituir el texto original.
- Separar hablantes y crear marcas de tiempo mediante el modelo de diarización configurado.
- Guardar y abrir una biblioteca local de proyectos.
- Reescritura y traducción a un idioma escrito por el usuario, mediante API de texto.
- Identificación de entidades, protección literal de datos detectados/cifras y revisión semántica.
- Propuestas con comparación antes/después; aplicar o descartar. Se bloquean propuestas con marcadores perdidos o duplicados. Una revisión sin avisos no garantiza exactitud.
- Voz Android: seleccionar voces instaladas, velocidad, tono y exportación WAV.
- Voz OpenAI: instrucciones de estilo, acento y emoción; audio WAV unido por segmentos.
- Cliente Qwen y servidor Python para diseñar/clonar voces en un equipo propio.
- Aviso inicial de uso responsable y declaración de permiso al usar clonación.

## Compilar en Windows

Con JDK 17 y Android SDK 35 instalados:

```powershell
./build.ps1 -Edition all
```

Los APK se escriben en `dist/`. La primera compilación crea una firma de desarrollo persistente en `.signing/` para permitir actualizaciones locales. Esa firma no debe utilizarse para publicar; la edición comercial necesita un almacén privado y respaldado.

## Uso inicial

1. Instala el APK. Es una app nueva y no sustituye a la versión 0.1.
2. Puedes editar texto y usar reglas sin API.
3. Para transcripción/traducción/reescritura y voz OpenAI, agrega tu propia clave en Ajustes y habilita las funciones conectadas. Tiene costo de API; no incluye saldo.
4. La clave puede guardarse cifrada con Android Keystore, opcionalmente. El token Qwen permanece solo en la sesión.
5. Mantén la app abierta durante las tareas. No hay un servicio de generación en segundo plano.
6. En Voz > Qwen puedes exportar este código y el servidor como ZIP.

## Motores y límites reales

- Android: la calidad depende del TTS y de la voz instalados. Algunas voces requieren red. No soporta dirección emocional independiente ni clonación.
- OpenAI: usa `/v1/responses`, `/v1/audio/transcriptions` y `/v1/audio/speech`. Los modelos de texto, transcripción y voz son configurables.
- La separación de hablantes usa temporalmente `gpt-4o-transcribe-diarize` y `diarized_json`. La documentación oficial indica que ese modelo está deprecado y se apagará el 26 de febrero de 2027; debe migrarse cuando OpenAI publique el flujo recomendado que lo sustituya.
- Qwen: diseño 1.7B VoiceDesign y clonación 0.6B Base por defecto; el modelo de clonación puede configurarse como 1.7B. Diez idiomas, no todos los idiomas posibles. Los modelos se descargan en el servidor al primer uso. No se ejecutan dentro del APK.
- Android/OpenAI: hasta 60 000 caracteres por narración. Qwen: hasta 12 000 por tarea. Reescritura/traducción: hasta 24 000 caracteres por tarea, con hasta tres consultas de IA.
- Se inserta la pausa elegida entre segmentos. La puntuación dirige las pausas interiores.
- Diseño Qwen: la identidad puede variar entre segmentos; crea una muestra corta y úsala luego como referencia de clonación si buscas continuidad.
- Clonación Qwen: muestra limpia de 3–30 segundos, hasta 8 MB. Texto de referencia recomendado; sin él se usa x-vector-only, que puede reducir calidad. Se hereda el estilo de la muestra; no se promete control emocional adicional en el modo Base.
- Cancelar en el teléfono interrumpe la espera, pero no garantiza detener una generación que ya esté ejecutándose en un servidor.

## Instalar el servidor Qwen en Windows

Requiere Python 3.12 de 64 bits. Recomendable un equipo con GPU NVIDIA compatible y memoria suficiente; el consumo y velocidad deben medirse en el equipo real. No se ha validado una cifra de VRAM o rendimiento para este proyecto. CPU se admite como alternativa, pero puede ser muy lenta. Prevén varios GB de descarga y espacio; el equipo puede no tener memoria suficiente.

Abre PowerShell en `server` y ejecuta `./start-windows.ps1`. El script crea un entorno virtual, instala dependencias y genera un token aleatorio en `server-token.txt`. No modifica por sí solo la política de ejecución de PowerShell ni las reglas del firewall. Si Windows bloquea esos pasos, revisa la configuración para esa red. Si falla la instalación de PyTorch, instala una compilación compatible con tu CPU/GPU según la guía oficial de PyTorch.

Servidor: puerto 8790, un solo proceso. En el APK introduce `http://IP-PRIVADA-DE-TU-PC:8790` y el token impreso. Ambos equipos deben poder comunicarse en esa red. El HTTP local no está cifrado; para acceso remoto debe usarse HTTPS con un certificado reconocido por Android y un proxy seguro. Nunca publiques este servidor de pruebas directamente sin endurecerlo.

Alternativa Linux/macOS: crea un entorno Python 3.12, instala `server/requirements.txt`, define `STUDIO_TOKEN` (mínimo 24 caracteres aleatorios) y ejecuta `uvicorn server:app --host 0.0.0.0 --port 8790 --workers 1` desde `server`.

No se retienen muestras en archivos del servidor ni se registra su contenido deliberadamente; las peticiones y audios existen temporalmente en memoria. Los modelos descargados permanecen en la caché de Hugging Face. El APK guarda la última narración en su almacenamiento privado hasta que se sustituye o se desinstala. El borrado comercial de datos y su procedimiento aún no están completos.

## Antes de vender — pendiente, no implementado

- Definir titular del servicio, domicilio y contacto, países, soporte y modelo de precios.
- Términos de uso, aviso de privacidad, consentimiento/revocación y procedimiento de reclamación, revisados para el negocio real.
- Autorizaciones de clonación que permitan acreditar alcance, duración, identidad y revocación. La casilla del prototipo es una declaración, no una verificación ni autorización de un tercero.
- Cuentas, facturación, cuotas, claves exclusivamente en backend, borrado de cuentas/datos.
- Reporte de contenido dentro de la app, tratamiento de reportes, medidas contra abuso y requisitos de tienda.
- Auditoría de licencias y dependencias, modelos exactos, derechos sobre muestras y contenido.
- Pruebas reales de calidad, seguridad, dispositivos, carga, costos y recuperación.
- Firma comercial privada y permanente, actualizaciones, privacidad pública y revisión de publicación.

El aviso «no asumimos responsabilidad» no garantiza exención ni reemplaza obligaciones legales. No es una versión lista para cobrar o publicar.

## Validación realizada

Compilación Java, empaquetado y firma del APK; pruebas de protección de datos y WAV; pruebas de interfaz en Chromium con puente Android simulado; pruebas del protocolo del servidor con inferencia simulada. No se probaron en un Android físico, no se ejecutó inferencia Qwen real y no se realizaron llamadas facturadas a OpenAI.

## Fuentes técnicas

- https://github.com/QwenLM/Qwen3-TTS
- https://developers.openai.com/api/docs/guides/text-to-speech
- https://developers.openai.com/api/docs/guides/speech-to-text
- https://developers.openai.com/api/reference/resources/responses/methods/create

## Código y reconstrucción

`src/`: aplicación Android y utilidades. `assets/index.html`: interfaz local, sin scripts externos.
`server/`: servicio Qwen. `tests/`: pruebas. `build.sh`: construcción manual con JDK 17 y Android SDK platform 35 / build-tools 35.0.0. Usa un almacén de firma propio. El APK de prueba no contiene la clave de firma.

El código propio se entrega al usuario del proyecto para modificarlo. No se incluyen los pesos de Qwen ni código de sus librerías dentro del APK; el servidor los instala por separado. Sus respectivas licencias siguen siendo aplicables. El nombre de una tecnología no implica respaldo de su proveedor.
