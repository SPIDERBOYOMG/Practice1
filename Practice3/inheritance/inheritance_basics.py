#inheritance_basics.py
class Animal:
    def speak(self):
        return "The animal makes a sound"
class Dog(Animal):
    def speak(self):
        return "Woof! Woof!"
class Cat(Animal):
    def speak(self):
        return "Meow! Meow!"

# Example usage
neutral_animal = Animal()
print(neutral_animal.speak())
dog = Dog()
cat = Cat()
print(dog.speak())
print(cat.speak())
# End of inheritance_basics.py
