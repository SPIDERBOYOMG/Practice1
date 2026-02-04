#multiple_inheritance.py
class Flyer:
    def fly(self):
        return "Flying high!"
class Swimmer:
    def swim(self):
        return "Swimming in the water!"
class Duck(Flyer, Swimmer):
    def quack(self):
        return "Quack! Quack!"
    def fly(self):
        return super().fly() + " The duck is soaring!"
    def swim(self):
        return super().swim() + " The duck is paddling!"
    
# we need multiple inheritance when a class needs to inherit features from more than one parent class. 
# This allows for greater flexibility and code reuse, enabling the creation of complex behaviors by combining simpler, well-defined classes.    
# Example usage
donald = Duck()
print(donald.fly())
print(donald.swim())
print(donald.quack())
# End of multiple_inheritance.py