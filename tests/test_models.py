from schemas.solicitudes import Solicitud
from pydantic import ValidationError
import pytest

def test_solicitud_valida():
    s = Solicitud(
        estudiante="Ana Pérez",
        tipo="Solicitud de certificado",
        descripcion="Requiero certificado de notas del semestre pasado.",
        estado="PENDIENTE"
    )
    assert s.estudiante == "Ana Pérez"
    assert s.estado == "PENDIENTE"

def test_solicitud_estado_invalido():
    with pytest.raises(ValidationError):
        Solicitud(
            estudiante="Juan",
            tipo="Tipo",
            descripcion="Descripción corta",
            estado="INVALIDO"
        )
