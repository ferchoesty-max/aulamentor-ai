# Modelo de Datos en Cloud Firestore — AulaMentor AI

Documento de diseño del modelo de datos en **Firebase Cloud Firestore** para el Proyecto 02 (*Lenguajes Modernos de Programación*), cubriendo las **7 colecciones oficiales** y el estado de implementación por revisión.

---

## 1. Mapa General de Colecciones

| Colección | Propósito | Fase de Activación |
|---|---|---|
| `users` | Perfiles y roles (`teacher`, `student`, `admin`) vinculados a Firebase Auth | **R1** (activa) |
| `courses` | Cursos publicados por docentes con sus unidades temáticas | **R1** (activa) |
| `questions` | Banco de preguntas de opción múltiple, dificultad y actividad de refuerzo | **R1** (activa) |
| `enrollments` | Inscripciones de estudiantes a cursos (`{course_id}_{student_uid}`) | **R2** (activa) |
| `attempts` | Intentos de evaluación diagnóstica calificados en el servidor | **R2** (activa) |
| `masteryProfiles` | Dominio acumulado por estudiante, curso y tema (`0` a `100`) | **R2** (activa) |
| `recommendations` | Actividades de refuerzo sugeridas con explicación y estado | **R2** (activa; asignación manual en R3) |

---

## 2. Especificación por Colección

### 2.1 `users/{uid}`
- **Clave de documento:** `uid` de Firebase Authentication (o `mock-<role>-uid` en modo demo).
- **Campos:**
  - `uid` (`string`): Identificador único del usuario.
  - `email` (`string`): Correo electrónico.
  - `display_name` (`string`): Nombre visible en la plataforma.
  - `role` (`"teacher" | "student" | "admin"`): Rol de acceso validado en backend y reglas de Firestore.
  - `created_at` (`string`, ISO 8601 UTC) / `updated_at` (`string`, opcional).

### 2.2 `courses/{courseId}`
- **Campos:**
  - `title` (`string`, 3–120 caracteres): Nombre del curso.
  - `code` (`string`, 2–20 caracteres en mayúsculas, único): Clave del curso (ej. `EDA-101`).
  - `description` (`string`, máx. 1000): Objetivo o descripción general.
  - `topics` (`string[]`, 1–30 elementos únicos): Unidades temáticas del curso.
  - `teacher_uid` (`string`): UID del docente creador.
  - `teacher_name` (`string`): Nombre del docente creador.
  - `status` (`"active" | "archived"`): Estado del curso.
  - `created_at` / `updated_at` (`string`, ISO 8601 UTC).

### 2.3 `questions/{questionId}`
- **Campos:**
  - `course_id` (`string`): Referencia al curso en `courses`.
  - `topic` (`string`): Tema perteneciente a `course.topics`.
  - `difficulty` (`1 | 2 | 3`): `1` básico, `2` intermedio, `3` avanzado.
  - `statement` (`string`, 5–500): Enunciado de la pregunta.
  - `options` (`string[4]`): Exactamente 4 opciones distintas.
  - `correct_index` (`0 | 1 | 2 | 3`): Índice de la respuesta correcta *(ocultado siempre al rol `student`)*.
  - `reinforcement_activity` (`object | null`): `{ title: string, description: string }` asociado al reactivo.
  - `active` (`boolean`): Bandera de habilitación lógica.
  - `created_by` (`string`): UID del creador.
  - `created_at` / `updated_at` (`string`, ISO 8601 UTC).

### 2.4 `enrollments/{courseId}_{studentUid}` *(R2)*
- **Campos:** `course_id`, `student_uid`, `student_name`, `status` (`"enrolled" | "completed"`), `enrolled_at`.
- **Regla de negocio:** Impide inscripciones duplicadas usando clave compuesta `{course_id}_{student_uid}` y bloquea lectura de preguntas/exámenes si el alumno no está inscrito (`403 NOT_ENROLLED`).

