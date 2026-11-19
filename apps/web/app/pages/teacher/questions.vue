<template>
  <div class="space-y-6">
    <!-- Cabecera y selector de curso -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">Banco de Preguntas</h1>
        <p class="text-sm text-base-content/70">Registra reactivos de opción múltiple y actividades de refuerzo por unidad.</p>
      </div>

      <div class="w-full sm:w-80">
        <select v-model="selectedCourseId" class="select select-bordered select-sm w-full" @change="onCourseChange">
          <option disabled value="">Selecciona un curso...</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">
            {{ c.code }} - {{ c.title }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="!selectedCourseId" class="cb-card p-8 text-center text-base-content/70">
      Selecciona un curso en el menú superior para consultar o agregar preguntas.
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Formulario de nueva pregunta -->
      <div class="lg:col-span-5 cb-card p-6 h-fit space-y-4">
        <h2 class="font-bold text-lg">Nueva Pregunta</h2>

        <div v-if="formError" class="alert alert-error text-xs">
          <span>{{ formError }}</span>
        </div>
        <div v-if="formSuccess" class="alert alert-success text-xs">
          <span>{{ formSuccess }}</span>
        </div>

        <form class="space-y-3" @submit.prevent="createQuestion">
          <div class="grid grid-cols-2 gap-3">
            <fieldset class="fieldset">
              <legend class="fieldset-legend">Tema / Unidad</legend>
              <select v-if="selectedCourse?.topics?.length" v-model="form.topic" required class="select select-bordered select-sm w-full">
                <option v-for="t in selectedCourse.topics" :key="t" :value="t">{{ t }}</option>
              </select>
              <input v-else v-model="form.topic" type="text" required placeholder="Tema 1" class="input input-bordered input-sm w-full" />
            </fieldset>

            <fieldset class="fieldset">
              <legend class="fieldset-legend">Dificultad</legend>
              <select v-model.number="form.difficulty" class="select select-bordered select-sm w-full">
                <option :value="1">1 - Básica</option>
                <option :value="2">2 - Intermedia</option>
                <option :value="3">3 - Avanzada</option>
              </select>
            </fieldset>
          </div>

          <fieldset class="fieldset">
            <legend class="fieldset-legend">Enunciado (mín. 5 caracteres)</legend>
            <textarea v-model="form.statement" required minlength="5" rows="2" placeholder="Escribe la pregunta del diagnóstico..." class="textarea textarea-bordered textarea-sm w-full"></textarea>
          </fieldset>

          <div class="space-y-2">
            <p class="text-xs font-semibold">Opciones (marca el círculo de la correcta)</p>
            <div v-for="(opt, idx) in form.options" :key="idx" class="flex items-center gap-2">
              <input
                v-model.number="form.correct_index"
                type="radio"
                name="correct_option"
                :value="idx"
                class="radio radio-primary radio-xs"
              />
              <input
                v-model="form.options[idx]"
                type="text"
                required
                :placeholder="`Opción ${String.fromCharCode(65 + idx)}`"
                class="input input-bordered input-xs w-full"
              />
            </div>
          </div>

          <div class="divider text-[11px] text-base-content/50 my-1">ACTIVIDAD DE REFUERZO (OPCIONAL)</div>

          <div class="space-y-2">
            <input v-model="form.reinforcement_title" type="text" placeholder="Título de la actividad sugerida" class="input input-bordered input-xs w-full" />
            <textarea v-model="form.reinforcement_description" rows="2" placeholder="Breve guía o ejercicio práctico..." class="textarea textarea-bordered textarea-xs w-full"></textarea>
          </div>

          <button type="submit" class="btn btn-primary btn-sm w-full mt-2" :disabled="submitting">
            <span v-if="submitting" class="loading loading-spinner loading-xs"></span>
            Guardar Pregunta
          </button>
        </form>
      </div>

      <!-- Listado de preguntas registradas -->
      <div class="lg:col-span-7 space-y-3">
        <div v-if="loadingQuestions" class="cb-card p-12 flex justify-center">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="questions.length === 0" class="cb-card p-8 text-center text-base-content/70">
          Este curso aún no tiene preguntas registradas.
        </div>

        <div v-else class="space-y-3">
          <div v-for="(q, index) in questions" :key="q.id || index" class="cb-card p-5 space-y-3">
            <div class="flex items-center justify-between gap-2">
              <span class="badge badge-primary badge-sm">{{ q.topic }}</span>
              <span class="badge badge-outline badge-xs">
                Nivel {{ q.difficulty }} · {{ difficultyLabel(q.difficulty) }}
              </span>
            </div>

            <p class="font-semibold text-sm">{{ q.statement }}</p>

            <ul class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <li
                v-for="(option, oIdx) in q.options"
                :key="oIdx"
                class="px-3 py-2 rounded-lg border"
                :class="oIdx === q.correct_index ? 'bg-success/15 border-success font-semibold' : 'border-base-300 bg-base-200/40'"
              >
                {{ String.fromCharCode(65 + oIdx) }}. {{ option }}
              </li>
            </ul>

            <div v-if="q.reinforcement_activity?.title" class="text-xs bg-base-200 p-2.5 rounded-lg">
              <span class="font-semibold">Actividad de refuerzo:</span> {{ q.reinforcement_activity.title }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Course {
  id: string
  title: string
  code: string
  topics: string[]
}

type Difficulty = 1 | 2 | 3

interface Question {
  id?: string
  topic: string
  difficulty: Difficulty
  statement: string
  options: string[]
  correct_index?: number
  reinforcement_activity?: {
    title: string
    description: string
  }
}

const route = useRoute()
const { request } = useApi()

const courses = ref<Course[]>([])
const questions = ref<Question[]>([])
const selectedCourseId = ref<string>((route.query.courseId as string) || '')
const loadingQuestions = ref(false)
const submitting = ref(false)
const formError = ref('')
const formSuccess = ref('')

const form = reactive({
  topic: '',
  difficulty: 1 as Difficulty,
  statement: '',
  options: ['', '', '', ''],
  correct_index: 0,
  reinforcement_title: '',
  reinforcement_description: ''
})

const selectedCourse = computed(() => courses.value.find((c) => c.id === selectedCourseId.value))
const difficultyLabel = (d: number) => (d === 1 ? 'Básica' : d === 2 ? 'Intermedia' : 'Avanzada')

const fetchCourses = async () => {
  formError.value = ''
  try {
    courses.value = await request<Course[]>('/api/v1/courses')
    if (!selectedCourseId.value && courses.value.length > 0) {
      const firstCourse = courses.value[0]
      if (firstCourse) selectedCourseId.value = firstCourse.id
    }
    const firstTopic = selectedCourse.value?.topics[0]
    if (firstTopic) form.topic = firstTopic
    if (selectedCourseId.value) {
      await fetchQuestions()
    }
  } catch (err) {
    formError.value = extractApiError(err).message
  }
}

const fetchQuestions = async () => {
  if (!selectedCourseId.value) return
  loadingQuestions.value = true
  try {
    questions.value = await request<Question[]>(`/api/v1/courses/${selectedCourseId.value}/questions`)
  } catch (err) {
    formError.value = extractApiError(err).message
  } finally {
    loadingQuestions.value = false
  }
}

const onCourseChange = async () => {
  formError.value = ''
  formSuccess.value = ''
  const firstTopic = selectedCourse.value?.topics[0]
  if (firstTopic) form.topic = firstTopic
  await fetchQuestions()
}

const createQuestion = async () => {
  formError.value = ''
  formSuccess.value = ''

  const cleanOptions = form.options.map((option) => option.trim().replace(/\s+/g, ' '))
  if (cleanOptions.some((option) => option.length === 0) ||
      new Set(cleanOptions.map((option) => option.toLocaleLowerCase())).size !== 4) {
    formError.value = 'Las 4 opciones deben ser distintas entre sí.'
    return
  }

  const payload: {
    topic: string
    difficulty: Difficulty
    statement: string
    options: string[]
    correct_index: number
    reinforcement_activity?: { title: string; description: string }
  } = {
    topic: form.topic.trim(),
    difficulty: form.difficulty,
    statement: form.statement.trim(),
    options: cleanOptions,
    correct_index: Number(form.correct_index)
  }

  const reinforcementTitle = form.reinforcement_title.trim()
  const reinforcementDescription = form.reinforcement_description.trim()
  if (reinforcementTitle || reinforcementDescription) {
    if (!reinforcementTitle || !reinforcementDescription) {
      formError.value = 'Completa el título y la descripción de la actividad de refuerzo, o deja ambos vacíos.'
      return
    }
    payload.reinforcement_activity = {
      title: reinforcementTitle,
      description: reinforcementDescription
    }
  }

  submitting.value = true
  try {
    await request<Question>(`/api/v1/courses/${selectedCourseId.value}/questions`, {
      method: 'POST',
      body: payload
    })
    formSuccess.value = 'Pregunta guardada correctamente.'
    form.statement = ''
    form.options = ['', '', '', '']
    form.correct_index = 0
    form.reinforcement_title = ''
    form.reinforcement_description = ''
    await fetchQuestions()
  } catch (err) {
    formError.value = extractApiError(err).message
  } finally {
    submitting.value = false
  }
}

onMounted(fetchCourses)
</script>