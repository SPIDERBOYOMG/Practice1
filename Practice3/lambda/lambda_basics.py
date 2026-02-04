#lambda_basics.py
greet = lambda name, greeting="Hello": f"{greeting}, {name}!"
add = lambda *args: sum(args)
multiply = lambda *args: __import__('functools').reduce(lambda x, y: x * y, args, 1)
divide = lambda a, b=1: "Error: Division by zero" if b == 0 else a / b
# End of lambda_basics.py
