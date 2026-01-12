#light pythone image
FROM python:3.11-slim

#working directory
WORKDIR /app

#system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# copy requirements file
COPY requirements.txt .

# and install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application code
COPY . .

# expose the port the app runs on
EXPOSE 8000

# command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]