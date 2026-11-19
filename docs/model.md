# Modelo de Datos en Cloud Firestore — AulaMentor AI

Documento de diseño del modelo de datos en **Firebase Cloud Firestore** para el Proyecto 02 (*Lenguajes Modernos de Programación*), cubriendo las **7 colecciones oficiales** y el estado de implementación por revisión.

---

## 1. Mapa General de Colecciones

| Colección | Propósito | Fase de Activación |
|---|---|---|
| `users` | Perfiles y roles (`teacher`, `student`, `admin`) vinculados a Firebase Auth | **R1** (activa) |
| `courses` | Cursos publicados por docentes con sus unidades temáticas | **R1** (activa) |
| `questions` | Banco de preguntas de opción múltiple, dificultad y actividad de refuerzo | **R1** (activa) |
| `enrollments` | Inscripciones de estudiantes a cursos (`{course_id}_{student_uid}`) | **R2** (reglas/consultas preparadas en R1) |
| `attempts` | Intentos de evaluación diagnóstica calificados en el servidor | **R2** |
| `masteryProfiles` | Dominio acumulado por estudiante, curso y tema (`0` a `100`) | **R2** |
| `recommendations` | Actividades de refuerzo sugeridas con explicación y estado | **R2 / R3** |

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
- **Campos:** `course_id`, `student_uid`, `answers`, `score` (`0..100`), `topic_breakdown` (aciertos, errores y dificultad por tema), `attempt_number`, `submitted_at`.

### 2.6 `masteryProfiles/{profileId}` *(R2)*
- **Campos:** `course_id`, `student_uid`, `topic`, `mastery_score` (`0..100`), `level` (`"requiere_refuerzo" | "en_progreso" | "dominado"`), `total_attempts`, `accuracy_rate`, `updated_at`.

### 2.7 `recommendations/{recommendationId}` *(R2 / R3)*
- **Campos:** `course_id`, `student_uid`, `attempt_id`, `topic`, `recommended_level` (`1 | 2 | 3`), `activity_title`, `activity_description`, `explanation` (justificación legible de aciertos/intentos/dificultad), `status` (`"pending" -> "in_progress" -> "completed"`), `created_at`.

---

## 3. Seguridad e Índices (`firebase/`)

- **`firebase/firestore.rules`:** Ningún cliente puede escribir directamente en Firestore (`allow write: if false`); todas las escrituras pasan por la API REST en Python con validación Pydantic y verificación de token/rol. Además, los estudiantes no tienen lectura directa sobre `questions` para proteger `correct_index`.
- **`firebase/firestore.indexes.json`:** Índices compuestos declarados para `questions` (`course_id`, `topic`, `difficulty`), `attempts` (`course_id`, `student_uid`, `submitted_at`) y `enrollments` (`student_uid`, `enrolled_at`).
