# Frontend
FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY src/ui/frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy tsconfig and other config files
COPY src/ui/frontend/tsconfig*.json ./
COPY src/ui/frontend/.env* ./

# Copy source code
COPY src/ui/frontend/src ./src
COPY src/ui/frontend/public ./public

# Build for production (if needed)
# RUN npm run build

# Start development server
CMD ["npm", "start"] 