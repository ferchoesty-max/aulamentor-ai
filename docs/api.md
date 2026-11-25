# API REST — AulaMentor AI (v1)

Base: `/api/v1`. Autenticación: `Authorization: Bearer <Firebase ID token>` (en pruebas: `mock-teacher`, `mock-student`, `mock-admin`).

**Éxito:** `{"success": true, "data": ...}` — **Error:** `{"success": false, "error": {"code", "message", "details"}}`.

| Código | Cuándo |
|---|---|
| 401 `UNAUTHENTICATED` | Falta token o es inválido |
| 403 `FORBIDDEN` / `NOT_ENROLLED` | Rol sin permiso, docente ajeno o estudiante sin inscripción `enrolled` |
| 404 `COURSE_NOT_FOUND` / `QUESTION_NOT_FOUND` | El recurso no existe |
| 409 | `DUPLICATE_CODE`, `ALREADY_ENROLLED`, `COURSE_ARCHIVED`, `TOPIC_IN_USE` |
| 422 `VALIDATION_ERROR` / `INVALID_TOPIC` / `INVALID_QUESTION` / `DUPLICATE_ANSWER` | Datos inválidos (`details.fields` lista cada campo) |

## Cursos

| Método y ruta | Roles | Descripción |
|---|---|---|
| `GET /courses` | todos | Docente: sus cursos · Admin: todos · Estudiante: catálogo activo + `enrollment_status` |
| `POST /courses` | teacher, admin | Crea curso `{title, code, description?, topics[]}` → 201 |
| `GET /courses/<id>` | todos | Detalle (estudiante solo si el curso está activo) |
| `PATCH /courses/<id>` | dueño, admin | Edición parcial `{title?, description?, topics?, status?}`. No se puede quitar un tema con preguntas activas (409 `TOPIC_IN_USE`) |
| `DELETE /courses/<id>` | dueño, admin | **Baja lógica**: `status = "archived"` (el documento se conserva) |

## Preguntas

| Método y ruta | Roles | Descripción |
|---|---|---|
| `GET /courses/<id>/questions` | todos | Staff: banco completo con `correct_index`. Estudiante inscrito: solo activas **sin** `correct_index` ni actividad de refuerzo |
| `POST /courses/<id>/questions` | dueño, admin | Crea pregunta `{topic, difficulty 1-3, statement, options[4], correct_index, reinforcement_activity?}` → 201 |
| `PATCH /courses/<id>/questions/<qid>` | dueño, admin | Edición parcial (mismos campos + `active`) |
| `DELETE /courses/<id>/questions/<qid>` | dueño, admin | **Baja lógica**: `active = false` (sale del examen, queda en el historial) |

## Inscripciones

| Método y ruta | Roles | Descripción |
|---|---|---|
| `POST /enrollments` | student | Body `{course_id}`. Crea `enrollments/<course_id>_<uid>` con `status="enrolled"` → 201. Curso archivado → 409, repetida → 409 `ALREADY_ENROLLED` |
| `GET /enrollments/my` | student | Mis inscripciones (con `course_title`) |
| `GET /courses/<id>/enrollments` | dueño, admin | Lista de estudiantes inscritos |

## Intentos de examen

| Método y ruta | Roles | Descripción |
|---|---|---|
| `POST /attempts` | student | Body `{course_id, answers: [{question_id, selected_index 0-3}]}`. Requiere inscripción `enrolled` (403 `NOT_ENROLLED`). El servidor califica con `correct_index` (que nunca sale), guarda el intento y ejecuta el motor adaptativo → 201 |
| `GET /attempts?course_id=&student_uid=` | todos | Estudiante: solo los suyos · Docente: de sus cursos · Admin: todos |

**Respuesta de `POST /attempts`:** `score` (0-100, ponderado por dificultad 1.0 / 1.5 / 2.0), `attempt_number`, `correct_count`, `total_questions`, `answers[]` (`question_id, topic, difficulty, selected_index, is_correct`), `topic_breakdown[]` (`topic, correct, total, accuracy, weighted_accuracy`), más `mastery_profiles[]` y `recommendations[]` generados por el motor de dominio.

## Dominio y recomendaciones (motor adaptativo)

`GET /mastery/<course_id>`, `GET /recommendations`, `PATCH /recommendations/<id>/status` — ver la sección del algoritmo en `docs/model.md`.
