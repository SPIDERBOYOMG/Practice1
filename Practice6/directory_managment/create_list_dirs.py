import os

def create_directory(dirname):
    """Create a new directory."""
    os.makedirs(dirname, exist_ok=True)
    print(f"Directory '{dirname}' created.")

def list_directories(path="."):
    """List all directories in a given path."""
    dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    print("Directories:", dirs)
