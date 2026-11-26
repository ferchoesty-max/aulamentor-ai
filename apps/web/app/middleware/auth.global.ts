export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()
  if (!authStore.initialized) {
    await authStore.initAuth()
  }

  if (to.path === '/login') {
    if (authStore.isAuthenticated) {
      return navigateTo(authStore.isTeacher ? '/teacher/courses' : '/student/courses')
    }
    return
  }

  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }

  if (to.path.startsWith('/teacher') && !authStore.isTeacher) {
    return navigateTo('/student/courses')
  }

  if (to.path.startsWith('/student') && !authStore.isStudent) {
    return navigateTo('/teacher/courses')
  }
})