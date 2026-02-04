#class_methods.py
class Programmer:
    def __init__(self, name, language="Python"):
        self.name = name
        self.language = language

    def greet(self):
        return f"Hello, {self.name}! Welcome to {self.language} programming."

    def code(self, lines):
        return f"{self.name} wrote {lines} lines of {self.language} code."

    def debug(self, errors):
        if errors == 0:
            return f"{self.name} found no errors!"
        return f"{self.name} found and fixed {errors} errors."
    
p = Programmer("Alice", "JavaScript")
print(p.greet())
print(p.code(150))
print(p.debug(3))
# End of class_methods.py
