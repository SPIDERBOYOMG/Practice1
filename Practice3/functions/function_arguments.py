#function_arguments.py
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"
def add(*args):
    return sum(args)
def multiply(*args):
    result = 1
    for num in args:
        result *= num
    return result
def divide(a, b=1):
    if b == 0:
        return "Error: Division by zero"
    return a / b
# End of function_arguments.py