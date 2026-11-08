# Estado y faltantes

Actualizado: 2026-11-08

Ubicación oficial: `C:\Users\Elide\OneDrive\Documentos\PROYECTOS_IA_Y_DESARROLLO\Transcriptor`.

## Estado general

- El proyecto completo fue separado de `ChatGPT\New project` y trasladado a su carpeta propia mediante el plan reversible `68e9722d7335`.
- Android Free y Premium 1.4 compilan y se firman con la clave de desarrollo. Compilaciones anteriores se instalaron como paquetes separados; la recompilación del 2026-11-08 no pudo reinstalarse porque BlueStacks falló al iniciar.
- Free/Premium, biblioteca, historial, reglas, respaldo y borrado local tienen pruebas automatizadas.
- En BlueStacks se validaron importación, grabación, transcripción real con faster-whisper `tiny`, URL HTTPS directa, reglas, historial, respaldo y borrado local.
- OpenAI, Gemini y Groq están integrados con clave propia; no se hicieron llamadas facturadas reales.
- El servidor FastAPI tiene contrato probado con motores simulados y una transcripción real con Whisper `tiny`.
- El despliegue VPS está preparado con Docker Compose y Caddy, pero no se ha desplegado en Hostinger.
- Windows mantiene la fuente 1.1.3; el último empaquetado completo con IA local no quedó validado de extremo a extremo.

## Faltantes de Android/APK

- Probar voz Android y exportación WAV en un teléfono físico con motor TTS instalado.
- Ejecutar traducción/reescritura real con Ollama/Qwen.
- Ejecutar diseño y clonación real con Qwen3-TTS y muestra autorizada.
- Probar llamadas reales de OpenAI, Gemini y Groq con cuentas del propietario.
- Desplegar y medir el VPS real por HTTPS.
- Definir licenciamiento/compra Premium, cuentas, cuotas, facturación y recuperación de acceso.
- Crear firma privada de producción y flujo de publicación/actualización.
- Completar privacidad pública, condiciones, soporte y borrado remoto/de cuenta.

## Faltantes de Windows

- Reconstruir el paquete actual con espacio suficiente.
- Validar `Transcriptor.exe` en una PC limpia.
- Probar transcripción, resumen y traducción local dentro del paquete distribuible.
- Verificar que las DLL Qt/ICU no dependan del PATH de desarrollo.
- Medir memoria, tiempo y espacio de los modelos.
- Alinear interfaz y funciones con Android 1.4 o documentar sus diferencias intencionales.

## Versiones conservadas

- `main.py` y archivos de raíz: aplicación Windows 1.1.3.
- `android-studio`: prototipo Android anterior; conservar como histórico hasta comparar y cerrar migración.
- `android-studio-v1.3`: fuente Android vigente de la línea 1.4.
- `android-studio-v1.3/android-studio-v1.3`: copia anidada que requiere comparar antes de clasificar como histórica o duplicada; no eliminar sin hashes y revisión.
- `android-studio-v1.3.zip`: respaldo/paquete de la fuente Android; conservar hasta verificar su relación exacta.
