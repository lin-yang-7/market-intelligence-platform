FROM node:22-alpine AS build
WORKDIR /app
COPY lite/frontend/package.json ./
# The build runs on the deployment server.  Use a reachable registry and retry
# transient DNS/network failures instead of failing the complete Compose build.
RUN npm config set registry https://registry.npmmirror.com \
    && npm install --no-audit --no-fund \
      --fetch-retries=5 \
      --fetch-retry-mintimeout=20000 \
      --fetch-retry-maxtimeout=120000
COPY lite/frontend/ ./
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY lite/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
