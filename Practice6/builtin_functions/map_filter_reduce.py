from functools import reduce

numbers = [1, 2, 3, 4, 5]

# Map: square numbers
squares = list(map(lambda x: x**2, numbers))
print("Squares:", squares)

# Filter: even numbers
evens = list(filter(lambda x: x % 2 == 0, numbers))
print("Evens:", evens)

# Reduce: sum of numbers
total = reduce(lambda x, y: x + y, numbers)
print("Sum:", total)
