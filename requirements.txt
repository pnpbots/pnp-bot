FROM python:3.11-slim

# Actualizar e instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Actualizar pip y instalar wheel
RUN pip install --upgrade pip setuptools wheel

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Dar permisos de ejecución
RUN chmod +x run_bot.py

# Comando de inicio
CMD ["python", "run_bot.py"]
