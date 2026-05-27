# ── Stage 1: build the React/Vite app ────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies first (separate layer → cache hit when only src changes)
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build


# ── Stage 2: serve the compiled static files with Nginx ───────────────────────
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
