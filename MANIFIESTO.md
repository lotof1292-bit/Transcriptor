# Manifiesto de Transcriptor Studio

Ubicación oficial del proyecto: `C:\Users\Elide\OneDrive\Documentos\PROYECTOS_IA_Y_DESARROLLO\Transcriptor`.

## Qué es

Transcriptor Studio es una familia de aplicaciones para convertir audio, video o un enlace directo a un texto editable y verificable. Conserva el original y el historial para que la persona pueda corregir, aplicar reglas, traducir, reescribir, resumir, consultar el contenido, crear una narración y recuperar versiones anteriores sin usar una terminal.

El proyecto contiene una aplicación para Windows y una aplicación Android con ediciones Free y Premium. El servidor propio es parte del mismo producto, pero se ejecuta en una PC o VPS; no dentro del APK.

## Meta

Que cualquier persona pueda:

1. Importar o grabar audio y video.
2. Obtener una transcripción sin perder el trabajo abierto ante un error.
3. Corregir manualmente o mediante reglas repetibles.
4. Comparar una propuesta de traducción o reescritura con el original.
5. Recuperar el original o cualquier versión guardada.
6. Escuchar el texto con una voz disponible y exportarlo.
7. Guardar TXT, WAV y un respaldo del proyecto.
8. Elegir entre procesamiento local, servidor propio o una API personal autorizada.

La meta comercial es ofrecer Free como herramienta local útil y Premium como edición completa, sin encerrar al usuario en un único proveedor de IA.

## Principios del producto

- El original nunca debe sustituirse silenciosamente.
- Un error de conexión, formato o ausencia de voz no debe borrar el editor.
- Las claves API no se incluyen en el APK, proyecto ni respaldo.
- El usuario elige si usa servidor propio, OpenAI, Google Gemini o Groq.
- La clonación de voz exige autorización y no debe facilitar suplantación o fraude.
- El procesamiento local debe seguir disponible cuando la función lo permita.
- Free y Premium deben indicar claramente qué está disponible y por qué.
- Cada cambio de código debe registrar lo realizado, su validación y lo pendiente.

## Componentes

### Aplicación Windows

- Código principal: `main.py`.
- Transcripción local con faster-whisper.
- Importación de archivos y enlaces compatibles mediante yt-dlp.
- Resumen y traducción local con Qwen.
- Sustitución global de palabras y exportación.
- Versión de fuente identificada actualmente: 1.1.3.

### Android Free

- Grabación, importación para edición, texto manual y reglas.
- Hasta tres proyectos y diez versiones por proyecto.
- Narración mediante las voces Android instaladas.
- Exportación local y respaldo.
- Sin permiso de Internet; las funciones Premium permanecen visibles con explicación.

### Android Premium

- Todo lo incluido en Free.
- Proyectos locales sin límite artificial y hasta treinta versiones.
- Transcripción, reescritura, traducción, resumen, preguntas y hablantes.
- Servidor propio, modo automático y claves personales de OpenAI, Gemini o Groq.
- Voz OpenAI y diseño/clonación mediante Qwen3-TTS en servidor propio.

### APK y servidor

- Cliente Android en Java con interfaz web integrada.
- Servidor FastAPI con faster-whisper, Ollama/Qwen y Qwen3-TTS.
- Preparación para Windows y para VPS con Docker, HTTPS y proxy inverso.
- Los modelos y sus pesos no se incluyen dentro del APK.

## Definición de terminado

La versión funcional se considera terminada cuando un Android real puede transcribir audio, video y URL directa; editar, traducir y recuperar el original; generar y exportar voz; restaurar un respaldo; y conectarse por HTTPS al VPS. Windows debe ejecutar su paquete publicado sin depender del entorno de desarrollo.

La versión comercial requiere además cuentas, licenciamiento Premium, cuotas, facturación, privacidad pública, borrado remoto, soporte, firma de producción y pruebas de carga/costos.

## Documentos que deben mantenerse

- `INSTRUCCIONES-DE-USO.md`: manual para usuarios.
- `ESTADO-Y-FALTANTES.md`: fotografía actual del proyecto.
- `BITACORAS/APP-WINDOWS.md`: cambios de Windows.
- `BITACORAS/APK-GENERAL.md`: cambios compartidos de Android/servidor.
- `BITACORAS/APK-FREE.md`: cambios específicos de Free.
- `BITACORAS/APK-PREMIUM.md`: cambios específicos de Premium.
