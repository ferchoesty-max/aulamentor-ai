<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Mi progreso</h1>
        <p class="text-sm text-base-content/70">Consulta tu dominio por tema, intentos y actividades recomendadas.</p>
      </div>
      <select
        v-if="courses.length"
        v-model="selectedCourseId"
        class="select select-bordered select-sm w-full sm:w-80"
        @change="fetchProgress"
      >
        <option v-for="item in courses" :key="item.id" :value="item.id">{{ item.code }} · {{ item.title }}</option>
      </select>
    </div>

    <div v-if="pageError" class="alert alert-error">
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span v-if="pageError.status" class="badge badge-error font-mono">HTTP {{ pageError.status }}</span>
          <span class="font-bold text-sm">{{ pageError.code }}</span>
        </div>
        <p class="mt-1 text-sm">{{ pageError.message }}</p>
      </div>
    </div>

    <div v-if="loadingCourses" class="cb-card flex justify-center p-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else-if="courses.length === 0" class="cb-card space-y-3 p-8 text-center">
      <p class="text-base-content/70">Aún no tienes cursos inscritos para consultar el progreso.</p>
      <NuxtLink to="/student/courses" class="btn btn-primary btn-sm">Explorar cursos</NuxtLink>
    </div>

    <template v-else>
      <div v-if="loadingProgress" class="cb-card flex justify-center p-10">
        <span class="loading loading-spinner loading-lg text-primary"></span>
      </div>

      <template v-else-if="selectedCourse">
        <section class="space-y-3">
          <h2 class="text-lg font-bold">Dominio por tema</h2>
          <div class="grid gap-4 md:grid-cols-2">
            <article v-for="topic in selectedCourse.topics" :key="topic" class="cb-card space-y-3 p-5">
              <div class="flex items-center justify-between gap-2">
                <h3 class="font-semibold">{{ topic }}</h3>
                <span v-if="profileForTopic(topic)" class="badge" :class="masteryBadgeClass(profileForTopic(topic)!.level)">
                  {{ masteryLabel(profileForTopic(topic)!.level) }}
                </span>
                <span v-else class="badge badge-ghost">Sin evaluar</span>
              </div>
              <div class="flex items-center gap-3">
                <progress
                  class="progress progress-primary flex-1"
                  :value="profileForTopic(topic)?.mastery_score || 0"
                  max="100"
                ></progress>
                <span class="w-12 text-right text-sm font-semibold">
                  {{ profileForTopic(topic) ? `${profileForTopic(topic)!.mastery_score}%` : '—' }}
                </span>
              </div>
              <p v-if="profileForTopic(topic)" class="text-xs text-base-content/60">
                {{ profileForTopic(topic)!.total_attempts }} intentos · última actualización
                {{ formatDate(profileForTopic(topic)!.updated_at) }}
              </p>
              <p v-else class="text-xs text-base-content/60">Presenta el examen para obtener tu primer resultado.</p>
            </article>
          </div>
        </section>

        <section class="space-y-3">
          <h2 class="text-lg font-bold">Recomendaciones de refuerzo</h2>
          <div v-if="recommendations.length === 0" class="cb-card p-6 text-sm text-base-content/70">
            Todavía no hay recomendaciones. Presenta el examen para que el sistema adapte las actividades a tu resultado.
          </div>
          <article v-for="recommendation in recommendations" :key="recommendation.id" class="cb-card space-y-3 p-5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span class="badge badge-primary badge-sm mr-2">{{ recommendation.topic }}</span>
                <span class="badge badge-outline badge-sm">Nivel {{ recommendation.recommended_level }}</span>
              </div>
              <span class="badge" :class="recommendationStatusClass(recommendation.status)">
                {{ recommendationStatusLabel(recommendation.status) }}
              </span>
            </div>
            <h3 class="font-bold">{{ recommendation.activity_title }}</h3>
            <p class="text-sm">{{ recommendation.activity_description }}</p>
            <p class="rounded-box bg-base-200 p-3 text-sm text-base-content/80">{{ recommendation.explanation }}</p>
            <button
              v-if="nextStatus(recommendation.status)"
              class="btn btn-outline btn-primary btn-sm"
              :disabled="updatingRecommendationId === recommendation.id"
              @click="advanceRecommendation(recommendation)"
            >
              <span v-if="updatingRecommendationId === recommendation.id" class="loading loading-spinner loading-xs"></span>
              {{ recommendation.status === 'pending' ? 'Marcar en progreso' : 'Marcar completada' }}
            </button>
          </article>
        </section>

        <section class="space-y-3">
          <h2 class="text-lg font-bold">Historial de intentos</h2>
          <div v-if="attempts.length === 0" class="cb-card p-6 text-sm text-base-content/70">
            Aún no has presentado evaluaciones en este curso.
          </div>
          <div v-else class="overflow-x-auto cb-card">
            <table class="table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Intento</th>
                  <th>Calificación</th>
                  <th>Aciertos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="attempt in attempts" :key="attempt.id">
                  <td>{{ formatDate(attempt.submitted_at) }}</td>
                  <td>#{{ attempt.attempt_number }}</td>
                  <td class="font-semibold">{{ attempt.score }}%</td>
                  <td>{{ attempt.correct_count }}/{{ attempt.total_questions }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
type MasteryLevel = 'requiere_refuerzo' | 'en_progreso' | 'dominado'
type RecommendationStatus = 'pending' | 'in_progress' | 'completed'

interface StudentCourse {
  id: string
  title: string
  code: string
  topics: string[]
  enrollment_status?: string | null
}

interface MasteryProfile {
  topic: string
  mastery_score: number
  level: MasteryLevel
  total_attempts: number
  updated_at: string
}

interface StudentAttempt {
  id: string
  attempt_number: number
  score: number
  correct_count: number
  total_questions: number
  submitted_at: string
}

interface Recommendation {
  id: string
  topic: string
  recommended_level: number
  activity_title: string
  activity_description: string
  explanation: string
  status: RecommendationStatus
}

const { request } = useApi()
const courses = ref<StudentCourse[]>([])
const selectedCourseId = ref('')
const masteryProfiles = ref<MasteryProfile[]>([])
const attempts = ref<StudentAttempt[]>([])
const recommendations = ref<Recommendation[]>([])
const loadingCourses = ref(true)
const loadingProgress = ref(false)
const updatingRecommendationId = ref<string | null>(null)
const pageError = ref<{ status: number; code: string; message: string } | null>(null)
const selectedCourse = computed(() => courses.value.find((item) => item.id === selectedCourseId.value))

const fetchProgress = async () => {
  if (!selectedCourseId.value) return
  loadingProgress.value = true
  pageError.value = null
  masteryProfiles.value = []
  attempts.value = []
  recommendations.value = []
  try {
    const courseId = encodeURIComponent(selectedCourseId.value)
    masteryProfiles.value = await request<MasteryProfile[]>(`/api/v1/mastery/${courseId}`)
    attempts.value = await request<StudentAttempt[]>(`/api/v1/attempts?course_id=${courseId}`)
    recommendations.value = await request<Recommendation[]>(`/api/v1/recommendations?course_id=${courseId}`)
  } catch (err) {
    pageError.value = extractApiError(err)
  } finally {
    loadingProgress.value = false
  }
}

const fetchCourses = async () => {
  loadingCourses.value = true
  pageError.value = null
  try {
    const allCourses = await request<StudentCourse[]>('/api/v1/courses')
    courses.value = allCourses.filter((item) => item.enrollment_status === 'enrolled' || item.enrollment_status === 'completed')
    if (!courses.value.some((item) => item.id === selectedCourseId.value)) {
      selectedCourseId.value = courses.value[0]?.id || ''
    }
    if (selectedCourseId.value) await fetchProgress()
  } catch (err) {
    pageError.value = extractApiError(err)
  } finally {
    loadingCourses.value = false
  }
}

const profileForTopic = (topic: string) => masteryProfiles.value.find((profile) => profile.topic === topic)

const masteryLabel = (level: MasteryLevel) => ({
  requiere_refuerzo: 'Requiere refuerzo',
  en_progreso: 'En progreso',
  dominado: 'Dominado'
}[level])

const masteryBadgeClass = (level: MasteryLevel) => ({
  requiere_refuerzo: 'badge-error',
  en_progreso: 'badge-warning',
  dominado: 'badge-success'
}[level])

const recommendationStatusLabel = (status: RecommendationStatus) => ({
  pending: 'Pendiente',
  in_progress: 'En progreso',
  completed: 'Completada'
}[status])

const recommendationStatusClass = (status: RecommendationStatus) => ({
  pending: 'badge-warning',
  in_progress: 'badge-info',
  completed: 'badge-success'
}[status])

const nextStatus = (status: RecommendationStatus): RecommendationStatus | null => {
  if (status === 'pending') return 'in_progress'
  if (status === 'in_progress') return 'completed'
  return null
}

const advanceRecommendation = async (recommendation: Recommendation) => {
  const status = nextStatus(recommendation.status)
  if (!status) return
  pageError.value = null
  updatingRecommendationId.value = recommendation.id
  try {
    const updated = await request<Recommendation>(`/api/v1/recommendations/${recommendation.id}/status`, {
      method: 'PATCH',
      body: { status }
    })
    recommendations.value = recommendations.value.map((item) => item.id === recommendation.id ? updated : item)
  } catch (err) {
    pageError.value = extractApiError(err)
  } finally {
    updatingRecommendationId.value = null
  }
}

const formatDate = (value: string) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

onMounted(fetchCourses)
</script>
