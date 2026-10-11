from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes.registros import router

app = FastAPI(title="Sistema de Registro - Excel + Telegram")
app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def inicio():
    return FileResponse("static/index.html")
