#init_method.py
class Calculator:
    def __init__(self, x=0, y=1):
        self.x = x
        self.y = y
    def add(self):
        return self.x + self.y
    def multiply(self):
        return self.x * self.y
    def divide(self):
        if self.y == 0:
            return "Error: Division by zero"
        return self.x / self.y
# End of init_method.py

