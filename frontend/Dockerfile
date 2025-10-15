# Multi-stage build for React frontend
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy shared config (needed for build)
COPY shared/config ./shared/config

# Copy package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies needed for build)
RUN npm ci

# Copy frontend source code
COPY frontend/ .

# IMPORTANT: Posters must be pre-fetched before building
# The backend writes them to frontend/public/posters/ via volume mount
# Now we copy them into the build so they're baked into the static site
# If this fails, run: docker-compose run scraper && wait for backend to prefetch posters

# Build the application (includes posters from frontend/public/posters/)
RUN npm run build

# Production stage - Fully Static (No Backend Dependency)
FROM nginx:alpine AS production

# Copy custom nginx configuration for static site
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Serve all static assets with caching (including posters)
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    # SPA fallback - serve index.html for all routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
EOF

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]