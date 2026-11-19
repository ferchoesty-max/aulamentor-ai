<template>
  <div v-if="!authStore.isAuthenticated" class="min-h-screen bg-base-200">
    <slot />
  </div>

  <div v-else class="drawer lg:drawer-open min-h-screen bg-base-200">
    <input id="app-drawer" type="checkbox" class="drawer-toggle" />

    <div class="drawer-content flex flex-col">
      <!-- Navbar móvil -->
      <header class="navbar bg-base-100 border-b border-base-300 lg:hidden px-4">
        <div class="flex-none">
          <label for="app-drawer" class="btn btn-square btn-ghost">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-5 h-5 stroke-current">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </label>
        </div>
        <div class="flex-1 px-2">
          <span class="font-bold text-lg text-primary">AulaMentor AI</span>
        </div>
      </header>

      <!-- Contenido principal -->
      <main class="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
        <slot />
      </main>
    </div>

    <!-- Sidebar lateral -->
    <aside class="drawer-side z-20">
      <label for="app-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
      <div class="w-64 min-h-full bg-base-100 border-r border-base-300 flex flex-col justify-between p-4">
        <div>
          <div class="flex items-center gap-2.5 px-2 py-3 mb-6">
            <div class="w-9 h-9 rounded-xl bg-primary text-primary-content flex items-center justify-center font-bold text-lg">
              A
            </div>
            <div>
              <h1 class="font-bold text-base leading-tight">AulaMentor AI</h1>
              <p class="text-[11px] text-base-content/60 uppercase tracking-wider font-semibold">
                {{ authStore.user?.role }}
              </p>
            </div>
          </div>

          <ul class="menu menu-md gap-1 w-full p-0">
            <template v-if="authStore.isTeacher">
              <li class="menu-title text-xs uppercase tracking-wider opacity-60">Panel Docente</li>
              <li>
                <NuxtLink to="/teacher/courses" active-class="active font-semibold">
                  Cursos y Unidades
                </NuxtLink>
              </li>
              <li>
                <NuxtLink to="/teacher/questions" active-class="active font-semibold">
                  Banco de Preguntas
                </NuxtLink>
              </li>
            </template>

            <template v-else>
              <li class="menu-title text-xs uppercase tracking-wider opacity-60">Portal Estudiante</li>
              <li>
                <NuxtLink to="/student/courses" active-class="active font-semibold">
                  Catálogo de Cursos
                </NuxtLink>
              </li>
            </template>
          </ul>
        </div>

        <div class="pt-4 border-t border-base-300 space-y-3">
          <div class="px-2">
            <p class="text-xs font-medium truncate">{{ authStore.user?.display_name || 'Usuario Activo' }}</p>
            <p class="text-[11px] text-base-content/60 truncate">{{ authStore.user?.email }}</p>
          </div>
          <button class="btn btn-outline btn-error btn-sm w-full" @click="handleLogout">
            Cerrar sesión
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
const authStore = useAuthStore()

const handleLogout = async () => {
  await authStore.logout()
  await navigateTo('/login')
}
</script>