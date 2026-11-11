# Especificacion de la API REST: AulaMentor AI

Documentacion de los endpoints del backend en Python Flask para el consumo desde el cliente Nuxt 4.

---

## 1. Convenciones Generales
- **URL Base local:** `http://localhost:8000`
- **Prefijo de API:** `/api/v1`
- **Formato de datos:** `application/json`
- **Autenticacion:** Cabecera HTTP `Authorization: Bearer <firebase_id_token>`
- **Manejo de Errores:** Respuestas estandarizadas con formato:
```json
{
  "success": false,
  "error": {
    "code": "CODIGO_DE_ERROR",
    "message": "Explicacion legible"
  }
}
```

---

## 2. Modulo de Salud y Monitoreo

### `GET /api/v1/health`
Permite comprobar la disponibilidad del servicio y su version.
- **Acceso:** Publico (sin token)
- **Respuesta 200 OK:**
```json
{
  "status": "ok",
  "service": "aulamentor-api",
  "timestamp": "2026-11-11T18:00:00Z",
  "version": "1.0.0"
}
```

---

## 3. Modulo de Autenticacion y Perfiles

### `GET /api/v1/auth/me`
Recupera los datos del usuario actualmente autenticado a partir del token JWT.
- **Acceso:** Protegido (cualquier rol valido)
- **Respuesta 200 OK:**
```json
{
  "success": true,
  "data": {
    "uid": "abc123xyz",
    "email": "docente@aulamentor.test",
    "display_name": "Profesor Demo",
    "role": "teacher"
  }
}
```

### `PUT /api/v1/auth/role`
Actualiza el rol de un usuario en la coleccion `users`.
- **Acceso:** Administrador o el propio usuario en modo desarrollo.
- **Cuerpo de peticion:**
```json
{
  "role": "teacher"
}
```
- **Respuesta 200 OK:** Perfil actualizado.

---

## 4. Modulo de Cursos (Responsabilidad de Maria Paula en R1 y R2)

### `GET /api/v1/courses`
Consulta el listado de cursos activos disponibles.
- **Acceso:** Protegido (estudiantes y docentes)

### `POST /api/v1/courses`
Crea un nuevo curso con su lista de unidades tematicas.
- **Acceso:** Restringido a rol `teacher` o `admin`
- **Cuerpo de peticion:**
```json
{
  "title": "Estructuras de Datos y Algoritmos",
  "code": "EDA-301",
  "description": "Curso fundamental sobre analisis y diseno de algoritmos.",
  "topics": ["Arboles Binarios", "Grafos", "Programacion Dinamica"]
}
```

### `GET /api/v1/courses/{course_id}/questions`
Recupera el banco de preguntas del curso.
- Para rol `teacher`: devuelve el reactivo completo incluyendo `correct_index`.
- Para rol `student`: omite siempre el campo `correct_index`.

### `POST /api/v1/courses/{course_id}/questions`
Registra una nueva pregunta de opcion multiple en el curso.
- **Acceso:** Restringido a rol `teacher` o `admin`

---

## 5. Modulo de Evaluacion y Algoritmo Adaptativo (Responsabilidad de Daniel en R2)

### `POST /api/v1/attempts`
Recibe las respuestas seleccionadas por un estudiante, ejecuta la calificacion en el servidor, actualiza `masteryProfiles` y detona la generacion de `recommendations`.
- **Acceso:** Restringido a rol `student` inscrito en el curso.
- **Cuerpo de peticion:**
```json
{
  "course_id": "eda301",
  "answers": {
    "q1": 0,
    "q2": 2,
    "q3": 1
  }
}
```

### `GET /api/v1/mastery/{course_id}`
Obtiene el perfil consolidado de dominio por temas del estudiante autenticado.

### `GET /api/v1/recommendations`
Consulta las actividades de refuerzo asignadas con su explicacion matematica y conceptual.

### `PATCH /api/v1/recommendations/{id}/status`
Actualiza el estado de una recomendacion (`pending` -> `in_progress` -> `completed`).
