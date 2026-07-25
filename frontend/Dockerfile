# syntax=docker/dockerfile:1
# --- base ---
FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./

# --- dev: hot-reload через volume, команда переопределяется в override ---
FROM base AS dev
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- build: production-сборка ---
FROM base AS build
RUN npm ci
COPY . .
RUN npm run build

# --- prod: только собранный .output ---
FROM node:22-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
