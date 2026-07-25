// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  future: {
    // Включает архитектуру Nuxt 4 (srcDir = app/, новая структура директорий).
    compatibilityVersion: 4,
  },
  devtools: { enabled: true },

  modules: ['@pinia/nuxt', '@nuxt/eslint'],

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // Приватные ключи — доступны только на сервере.
    apiSecret: '',
    public: {
      // Доступно на клиенте. Переопределяется NUXT_PUBLIC_API_BASE.
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
    },
  },

  typescript: {
    strict: true,
    typeCheck: false, // включайте в CI: npm run typecheck
  },
})