### 2.5 `attempts/{attemptId}` *(R2)*
- **Campos:** `course_id`, `student_uid`, `attempt_number`, `answers` (`[{question_id, topic, difficulty, selected_index, is_correct}]`), `score` (`0..100` ponderado por dificultad), `total_questions`, `correct_count`, `topic_breakdown` (`[{topic, correct, total, accuracy, weighted_accuracy, difficulties}]`), `submitted_at`.

### 2.6 `masteryProfiles/{courseId}_{studentUid}_{slug}_{hash}` *(R2)*
- **Campos:** `course_id`, `student_uid`, `topic`, `mastery_score` (`0..100`), `level` (`"requiere_refuerzo" | "en_progreso" | "dominado"`), `total_attempts`, `accuracy_rate`, `weighted_accuracy`, `last_attempt_id`, `updated_at`.

### 2.7 `recommendations/{recommendationId}` *(R2 / R3)*
- **Campos:** `course_id`, `student_uid`, `attempt_id`, `topic`, `recommended_level` (`1 | 2 | 3`), `mastery_score`, `mastery_level`, `activity_title`, `activity_description`, `explanation` (justificación legible de aciertos/intentos/dificultad), `status` (`"pending" -> "in_progress" -> "completed"`), `status_updated_by` *(opcional)*, `created_at`, `updated_at`.

---

## 3. Motor Adaptativo Explicable (sin IA comercial)

Implementado en `apps/api/src/services/adaptive_service.py` y ejecutado automáticamente al calificar cada intento (`POST /api/v1/attempts`):

1. **Pesos por dificultad:** nivel `1` (básica) = `1.0`, nivel `2` (media) = `1.5`, nivel `3` (alta) = `2.0`.
2. **Factor de consistencia por intento (`attempt_number`):** `1.0` en el intento #1, `0.9` en el intento #2 y `max(0.4, 1.0 - 0.15 * (attempt_number - 1))` a partir del intento #3.
3. **Índice de dominio por tema (`0` a `100`):**
   `mastery_score = (weighted_accuracy * 70) + (weighted_accuracy * consistency * 30)`
   donde `weighted_accuracy = earned_weight / total_weight`.
4. **Clasificación y recomendación generada:**
   - `< 60`: `requiere_refuerzo` → actividad de nivel `1` (básico/conceptual).
   - `60 – 84.99`: `en_progreso` → actividad de nivel `2` (intermedio/práctico).
   - `>= 85`: `dominado` → actividad de nivel `3` (avanzado/reto).
5. **Endpoints asociados:**
   - `GET /api/v1/mastery/<course_id>?student_uid=`: perfiles de dominio del estudiante (o de todo el grupo para docente dueño / admin) ordenados por temario.
   - `GET /api/v1/recommendations?course_id=&status=&student_uid=`: lista recomendaciones filtrables por curso, estado (`pending`, `in_progress`, `completed`) o estudiante.
   - `PATCH /api/v1/recommendations/<id>/status`: avanza el estado de forma estricta (`pending` → `in_progress` → `completed`; otra transición devuelve `409 INVALID_STATUS_TRANSITION`).

---

## 4. Seguridad e Índices (`firebase/`)

- **`firebase/firestore.rules`:** Ningún cliente puede escribir directamente en Firestore (`allow write: if false`); todas las escrituras pasan por la API REST en Python con validación Pydantic y verificación de token/rol. Para lectura directa: `users` (propio o admin), `courses` (dueño, admin o activos para estudiantes), `questions` (solo docente dueño o admin, protegiendo `correct_index`) y `enrollments`, `attempts`, `masteryProfiles`, `recommendations` (estudiante dueño, docente del curso o admin).
- **`firebase/firestore.indexes.json`:** Índices compuestos declarados para `questions` (`course_id`, `topic`, `difficulty`), `attempts` (`course_id`, `student_uid`, `submitted_at`) y `enrollments` (`student_uid`, `enrolled_at`).
