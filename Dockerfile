FROM tiangolo/uwsgi-nginx-flask:python3.8

WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Set environment variable for Flask app
ENV FLASK_APP=app.py

# Start Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
