FROM python:3.11.6-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and other packages
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Remove the pango line from requirements if it exists, then install
RUN pip install --no-cache-dir --upgrade pip && \
    grep -v "^pango==" requirements.txt > requirements_fixed.txt || cp requirements.txt requirements_fixed.txt && \
    pip install --no-cache-dir -r requirements_fixed.txt

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "ULTIMATE_JEE.py"]
