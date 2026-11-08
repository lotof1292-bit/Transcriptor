# Bitácora · APK Free

## 2026-11-08 · traslado a carpeta propia

- Cambio: fuente, pruebas y APK Free quedaron bajo la ubicación oficial del proyecto.
- Motivo: separar Transcriptor de la carpeta histórica de ChatGPT.
- Archivos: `android-studio-v1.3` y documentación central.
- Validación: presencia del APK y fuente confirmada tras el movimiento.
- Faltantes: reinstalación física pendiente por el fallo de arranque de BlueStacks.

## 2026-11-08 · Free 1.4

- Cambio: se documentaron capacidades y límites; se retiró de la fuente el permiso de Internet y se bloqueó tráfico HTTP para Free.
- Motivo: Free es una edición local y no necesita acceso directo a Internet.
- Archivos: `android-studio-v1.3/AndroidManifest.free.xml`, interfaz y pruebas de edición.
- Validación: la lógica Free bloquea IA Premium, limita la biblioteca a tres proyectos y el historial a diez versiones. Se ejecutó la batería completa, se recompiló el APK y `aapt` confirmó que solo declara `RECORD_AUDIO`; SHA-256 `F30FFD04E5A833DA0BCFE11D409691594C65D9F0F632301B0E49853ABCD45B01`.
- Faltantes: probar voz Android/WAV en teléfono real y reinstalar esta compilación en BlueStacks o dispositivo físico; BlueStacks falló al iniciar el 2026-11-08.

## Capacidades vigentes

- Texto manual, grabación, reglas, original e historial.
- Hasta tres proyectos y diez versiones por proyecto.
- Voz Android y exportación local.
- Importación/exportación mediante selector de documentos, sin acceso general al almacenamiento.
