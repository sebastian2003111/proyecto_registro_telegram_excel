import random
from locust import HttpUser, task, between
from locust.exception import StopUser

class UsuarioAPI(HttpUser):
    # Sin wait_time porque queremos que dispare inmediatamente
    
    @task
    def crear_solicitud(self):
        payload = {
            "estudiante": f"Estudiante Prueba {random.randint(1000,9999)}",
            "tipo": "Prueba de Carga",
            "descripcion": "Solicitud generada para el laboratorio de carga.",
            "estado": "PENDIENTE"
        }
        
        with self.client.post(
            "/api/solicitudes",
            json=payload,
            name="POST /api/solicitudes",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Error HTTP: {response.status_code}")
                
        # Detenemos al usuario tras 1 petición para tener exactamente
        # el número de solicitudes deseado en cada prueba (10, 25, 50, 100).
        raise StopUser()