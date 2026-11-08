# Reglas de mantenimiento de Transcriptor Studio

Estas reglas aplican a cualquier persona o agente que edite este proyecto.

1. No mezclar Transcriptor con Aegis, Antigravity u otro producto.
2. Antes de modificar, identificar si el cambio afecta Windows, APK compartido, Free o Premium.
3. Toda edición de código, configuración, compilación o documentación funcional debe agregar una entrada con fecha a una o más bitácoras:
   - `BITACORAS/APP-WINDOWS.md`
   - `BITACORAS/APK-GENERAL.md`
   - `BITACORAS/APK-FREE.md`
   - `BITACORAS/APK-PREMIUM.md`
4. Cada entrada debe indicar: cambio, motivo, archivos principales, validación realizada y faltantes conocidos.
5. Actualizar `ESTADO-Y-FALTANTES.md` cuando cambie una capacidad, validación o bloqueo.
6. No marcar una función como terminada solo porque compila. Diferenciar compilación, instalación, prueba simulada y prueba real.
7. No guardar claves API, tokens de servidor, contraseñas, modelos pesados ni firma comercial dentro del repositorio o APK.
8. Conservar el original, historial y respaldos al modificar flujos de datos del usuario.
9. No eliminar versiones históricas o copias candidatas hasta comparar contenido, hashes y artefactos recuperables.

Formato de entrada:

```markdown
## AAAA-MM-DD · versión o estado

- Cambio:
- Motivo:
- Archivos:
- Validación:
- Faltantes:
```
