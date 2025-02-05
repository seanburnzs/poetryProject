import os
import subprocess

# development settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poetry_project.settings_dev')

print("Starting development server...")
subprocess.run(['python', 'manage.py', 'runserver', '8000'])