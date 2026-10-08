FROM node:20.19.4-alpine3.21
WORKDIR /app
ENV NODE_ENV=production
COPY standalone/ ./
COPY static/ ./.next/static/
COPY public/ ./public/
RUN mkdir -p /app/.next/cache && chown -R node:node /app
USER node
EXPOSE 3000
CMD ["node", "server.js"]
