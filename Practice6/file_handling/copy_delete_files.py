import shutil
import os

def copy_file(src, dest):
    """Copy file from src to dest."""
    shutil.copy(src, dest)
    print("File copied successfully.")

def delete_file(filename):
    """Delete a file."""
    if os.path.exists(filename):
        os.remove(filename)
        print("File deleted successfully.")
    else:
        print("File does not exist.")
