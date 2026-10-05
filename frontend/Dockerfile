# ---- Stage 1: build the static site ----
FROM node:22-alpine AS build

WORKDIR /app

# Dependencies first so this layer is cached until package files change.
# `npm ci` installs exactly what package-lock.json says (reproducible).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite bakes this into the JavaScript at BUILD time. The browser (not the
# container) calls the API, so it must be an address the browser can reach.
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Stage 2: serve it with nginx ----
# Only the built files are copied over, so the final image has no Node and no
# node_modules.
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80