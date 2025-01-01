import os
import django
import subprocess

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poetry_project.settings')

# Initialize Django
django.setup()

# Log the server start attempt
print("Starting Daphne on port 8080...")

# Run the Daphne command using subprocess
subprocess.run(['daphne', '-p', '8080', 'poetry_project.asgi:application'])

# Log the server end or any other output
print("Daphne server has stopped.")
