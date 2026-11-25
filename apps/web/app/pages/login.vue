<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="cb-card w-full max-w-md p-6 md:p-8 space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-primary text-primary-content flex items-center justify-center font-bold text-xl">
          A
        </div>
        <div>
          <h1 class="font-bold text-xl leading-tight">AulaMentor AI</h1>
          <p class="text-xs text-base-content/60">Aprendizaje adaptativo orientado a evidencias</p>
        </div>
      </div>

      <div role="tablist" class="tabs tabs-boxed">
        <a role="tab" class="tab" :class="{ 'tab-active': mode === 'login' }" @click="mode = 'login'">
          Iniciar sesión
        </a>
        <a role="tab" class="tab" :class="{ 'tab-active': mode === 'register' }" @click="mode = 'register'">
          Crear cuenta
        </a>
      </div>

      <div v-if="errorMsg" class="alert alert-error text-sm">
        <span>{{ errorMsg }}</span>
      </div>

      <form class="space-y-4" @submit.prevent="handleSubmit">
        <fieldset v-if="mode === 'register'" class="fieldset">
          <legend class="fieldset-legend">Nombre completo</legend>
          <input v-model="displayName" type="text" required placeholder="Ej. María Paula" class="input input-bordered w-full" />
        </fieldset>

        <fieldset class="fieldset">
          <legend class="fieldset-legend">Correo institucional</legend>
          <input v-model="email" type="email" required placeholder="usuario@aulamentor.test" class="input input-bordered w-full" />
        </fieldset>

        <fieldset class="fieldset">
          <legend class="fieldset-legend">Contraseña</legend>
          <input v-model="password" type="password" required minlength="6" placeholder="••••••••" class="input input-bordered w-full" />
        </fieldset>

        <fieldset v-if="mode === 'register'" class="fieldset">
          <legend class="fieldset-legend">Rol de la cuenta</legend>
          <select v-model="selectedRole" class="select select-bordered w-full">
            <option value="teacher">Docente (Gestión de cursos y preguntas)</option>
            <option value="student">Estudiante (Catálogo y exámenes)</option>
          </select>
        </fieldset>

        <button type="submit" class="btn btn-primary w-full" :disabled="authStore.loading">
          <span v-if="authStore.loading" class="loading loading-spinner loading-sm"></span>
          {{ mode === 'login' ? 'Entrar a la plataforma' : 'Registrar cuenta' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const displayName = ref('')
const email = ref('')
const password = ref('')
const selectedRole = ref<'teacher' | 'student'>('teacher')
const errorMsg = ref('')

const redirectByRole = async () => {
  await navigateTo(authStore.isTeacher ? '/teacher/courses' : '/student/courses')
}

const handleSubmit = async () => {
  errorMsg.value = ''
  try {
    if (mode.value === 'login') {
      await authStore.loginWithEmail(email.value, password.value)
    } else {
      await authStore.registerWithEmail(email.value, password.value, displayName.value, selectedRole.value)
    }
    await redirectByRole()
  } catch (err: any) {
    errorMsg.value = extractApiError(err).message
  }
}
</script>