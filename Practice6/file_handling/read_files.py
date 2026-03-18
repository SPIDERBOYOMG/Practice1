def read_file(filename):
    """Read and print contents of a file."""
    try:
        with open(filename, 'r') as f:
            print(f.read())
    except FileNotFoundError:
        print("File not found.")

# Example usage
# read_file("example.txt")
