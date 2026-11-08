# Despliegue 24/7 en un VPS de Hostinger

Este paquete deja Transcriptor detrás de HTTPS. El contenedor de la app solo publica el puerto 8790 en `127.0.0.1`; Caddy es la única entrada pública. No abras el puerto 8790 en el firewall.

## Requisitos

- VPS Linux de 64 bits con Docker Engine y el complemento Docker Compose.
- Un dominio o subdominio apuntando a la IP pública del VPS.
- Puertos TCP 80 y 443 abiertos.
- Memoria y almacenamiento suficientes para Whisper, Ollama y Qwen3-TTS. El tamaño adecuado debe medirse con los modelos reales; un VPS pequeño puede no ejecutar todos simultáneamente.

## Instalación

1. Copia la carpeta `server` al VPS y entra en ella.
2. Crea la configuración privada:

   ```sh
   cp .env.example .env
   TOKEN="$(openssl rand -hex 32)"
   sed -i "s/REEMPLAZAR_POR_64_CARACTERES_HEXADECIMALES/$TOKEN/" .env
   printf '%s\n' "$TOKEN"
   ```

   Guarda ese token en un administrador de contraseñas. No lo publiques ni lo agregues al APK.

3. Construye e inicia los servicios:

   ```sh
   docker compose -f docker-compose.hostinger.yml up -d --build
   docker compose -f docker-compose.hostinger.yml exec ollama ollama pull qwen3:4b
   ```

4. Comprueba el servicio local del VPS:

   ```sh
   curl --fail http://127.0.0.1:8790/live
   set -a; . ./.env; set +a
   curl --fail -H "Authorization: Bearer $STUDIO_TOKEN" http://127.0.0.1:8790/health
   ```

5. Instala Caddy en el sistema, copia `Caddyfile.example` a `/etc/caddy/Caddyfile`, reemplaza `transcriptor.example.com` y recarga Caddy. Caddy obtendrá y renovará el certificado cuando el DNS y los puertos sean correctos.
6. En Transcriptor Premium configura `https://tu-dominio` y el mismo `STUDIO_TOKEN`, luego pulsa **Probar conexión**.

## Operación y actualización

```sh
docker compose -f docker-compose.hostinger.yml ps
docker compose -f docker-compose.hostinger.yml logs --tail 200 transcriptor
docker compose -f docker-compose.hostinger.yml pull
docker compose -f docker-compose.hostinger.yml up -d --build
```

Las cachés de Hugging Face y Ollama viven en volúmenes persistentes. La aplicación procesa una tarea pesada a la vez. Realiza una copia del archivo `.env` por separado; los volúmenes de modelos se pueden reconstruir descargándolos de nuevo.

## Seguridad mínima antes de usuarios reales

- Mantén 8790 ligado a loopback y publica únicamente 80/443.
- Cambia el token si se comparte o aparece en registros. Después actualízalo en los teléfonos autorizados.
- Aplica actualizaciones del sistema y de los contenedores con una ventana de prueba.
- Configura copias, monitoreo de espacio/memoria y alertas de disponibilidad.
- No registres el contenido enviado por usuarios.
- Para vender el servicio todavía faltan cuentas individuales, cuotas, facturación, revocación, borrado de datos y controles contra abuso. Un token compartido no sustituye esas funciones.

## GPU opcional

El archivo entregado funciona en CPU. Para NVIDIA hacen falta controlador, NVIDIA Container Toolkit, una variante compatible de PyTorch y asignar GPU a los servicios. Esa configuración depende del VPS contratado; no actives una reserva de GPU sin verificar que Hostinger exponga una GPU compatible al contenedor.
