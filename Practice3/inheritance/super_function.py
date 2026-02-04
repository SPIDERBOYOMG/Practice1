#super_function.py
class BaseCalculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
    def divide(self, a, b):
        if b == 0:
            return "Error: Division by zero"
        return a / b

class AdvancedCalculator(BaseCalculator):
    def add(self, a, b, c=0):
        return super().add(a, b) + c

    def multiply(self, a, b, c=1):
        return super().multiply(a, b) * c

    def divide(self, a, b, precision=2):
        result = super().divide(a, b)
        if isinstance(result, str):  # Check for error message
            return result
        return round(result, precision)

#the purpose of super() function is to allow derived classes to call methods from their base classes, enabling code reuse and extending functionality without duplicating code.
#without super() the derived class would have to reimplement the base class methods if it wanted to use them, leading to code duplication and maintenance challenges.
calc = AdvancedCalculator()
print(calc.add(2, 3))          # Output: 5
print(calc.add(2, 3, 4))       # Output: 9
print(calc.multiply(2, 3))     # Output: 6
print(calc.multiply(2, 3, 4))  # Output: 24
print(calc.divide(10, 2))      # Output: 5.0
print(calc.divide(10, 3, 3))   # Output: 3.333
# End of super_function.py
