<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">Catálogo de Cursos</h1>
        <p class="text-sm text-base-content/70">Explora las asignaturas activas y consulta tu estado de inscripción.</p>
      </div>
      <button class="btn btn-outline btn-sm" :disabled="loading" @click="fetchCourses">
        Actualizar catálogo
      </button>
    </div>

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
            v-if="!course.enrollment_status"
            class="btn btn-outline btn-sm"
            :disabled="actionCourseId === course.id"
            @click="enrollInCourse(course)"
          >
            <span v-if="actionCourseId === course.id" class="loading loading-spinner loading-xs"></span>
            Inscribirme
          </button>
          <NuxtLink
            v-else
            :to="`/student/courses/${course.id}/exam`"
            class="btn btn-primary btn-sm"
          >
            Presentar examen
          </NuxtLink>
        </div>
      </div>
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

const { request } = useApi()

const courses = ref<StudentCourse[]>([])
const loading = ref(false)
const actionCourseId = ref<string | null>(null)
const controlledError = ref<{ status: number; code: string; message: string } | null>(null)

const enrollmentLabel = (status?: string | null) => {
  if (status === 'enrolled') return 'Inscrito'
  if (status === 'completed') return 'Completado'
  return 'No inscrito'
}

const fetchCourses = async () => {
  controlledError.value = null
  loading.value = true
  try {
    courses.value = await request<StudentCourse[]>('/api/v1/courses')
  } catch (err) {
    controlledError.value = extractApiError(err)
  } finally {
    loading.value = false
  }
}

const enrollInCourse = async (course: StudentCourse) => {
  controlledError.value = null
  actionCourseId.value = course.id

  try {
    await request(`/api/v1/enrollments`, {
      method: 'POST',
      body: { course_id: course.id }
    })
    await fetchCourses()
  } catch (err) {
    controlledError.value = extractApiError(err)
  } finally {
    actionCourseId.value = null
  }
}

onMounted(fetchCourses)
</script>