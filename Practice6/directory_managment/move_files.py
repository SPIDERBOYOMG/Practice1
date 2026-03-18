import shutil

def move_file(src, dest):
    """Move file from src to dest."""
    shutil.move(src, dest)
    print("File moved successfully.")
