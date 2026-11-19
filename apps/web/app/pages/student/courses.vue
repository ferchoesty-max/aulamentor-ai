<template>
  <div class="space-y-6">
    <!-- Cabecera -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">Catálogo de Cursos</h1>
        <p class="text-sm text-base-content/70">Explora las asignaturas activas y consulta tu estado de inscripción.</p>
      </div>
      <button class="btn btn-outline btn-sm" :disabled="loading" @click="fetchCourses">
        Actualizar catálogo
      </button>
    </div>

    <!-- Alerta visual controlada para respuestas 403 / 422 -->
    <div v-if="controlledError" class="alert alert-warning cb-card">
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span class="badge badge-error font-mono">HTTP {{ controlledError.status }}</span>
          <span class="font-bold text-sm">{{ controlledError.code }}</span>
        </div>
        <p class="text-xs mt-1">{{ controlledError.message }}</p>
      </div>
      <button class="btn btn-ghost btn-xs" @click="controlledError = null">Cerrar</button>
    </div>

    <div v-if="loading" class="cb-card p-12 flex justify-center">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else-if="courses.length === 0" class="cb-card p-8 text-center text-base-content/70">
      No hay cursos activos disponibles en este momento.
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="course in courses" :key="course.id" class="cb-card p-5 flex flex-col justify-between gap-4">
        <div class="space-y-2.5">
          <div class="flex items-center justify-between gap-2">
            <span class="badge badge-neutral font-mono text-xs">{{ course.code }}</span>
            <span
              class="badge badge-sm"
              :class="course.enrollment_status === 'enrolled' ? 'badge-success' : course.enrollment_status === 'completed' ? 'badge-info' : 'badge-warning badge-outline'"
            >
              {{ enrollmentLabel(course.enrollment_status) }}
            </span>
          </div>

          <h2 class="font-bold text-base">{{ course.title }}</h2>
          <p class="text-xs text-base-content/70 line-clamp-3">{{ course.description }}</p>

          <div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-base-content/50 mb-1">Temario</p>
            <div class="flex flex-wrap gap-1">
              <span v-for="topic in course.topics" :key="topic" class="badge badge-ghost badge-xs">
                {{ topic }}
              </span>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-base-200 flex justify-end">
          <button
            class="btn btn-sm"
            :class="course.enrollment_status === 'enrolled' ? 'btn-primary' : 'btn-outline'"
            :disabled="checkingCourseId === course.id"
            @click="inspectCourseQuestions(course)"
          >
            <span v-if="checkingCourseId === course.id" class="loading loading-spinner loading-xs"></span>
            {{ course.enrollment_status === 'enrolled' ? 'Ver Preguntas' : 'Probar consulta de preguntas' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Vista previa de preguntas si el alumno sí está inscrito -->
    <div v-if="previewQuestions.length > 0" class="cb-card p-6 border-success space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="font-bold text-base">Preguntas del curso: {{ previewCourseTitle }}</h3>
        <button class="btn btn-ghost btn-xs" @click="previewQuestions = []">Cerrar</button>
      </div>
      <ul class="divide-y divide-base-200">
        <li v-for="(q, idx) in previewQuestions" :key="q.id || idx" class="py-2.5 text-sm">
          <span class="badge badge-xs badge-primary mr-2">{{ q.topic }}</span>
          <span>{{ q.statement }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
interface StudentCourse {
  id: string
  title: string
  code: string
  description: string
  topics: string[]
  enrollment_status?: string | null
}

interface StudentQuestion {
  id: string
  topic: string
  statement: string
}

const { request } = useApi()

const courses = ref<StudentCourse[]>([])
const loading = ref(false)
const checkingCourseId = ref<string | null>(null)
const controlledError = ref<{ status: number; code: string; message: string } | null>(null)
const previewQuestions = ref<StudentQuestion[]>([])
const previewCourseTitle = ref('')

const enrollmentLabel = (status?: string | null) => {
  if (status === 'enrolled') return 'Inscrito'
  if (status === 'completed') return 'Completado'
  return 'No inscrito'
}

const fetchCourses = async () => {
  loading.value = true
  try {
    courses.value = await request<StudentCourse[]>('/api/v1/courses')
  } catch (err) {
    controlledError.value = extractApiError(err)
  } finally {
    loading.value = false
  }
}

const inspectCourseQuestions = async (course: StudentCourse) => {
  controlledError.value = null
  previewQuestions.value = []
  checkingCourseId.value = course.id

  try {
    previewQuestions.value = await request<StudentQuestion[]>(`/api/v1/courses/${course.id}/questions`)
    previewCourseTitle.value = course.title
  } catch (err) {
    const error = extractApiError(err)
    controlledError.value = {
      ...error,
      message: error.code === 'NOT_ENROLLED'
        ? 'No tienes una inscripción activa en este curso. El backend rechazó la consulta (403 NOT_ENROLLED).'
        : error.status === 422
          ? `El backend rechazó la solicitud (422): ${error.message}`
          : error.message
    }
  } finally {
    checkingCourseId.value = null
  }
}

onMounted(fetchCourses)
</script>