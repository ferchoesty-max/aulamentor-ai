<script setup lang="ts">
const authStore = useAuthStore()
await navigateTo(authStore.isTeacher ? '/teacher/courses' : '/student/courses')
</script>

<template>
  <div class="flex justify-center items-center h-64">
    <span class="loading loading-spinner loading-lg text-primary"></span>
  </div>
</template>