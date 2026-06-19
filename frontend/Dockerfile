FROM node:20-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json tsconfig.json next.config.js tailwind.config.js postcss.config.js ./
RUN npm ci

COPY src ./src
RUN npm run build

FROM node:20-alpine

WORKDIR /usr/src/app

COPY package*.json next.config.js ./
RUN npm ci --only=production

COPY --from=builder /usr/src/app/.next ./.next
COPY --from=builder /usr/src/app/public ./public
COPY --from=builder /usr/src/app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
