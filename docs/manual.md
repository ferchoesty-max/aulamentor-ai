# Manual de Usuario y Cuentas de Prueba: AulaMentor AI

Guia operativa para evaluar y recorrer la plataforma con credenciales preconfiguradas.

---

## 1. Cuentas de Acceso Ficticias para Pruebas

Para la evaluacion del proyecto y las demostraciones ante el profesor, se definen los siguientes usuarios ficticios:

| Perfil | Correo Electronico | Contrasena | Rol Asignado | Proposito en la Demostracion |
|---|---|---|---|---|
| **Docente Titular** | `docente@aulamentor.test` | `DemoDocente2026!` | `teacher` | Gestiona el curso, crea preguntas con ponderacion y consulta la analitica grupal |
| **Estudiante 1** | `alumno1@aulamentor.test` | `DemoAlumno2026!` | `student` | Responde el examen con buen dominio en Tema 1 y fallas en Tema 2 |
| **Estudiante 2** | `alumno2@aulamentor.test` | `DemoAlumno2026!` | `student` | Responde el mismo examen con fallas en Tema 1 y aciertos en Tema 2 y 3 |

---

## 2. Flujo Operativo del Docente

1. **Ingreso al Panel:** El profesor inicia sesion con su cuenta y es dirigido a `/teacher/courses`.
2. **Creacion o Seleccion de Curso:** Puede dar de alta materias nuevas ingresando clave, titulo y los nombres de las unidades tematicas.
3. **Carga de Preguntas:** En `/teacher/questions`, ingresa enunciados, cuatro alternativas, marca el indice correcto, selecciona el nivel de dificultad (1 a 3) y define el texto de la actividad de refuerzo vinculada.
4. **Seguimiento Grupal:** En la Revision 3, el profesor accede a `/teacher/analytics` para observar el promedio global y los temas que registran mayor indice de error en el salon.

---

## 3. Flujo Operativo del Estudiante

1. **Inscripcion:** El estudiante entra con sus credenciales a `/student/courses`, consulta la oferta de materias y se inscribe.
2. **Resolucion del Diagnostico:** Accede a `/student/courses/{id}/exam`, lee las preguntas y selecciona sus respuestas.
3. **Revision de Resultados y Recomendaciones:** Al enviar el examen, pasa a `/student/progress` donde revisa:
   - Su barra de avance por cada tema clasificada en `requiere_refuerzo`, `en_progreso` o `dominado`.
   - Las tarjetas con actividades recomendadas por el algoritmo.
   - La explicacion transparente de por que se le asigno cada ejercicio segun su desempeno y dificultad.
   - El control para cambiar el estado de la tarea de `pending` a `in_progress` o `completed`.
