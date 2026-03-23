FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build step required to make Docker image smaller theoretically or run heavily via dev
EXPOSE 3000

# Using dev server to map to localhost accurately 
CMD ["npm", "run", "dev", "--", "--host"]
