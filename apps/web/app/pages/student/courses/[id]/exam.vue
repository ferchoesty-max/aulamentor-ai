<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <NuxtLink to="/student/courses" class="link link-primary text-sm">← Catálogo de cursos</NuxtLink>
        <h1 class="mt-2 text-2xl font-bold">{{ course?.title || 'Examen' }}</h1>
        <p class="text-sm text-base-content/70">
          Responde las preguntas; el servidor calificará el intento y actualizará tu progreso.
        </p>
      </div>
      <NuxtLink to="/student/progress" class="btn btn-outline btn-sm">Ver mi progreso</NuxtLink>
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

    <div v-if="loading" class="cb-card flex justify-center p-12">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <template v-else-if="course && questions.length">
      <div v-if="result" class="cb-card space-y-4 border border-success p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-sm text-base-content/70">Calificación del intento #{{ result.attempt_number }}</p>
            <h2 class="text-3xl font-bold text-success">{{ result.score }}%</h2>
            <p class="text-sm">{{ result.correct_count }} de {{ result.total_questions }} respuestas correctas</p>
          </div>
          <button class="btn btn-outline btn-sm" @click="startAnotherAttempt">Intentar de nuevo</button>
        </div>

        <div v-if="result.topic_breakdown.length" class="grid gap-3 sm:grid-cols-2">
          <div v-for="topic in result.topic_breakdown" :key="topic.topic" class="rounded-box bg-base-200 p-3">
            <div class="flex justify-between gap-2 text-sm">
              <span class="font-semibold">{{ topic.topic }}</span>
              <span>{{ topic.correct }}/{{ topic.total }} · {{ topic.accuracy }}%</span>
            </div>
            <progress class="progress progress-primary mt-2 w-full" :value="topic.accuracy" max="100"></progress>
          </div>
        </div>

        <div class="space-y-2">
          <h3 class="font-bold">Revisión de respuestas</h3>
          <div
            v-for="answer in result.answers"
            :key="answer.question_id"
            class="flex items-center justify-between gap-3 rounded-box border border-base-300 p-3 text-sm"
          >
            <span>{{ questionLabel(answer.question_id) }}</span>
            <span class="badge" :class="answer.is_correct ? 'badge-success' : 'badge-error'">
              {{ answer.is_correct ? 'Correcta' : 'Incorrecta' }}
            </span>
          </div>
        </div>

        <NuxtLink to="/student/progress" class="btn btn-primary btn-sm">Consultar progreso y recomendaciones</NuxtLink>
      </div>

      <form v-else class="space-y-4" @submit.prevent="submitAttempt">
        <div class="flex items-center justify-between text-sm text-base-content/70">
          <span>{{ questions.length }} preguntas</span>
          <span>{{ answeredCount }} respondidas</span>
        </div>

        <section
          v-for="(question, questionIndex) in questions"
          :key="question.id"
          class="cb-card space-y-4 p-5"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge badge-primary">{{ question.topic }}</span>
            <span class="badge badge-outline">Dificultad {{ question.difficulty }}</span>
          </div>
          <h2 class="font-semibold">{{ questionIndex + 1 }}. {{ question.statement }}</h2>
          <fieldset class="grid gap-2 sm:grid-cols-2">
            <label
              v-for="(option, optionIndex) in question.options"
              :key="optionIndex"
              class="flex cursor-pointer items-start gap-3 rounded-box border border-base-300 p-3 hover:border-primary"
            >
              <input
                v-model="answers[question.id]"
                type="radio"
                :name="`question-${question.id}`"
                :value="optionIndex"
                class="radio radio-primary radio-sm"
              />
              <span class="text-sm">{{ option }}</span>
            </label>
          </fieldset>
        </section>

        <div class="flex justify-end">
          <button class="btn btn-primary" type="submit" :disabled="submitting || answeredCount !== questions.length">
            <span v-if="submitting" class="loading loading-spinner loading-sm"></span>
            Enviar evaluación
          </button>
        </div>
      </form>
    </template>

    <div v-else-if="!loading && course" class="cb-card p-8 text-center">
      <h2 class="font-bold">Este curso aún no tiene preguntas disponibles.</h2>
      <p class="mt-2 text-sm text-base-content/70">Cuando el docente agregue preguntas al examen podrás resolverlo aquí.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface StudentCourse {
  id: string
  title: string
  code: string
  enrollment_status?: string | null
}

interface ExamQuestion {
  id: string
  topic: string
  difficulty: number
  statement: string
  options: string[]
}

interface TopicBreakdown {
  topic: string
  correct: number
  total: number
  accuracy: number
}

interface GradedAnswer {
  question_id: string
  selected_index: number
  is_correct: boolean
}

interface AttemptResult {
  id: string
  attempt_number: number
  score: number
  correct_count: number
  total_questions: number
  topic_breakdown: TopicBreakdown[]
  answers: GradedAnswer[]
}

const route = useRoute()
const { request } = useApi()
const courseId = String(route.params.id)

const course = ref<StudentCourse | null>(null)
const questions = ref<ExamQuestion[]>([])
const answers = reactive<Record<string, number>>({})
const result = ref<AttemptResult | null>(null)
const loading = ref(true)
const submitting = ref(false)
const pageError = ref<{ status: number; code: string; message: string } | null>(null)
const answeredCount = computed(() => Object.keys(answers).length)

const fetchExam = async () => {
  loading.value = true
  pageError.value = null
  course.value = null
  questions.value = []
  result.value = null
  for (const questionId of Object.keys(answers)) delete answers[questionId]
  try {
    const fetchedCourse = await request<StudentCourse>(`/api/v1/courses/${courseId}`)
    course.value = fetchedCourse
    if (fetchedCourse.enrollment_status !== 'enrolled') {
      pageError.value = {
        status: 403,
        code: 'NOT_ENROLLED',
        message: 'Debes inscribirte desde el catálogo antes de presentar este examen.'
      }
      return
    }

    questions.value = await request<ExamQuestion[]>(`/api/v1/courses/${courseId}/questions`)
  } catch (err) {
    pageError.value = extractApiError(err)
  } finally {
    loading.value = false
  }
}

const submitAttempt = async () => {
  pageError.value = null
  if (answeredCount.value !== questions.value.length) {
    pageError.value = {
      status: 422,
      code: 'INCOMPLETE_ATTEMPT',
      message: 'Responde todas las preguntas antes de enviar el examen.'
    }
    return
  }

  submitting.value = true
  try {
    result.value = await request<AttemptResult>('/api/v1/attempts', {
      method: 'POST',
      body: {
        course_id: courseId,
        answers: questions.value.map((question) => ({
          question_id: question.id,
          selected_index: answers[question.id]
        }))
      }
    })
  } catch (err) {
    pageError.value = extractApiError(err)
  } finally {
    submitting.value = false
  }
}

const questionLabel = (questionId: string) => {
  const index = questions.value.findIndex((question) => question.id === questionId)
  return index < 0 ? 'Pregunta' : `Pregunta ${index + 1}`
}

const startAnotherAttempt = () => {
  result.value = null
  for (const questionId of Object.keys(answers)) delete answers[questionId]
}

onMounted(fetchExam)
</script>
