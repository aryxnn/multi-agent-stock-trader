FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py accounts.py ./

# Expose Gradio default port
EXPOSE 7860

# Run the Gradio app
CMD ["python", "app.py"]