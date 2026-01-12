# Using Node 22
FROM node:22-alpine

# Setting working directory
WORKDIR /app

# Copying package files
COPY package*.json ./

# Installing dependencies
RUN npm install

# Copying the rest of the application code
COPY . .

# Exposing port 5173
EXPOSE 5173

# Command to run the application
CMD ["npm", "run", "dev", "--", "--host"]