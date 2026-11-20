FROM node:22-slim

WORKDIR /app
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8080
ENV FAWN_RECIPE_DB_PATH=/data/recipes.sqlite

COPY src/client/trace-graph-dp.js ./src/client/trace-graph-dp.js
COPY src/recipe-service ./src/recipe-service

USER node
EXPOSE 8080
CMD ["node", "src/recipe-service/server-main.js"]
