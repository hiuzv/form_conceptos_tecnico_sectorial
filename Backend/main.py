from fastapi import FastAPI
from Backend.routes import llenado, descarga
from Backend.utils.config import settings
from Backend.utils.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Formulario Web Concepto Tecnico y Sectorial")

origins = settings.CORS_ORIGINS
allow_all = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
    "http://192.168.46.102:3000",
    "http://0.0.0.0:3000",
    "http://127.0.0.1:3000",
]

app.include_router(llenado.router)
app.include_router(descarga.router)

@app.get("/")
def root():
    return {"message": "Formulario service running", "env": settings.ENV}