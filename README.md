# Sistema de Registro Académico - FastAPI + Google Sheets + Telegram

Proyecto para la actividad de seguimiento de **Arquitectura de Software y Pruebas de Carga**.

---

## 🚀 Arquitectura Optimizada (Después de la Mejora)

### Problemas identificados en la versión inicial (Antes de la mejora):
1. **Llamadas externas bloqueantes:** La API procesaba las peticiones sincrónicamente esperando a Google Sheets y Telegram, elevando los tiempos de respuesta a más de 37 segundos bajo carga.
2. **Pérdida masiva de datos (Cuota 429):** En 100 solicitudes simultáneas, Google Sheets rechazaba las peticiones por exceder el límite por minuto, perdiendo el 55% de los registros en la hoja.
3. **Desorden en las entregas (Condición de carrera):** Las solicitudes competían en hilos paralelos sin orden, provocando que los mensajes en Telegram y las filas en Google Sheets llegaran desordenadas (ej. mensaje #14 antes del #11).

### Solución Arquitectónica Aplicada:
- **Patrón Productor-Consumidor con Cola Asíncrona FIFO (`queue.Queue`):**
  - La API recibe la solicitud, le asigna un número atómico correlativo (#1, #2, ...), la encola y **responde al cliente inmediatamente en menos de 5 milisegundos (`201 Created`)**.
  - Un **Worker secuencial en segundo plano** extrae las tareas una a una en estricto orden FIFO.
- **Mecanismo de Reintentos con Retroceso Exponencial:**
  - Si Google Sheets o Telegram devuelven error de cuota `429 Too Many Requests`, el worker espera y reintenta automáticamente hasta que la operación se complete. **Garantiza 0% pérdida de datos (100 de 100 llegan a ambos destinos)**.
- **Reutilización de Conexión (Caché de cliente):**
  - Se eliminaron las reconexiones redundantes que agotaban la cuota de lectura de Google Cloud.

---

## 🛠️ Instalación y Configuración

1. Activa tu entorno virtual:
```bash
.\.venv\Scripts\activate
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Asegúrate de tener tu archivo `.env` configurado:
```env
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
GOOGLE_SHEET_ID=tu_sheet_id
GOOGLE_CREDENTIALS_FILE=google_credentials.json
GOOGLE_WORKSHEET_NAME=Registros
```

---

## 🏃 Ejecución del Servidor

```bash
uvicorn main:app --port 8000 --reload
```
Documentación OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Endpoints especiales de control:
- `GET /api/cola/estado`: Muestra en tiempo real cuántas solicitudes se han recibido y cuántas faltan por procesarse en segundo plano.
- `POST /api/reiniciar-contador`: Reinicia el contador numérico a 0 para iniciar una prueba nueva y limpia (del 1 al 10, del 1 al 25, etc.).

---

## 📊 Ejecución de Pruebas con Locust

En una segunda terminal:
```bash
.\.venv\Scripts\locust.exe
```
Abre en tu navegador [http://127.0.0.1:8089](http://127.0.0.1:8089) y configura:
- **Host:** `http://127.0.0.1:8000`
- **Users:** `10`, `25`, `50` o `100` (según la prueba)
- **Spawn rate:** Mismo número que usuarios.
