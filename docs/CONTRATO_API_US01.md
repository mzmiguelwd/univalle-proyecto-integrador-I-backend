# US-01 — Crear Actividad Evaluativa

## 1. Información General
- **Nombre del endpoint:** Crear actividad evaluativa
- **Historia de Usuario:** US-01
- **Método HTTP:** POST
- **URL:** /tasks/
- **Autenticación:** Token requerida (Bearer Token)

## 2. Descripción
Este endpoint permite a un usuario autenticado crear una nueva actividad evaluativa con la información mínima requerida para su planificación.

La actividad creada quedará asociada automáticamente al usuario autenticado.

## 3. Request
### Headers requeridos
```
Authorization: Token <token>
Content-Type: application/json
```

### Body (JSON)
```
{
  "title": "Parcial 1 Cálculo",
  "task_type": "examen",
  "course": "Cálculo Diferencial",
  "due_date": "2026-03-15T10:00:00",
  "description": "Temas 1 al 5"
}
```

#### Campos
| Campo       | Tipo     | Obligatorio | Descripción                                             |
| ----------- | -------- | ----------- | ------------------------------------------------------- |
| title       | string   | Sí          | Título de la actividad                                  |
| task_type   | string   | Sí          | Tipo de actividad: examen, quiz, taller, proyecto, otro |
| course      | string   | Sí          | Nombre del curso                                        |
| due_date    | datetime | No          | Fecha y hora límite                                     |
| description | string   | No          | Descripción adicional                                   |

## 4. Respuesta Exitosa
### Status Code
```
201 CREATED
```
### Body
```
{
  "id": 5,
  "user": 3,
  "title": "Parcial 1 Cálculo",
  "task_type": "examen",
  "course": "Cálculo Diferencial",
  "due_date": "2026-03-15T10:00:00Z",
  "subtasks": [],
  "created_at": "2026-02-27T18:20:11Z",
  "updated_at": "2026-02-27T18:20:11Z",
  "description": "Temas 1 al 5"
}
```

## 5. Respuestas de Error
### Campos obligatorios vacíos
#### Status Code:
```
400 BAD REQUEST
```
#### Body:
```
{
  "title": ["Este campo no puede estar vacío."],
  "course": ["Este campo no puede estar vacío."]
}
```
### Usuario no autenticado
```
401 UNAUTHORIZED
```
#### Body:
```
{
  "detail": "Authentication credentials were not provided."
}
```

## 6. Relación con Criterios de Aceptación (Gherkin)
### Escenario 1: Creación exitosa

✔ Devuelve 201

✔ Devuelve objeto creado

✔ Permite mostrar mensaje de éxito en frontend

### Escenario 2: Validación de campos obligatorios

✔ Devuelve 400

✔ Devuelve mensajes de error por campo

✔ No crea la actividad