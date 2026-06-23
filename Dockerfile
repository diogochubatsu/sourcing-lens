# Use a lightweight node image
FROM node:20-alpine AS base
RUN apk add --no-cache libc6-compat

# Install dependencies + build
FROM base AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Create storage/data directories (empty placeholders for build)
RUN mkdir -p /app/storage /app/data && chmod 755 /app/storage /app/data
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Production image
FROM base AS runner
RUN apk add --no-cache python3 py3-pip py3-numpy py3-psycopg2
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Set up storage and data directories
RUN mkdir -p /app/storage /app/data
RUN chown -R nextjs:nodejs /app/storage /app/data

# Copy standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# public folder may not exist; copy only if present
COPY --from=builder --chown=nextjs:nodejs /app/public* ./public

# Copy data directory (translations, etc.)
COPY --from=builder --chown=nextjs:nodejs /app/data ./data
# Copy Python scripts for search/matching
COPY --from=builder --chown=nextjs:nodejs /app/scripts ./scripts


EXPOSE 3002
ENV PORT=3002
ENV HOSTNAME="0.0.0.0"

USER nextjs

CMD ["node", "server.js"]
