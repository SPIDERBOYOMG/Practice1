def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as f:
        f.write(content)
    print("File written successfully.")

# Example usage
# write_file("example.txt", "Hello, world!")
