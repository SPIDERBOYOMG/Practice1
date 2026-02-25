def generate_squares(n):
    for i in range(1, n+1):
        yield i * i

# Example usage:
for square in generate_squares(5):
    print(square)

def even_numbers(n):
    for i in range(n+1):
        if i % 2 == 0:
            yield i

# Example usage:
n = int(input("Enter a number: "))
print(",".join(str(num) for num in even_numbers(n)))

def divisible_by_3_and_4(n):
    for i in range(n+1):
        if i % 3 == 0 and i % 4 == 0:
            yield i

# Example usage:
for num in divisible_by_3_and_4(50):
    print(num)

def squares(a, b):
    for i in range(a, b+1):
        yield i * i

# Example usage:
for val in squares(3, 7):
    print(val)

def countdown(n):
    while n >= 0:
        yield n
        n -= 1

# Example usage:
for num in countdown(5):
    print(num)
