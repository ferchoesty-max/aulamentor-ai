# Modelo de Datos en Cloud Firestore: AulaMentor AI

Especificacion de las siete colecciones que componen la base de datos de la plataforma, detallando tipos de datos, identificadores y transiciones de estado.

---

## 1. Coleccion `users`
Almacena el perfil publico y permisos de cada cuenta registrada a traves de Firebase Authentication.

| Campo | Tipo | Descripcion |
|---|---|---|
| `uid` | string | Identificador unico proveniente de Firebase Auth (usado como ID del documento) |
| `email` | string | Correo electronico registrado |
| `display_name` | string | Nombre completo o alias para mostrar en la interfaz |
| `role` | string | Rol en el sistema: `'teacher'`, `'student'` o `'admin'` |
| `created_at` | string (ISO-8601) | Marca de tiempo de creacion de la cuenta |

---

## 2. Coleccion `courses`
Representa los cursos dados de alta por los docentes responsables.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador autogenerado del curso |
| `title` | string | Nombre descriptivo del curso |
| `code` | string | Codigo academico o clave del curso (ejemplo: `'LMP-2026'`) |
| `description` | string | Resumen de los objetivos del curso |
| `teacher_uid` | string | Referencia al `uid` del docente creador |
| `topics` | array[string] | Lista de nombres de las unidades tematicas cubiertas |
| `status` | string | Estado actual: `'active'` o `'archived'` |
| `created_at` | string (ISO-8601) | Fecha y hora de creacion |

---

## 3. Coleccion `enrollments`
Vincula a los estudiantes con los cursos a los que tienen acceso habilitado.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador autogenerado de la inscripcion |
| `course_id` | string | Referencia al identificador del curso |
| `student_uid` | string | Referencia al `uid` del alumno |
| `student_name` | string | Nombre del alumno al momento de inscribirse |
| `status` | string | Estado de la matricula: `'enrolled'` o `'completed'` |
| `enrolled_at` | string (ISO-8601) | Fecha y hora de inscripcion |

---

## 4. Coleccion `questions`
Banco de reactivos de opcion multiple creados por el docente para un curso.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador unico del reactivo |
| `course_id` | string | Referencia al curso al que pertenece la pregunta |
| `topic` | string | Unidad tematica evaluada (debe coincidir con un elemento de `courses.topics`) |
| `difficulty` | number | Nivel de complejidad: `1` (basico), `2` (intermedio) o `3` (avanzado) |
| `statement` | string | Enunciado completo de la pregunta |
| `options` | array[string] | Arreglo con las cuatro opciones posibles de respuesta |
| `correct_index` | number | Indice (0 a 3) de la respuesta correcta (confidencial, resguardado en backend) |
| `reinforcement_activity` | map | Actividad asignable si se falla el reactivo (`title`, `description`, `level`) |

---

## 5. Coleccion `attempts`
Bitacora de evaluaciones completadas por un estudiante.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador del intento |
| `course_id` | string | Referencia al curso evaluado |
| `student_uid` | string | Referencia al estudiante que presento la evaluacion |
| `answers` | map[string, number] | Mapa asociando `question_id` con el indice seleccionado |
| `score` | number | Calificacion global obtenida en escala de 0 a 100 |
| `topic_breakdown` | map | Resumen de aciertos, fallos y aciertos ponderados por cada tema |
| `attempt_number` | number | Contador ordinal del intento para ese alumno en el curso |
| `submitted_at` | string (ISO-8601) | Fecha y hora de envio de las respuestas |

---

## 6. Coleccion `masteryProfiles`
Registro consolidado del nivel de dominio conceptual que mantiene un alumno por tema.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador del registro (compuesto por `student_uid` y `topic`) |
| `course_id` | string | Referencia al curso |
| `student_uid` | string | Referencia al estudiante |
| `topic` | string | Nombre de la unidad tematica evaluada |
| `mastery_score` | number | Puntaje ponderado de 0 a 100 calculado por el algoritmo |
| `level` | string | Categoria actual: `'requiere_refuerzo'`, `'en_progreso'` o `'dominado'` |
| `total_attempts` | number | Cantidad total de evaluaciones presentadas |
| `accuracy_rate` | number | Proporcion de aciertos respecto al total de preguntas contestadas |
| `updated_at` | string (ISO-8601) | Ultima actualizacion calculada por el backend |

---

## 7. Coleccion `recommendations`
Actividades de refuerzo o tareas sugeridas automaticamente por el sistema.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | string | Identificador de la recomendacion |
| `course_id` | string | Referencia al curso |
| `student_uid` | string | Referencia al alumno destinatario |
| `attempt_id` | string | Referencia al intento que detono la recomendacion |
| `topic` | string | Unidad tematica correspondiente |
| `recommended_level` | number | Nivel de la actividad sugerida (1, 2 o 3) |
| `activity_title` | string | Titulo de la lectura o ejercicio practico |
| `activity_description` | string | Instrucciones de la tarea |
| `explanation` | string | Justificacion automatica y detallada calculada por el algoritmo |
| `status` | string | Estado de la actividad: `'pending'`, `'in_progress'` o `'completed'` |
| `created_at` | string (ISO-8601) | Fecha y hora de generacion |
