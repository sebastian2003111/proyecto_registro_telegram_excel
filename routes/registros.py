from fastapi import APIRouter, HTTPException

from schemas.solicitudes import Solicitud, EstadoActualizacion
from services.registro_service import (
    registrar,
    listar,
    actualizar_estado,
    estado_cola,
    reiniciar_contador
)

router = APIRouter(tags=["Solicitudes"])


@router.post("/solicitudes", status_code=201)
def crear_solicitud(solicitud: Solicitud):
    try:
        resultado = registrar(solicitud)
        return resultado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )


@router.get("/solicitudes")
def obtener_solicitudes():
    try:
        resultado = listar()
        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar las solicitudes: {str(e)}"
        )


@router.patch("/solicitudes/{id_registro}")
def cambiar_estado(id_registro: str, payload: EstadoActualizacion):
    try:
        exito = actualizar_estado(id_registro, payload.estado)
        if not exito:
            raise HTTPException(
                status_code=404,
                detail="No se pudo actualizar. Registro no encontrado o error en Google Sheets."
            )
        return {"mensaje": "Estado actualizado correctamente", "id": id_registro, "nuevo_estado": payload.estado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar la solicitud: {str(e)}"
        )


@router.get("/cola/estado")
def consultar_cola():
    """Consulta cuántas solicitudes han entrado y cuántas faltan por procesar en segundo plano."""
    return estado_cola()


@router.post("/reiniciar-contador")
def reset_contador():
    """Reinicia el contador numérico a 0 para empezar una nueva prueba limpia (1 a 10, 1 a 25, etc.)."""
    return reiniciar_contador()