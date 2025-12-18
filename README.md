# Science Chatbot (frontend + FastAPI backend)

Interfaz tipo chat minimalista para preguntas científicas. El backend por ahora solo responde en modo eco (`Has dicho: ...`) y sirve como esqueleto para conectar futura lógica de búsqueda/citación.

## Estructura

- `frontend/`: HTML/CSS/JS estático estilo ChatGPT.
- `backend/`: API en FastAPI con endpoint `/api/chat` y un `/api/health`.

## Requisitos previos

- Python 3.10+ (recomendado)
- Navegador moderno

## Cómo levantar el backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- El endpoint de prueba queda en `http://127.0.0.1:8000/api/chat`.
- Salud: `http://127.0.0.1:8000/api/health`.

## Cómo servir el frontend

1) En otra terminal, abre la carpeta `frontend` y levanta un servidor estático simple:

```powershell
cd frontend
python -m http.server 5500
```

2) Abre el navegador en `http://127.0.0.1:5500/`.

> Nota: El frontend apunta a `http://127.0.0.1:8000/api/chat`. Si cambias el puerto o dominio del backend, ajusta la URL dentro de `frontend/index.html` en la función `fetch`.

## Flujo esperado

1. Escribe una pregunta científica en el cuadro de texto.
2. El frontend envía `{"message": "..."}` al backend.
3. El backend responde `{"reply": "Has dicho: ..."}`.
4. El chat muestra el mensaje de usuario y la respuesta eco.

## Próximos pasos sugeridos

- Conectar a un motor de búsqueda académica / Wikipedia y devolver citas.
- Agregar almacenamiento de historial en localStorage.
- Añadir pruebas unitarias para la API con `pytest`.
