FROM node:20-alpine AS build
WORKDIR /app
COPY Frontend/turnos-frontend/package*.json ./
RUN npm ci
COPY Frontend/turnos-frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY Frontend/turnos-frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
