#class_definition.py
class Calculator:
    def __init__(self):
        pass
    def greet(self, name, greeting="Hello"):
        return f"{greeting}, {name}!"
    def add(self, *args):
        return sum(args)
    def multiply(self, *args):
        result = 1
        for num in args:
            result *= num
        return result
    def divide(self, a, b=1):
        if b == 0:
            return "Error: Division by zero"
        return a / b
c = Calculator()
print(c.greet("Alice"))
print(c.add(1, 2, 3, 4))
print(c.multiply(1, 2, 3, 4))
print(c.divide(10, 2))
# End of class_definition.py