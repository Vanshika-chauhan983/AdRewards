
import os
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def run_command(command):
    subprocess.check_call(command, shell=True)

def main():
    print("Installing dependencies...")
    packages = ["django", "djangorestframework", "firebase-admin", "django-cors-headers", "python-dotenv"]
    for p in packages:
        try:
            install(p)
        except Exception as e:
            print(f"Failed to install {p}: {e}")

    print("Initializing Django project...")
    try:
        if not os.path.exists("manage.py"):
            subprocess.check_call([sys.executable, "-m", "django", "startproject", "config", "."])
            print("Project created.")
        else:
            print("Project already exists.")
            
        if not os.path.exists("api"):
            subprocess.check_call([sys.executable, "manage.py", "startapp", "api"])
            print("App 'api' created.")
        else:
            print("App 'api' already exists.")
            
    except Exception as e:
        print(f"Error during initialization: {e}")

if __name__ == "__main__":
    main()
