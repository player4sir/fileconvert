FROM tiangolo/uwsgi-nginx-flask:python3.8

WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create upload folder and set permissions (optional if using volume mount)
RUN mkdir -p /app/uploads
RUN chmod 755 /app/uploads

# Define volume mount for persistent storage (optional)
VOLUME /app/uploads

# Set environment variable for upload folder
ENV UPLOAD_FOLDER=/app/uploads

# Expose port
EXPOSE 5000

# Set environment variable for Flask app
ENV FLASK_APP=app.py

# Start Flask app
CMD ["flask", "run", "--host=0.0.0.0"]