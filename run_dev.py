import os
import subprocess

# development settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poetry_project.settings_dev')

print("STARTING DEV SERVER...")
subprocess.run([os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts', 'python'), 'manage.py', 'runserver', '8080'])
