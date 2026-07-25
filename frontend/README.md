# Frontend — Nuxt 4 + TypeScript

SSR/SPA приложение. Исходники приложения лежат в `app/` (структура Nuxt 4).

## Структура

```
frontend/
├── nuxt.config.ts       # конфигурация Nuxt (compatibilityVersion: 4)
├── tsconfig.json
├── package.json
├── app/
│   ├── app.vue          # корневой компонент
│   ├── pages/           # файловый роутинг
│   ├── layouts/         # макеты страниц
│   ├── components/      # переиспользуемые компоненты
│   ├── composables/     # useXxx() композаблы
│   ├── stores/          # Pinia сторы
│   ├── middleware/      # роут-мидлвары
│   └── assets/          # стили, шрифты, изображения
├── public/              # статика как есть
└── server/              # серверные роуты/API (Nitro)
```

## Разработка

Внутри Docker — автоматически (`make up`). Локально без Docker:

```bash
npm install
npm run dev      # http://localhost:3000
```

Обращение к API — через `useRuntimeConfig().public.apiBase`.
