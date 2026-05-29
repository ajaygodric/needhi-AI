# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Run the FastAPI backend
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code and assets
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
COPY NotoSansTamil-*.ttf ./

# Set environment variables and expose port
ENV PORT=8000
EXPOSE 8000

# Start command (run from backend directory so server:app is resolved correctly)
CMD ["sh", "-c", "cd backend && uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
