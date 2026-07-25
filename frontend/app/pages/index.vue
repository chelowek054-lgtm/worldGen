<script setup lang="ts">
// Пример обращения к API бэкенда через runtimeConfig.
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
</script>

<template>
  <main class="home">
    <h1>onlineAtelier</h1>
    <p>Nuxt 4 + TypeScript frontend.</p>
    <p>API base: <code>{{ apiBase }}</code></p>
  </main>
</template>
