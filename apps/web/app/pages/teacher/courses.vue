<template>
  <div class="space-y-6">
    <!-- Cabecera -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">Cursos y Unidades</h1>
        <p class="text-sm text-base-content/70">Administra tus asignaturas y temas registrados.</p>
      </div>
      <button class="btn btn-outline btn-sm" :disabled="loadingList" @click="fetchCourses">
        Actualizar lista
      </button>
    </div>

    <!-- Stats resumen -->
    <div class="stats stats-vertical sm:stats-horizontal cb-card w-full">
      <div class="stat">
        <div class="stat-title">Total de Cursos</div>
        <div class="stat-value text-primary">{{ courses.length }}</div>
        <div class="stat-desc">Publicados en catálogo</div>
      </div>
      <div class="stat">
        <div class="stat-title">Unidades Temáticas</div>
        <div class="stat-value">{{ totalTopics }}</div>
        <div class="stat-desc">Temas listos para evaluación</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Formulario de creación -->
      <div class="lg:col-span-4 cb-card p-6 h-fit space-y-4">
        <h2 class="font-bold text-lg">Registrar Nuevo Curso</h2>

        <div v-if="formError" class="alert alert-error text-xs">
          <span>{{ formError }}</span>
        </div>
        <div v-if="formSuccess" class="alert alert-success text-xs">
          <span>{{ formSuccess }}</span>
        </div>

        <form class="space-y-3" @submit.prevent="createCourse">
          <fieldset class="fieldset">
            <legend class="fieldset-legend">Nombre de la materia</legend>
            <input v-model="form.title" type="text" required minlength="3" maxlength="120" placeholder="Ej. Estructuras de Datos" class="input input-bordered input-sm w-full" />
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend">Clave / Código</legend>
            <input v-model="form.code" type="text" required minlength="2" maxlength="20" pattern="[A-Za-z0-9._-]+" placeholder="EDA-101" class="input input-bordered input-sm w-full uppercase" />
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend">Descripción</legend>
            <textarea v-model="form.description" maxlength="1000" rows="2" placeholder="Objetivo general del curso..." class="textarea textarea-bordered textarea-sm w-full"></textarea>
          </fieldset>

          <fieldset class="fieldset">
            <legend class="fieldset-legend">Temas / Unidades</legend>
            <div class="join w-full">
              <input
                v-model="topicInput"
                type="text"
                placeholder="Ej. Árboles Binarios"
                class="input input-bordered input-sm join-item w-full"
                @keydown.enter.prevent="addTopic"
              />
              <button type="button" class="btn btn-sm btn-secondary join-item" @click="addTopic">
                Añadir
              </button>
            </div>
            <div class="flex flex-wrap gap-1.5 mt-2">
              <span v-for="(t, idx) in form.topics" :key="idx" class="badge badge-primary gap-1">
                {{ t }}
                <button type="button" class="text-xs font-bold" @click="removeTopic(idx)">✕</button>
              </span>
            </div>
          </fieldset>

          <button type="submit" class="btn btn-primary btn-sm w-full mt-2" :disabled="submitting">
            <span v-if="submitting" class="loading loading-spinner loading-xs"></span>
            Guardar Curso
          </button>
        </form>
      </div>

      <!-- Tabla / Tarjetas de cursos -->
      <div class="lg:col-span-8 space-y-4">
        <div v-if="loadingList" class="cb-card p-12 flex justify-center">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>

        <div v-else-if="courses.length === 0" class="cb-card p-8 text-center text-base-content/70">
          No hay cursos registrados todavía. Crea el primero usando el formulario lateral.
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="course in courses" :key="course.id" class="cb-card p-5 flex flex-col justify-between gap-4">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="badge badge-neutral font-mono text-xs">{{ course.code }}</span>
                <span class="badge badge-ghost badge-sm">{{ course.status || 'active' }}</span>
              </div>
              <h3 class="font-bold text-base">{{ course.title }}</h3>
              <p class="text-xs text-base-content/70 line-clamp-2">{{ course.description }}</p>

              <div class="pt-1">
                <p class="text-[11px] font-semibold uppercase tracking-wider text-base-content/50 mb-1">Temas</p>
                <div class="flex flex-wrap gap-1">
                  <span v-for="topic in course.topics" :key="topic" class="badge badge-outline badge-xs">
                    {{ topic }}
                  </span>
                </div>
              </div>
            </div>

            <div class="pt-3 border-t border-base-200 flex justify-end">
              <NuxtLink :to="`/teacher/questions?courseId=${course.id}`" class="btn btn-outline btn-primary btn-xs">
                Gestionar Preguntas →
              </NuxtLink>
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
  description: string
  topics: string[]
  status?: string
}

const { request } = useApi()

const courses = ref<Course[]>([])
const loadingList = ref(false)
const submitting = ref(false)
const formError = ref('')
const formSuccess = ref('')
const topicInput = ref('')

const form = reactive({
  title: '',
  code: '',
  description: '',
  topics: [] as string[]
})

const totalTopics = computed(() => courses.value.reduce((acc, c) => acc + (c.topics?.length || 0), 0))

const addTopic = () => {
  const clean = topicInput.value.trim()
  if (clean.length >= 2 && !form.topics.some((topic) => topic.toLocaleLowerCase() === clean.toLocaleLowerCase())) {
    form.topics.push(clean)
  }
  topicInput.value = ''
}

const removeTopic = (idx: number) => {
  form.topics.splice(idx, 1)
}

const fetchCourses = async () => {
  loadingList.value = true
  try {
    courses.value = await request<Course[]>('/api/v1/courses')
  } catch (err) {
    formError.value = extractApiError(err).message
  } finally {
    loadingList.value = false
  }
}

const createCourse = async () => {
  formError.value = ''
  formSuccess.value = ''
  if (form.topics.length === 0) {
    formError.value = 'Agrega al menos un tema o unidad antes de guardar.'
    return
  }

  submitting.value = true
  try {
    await request<Course>('/api/v1/courses', {
      method: 'POST',
      body: {
        title: form.title.trim(),
        code: form.code.trim().toUpperCase(),
        description: form.description.trim(),
        topics: form.topics
      }
    })
    formSuccess.value = 'Curso guardado correctamente.'
    form.title = ''
    form.code = ''
    form.description = ''
    form.topics = []
    await fetchCourses()
  } catch (err) {
    formError.value = extractApiError(err).message
  } finally {
    submitting.value = false
  }
}

onMounted(fetchCourses)
</script>