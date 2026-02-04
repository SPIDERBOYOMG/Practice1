
# Practice3

## Overview
A Python practice project demonstrating core programming concepts and best practices.

## Features
- Clean code structure
- Well-documented functions
- Example implementations

## Installation
```bash
git clone <repository-url>
cd Practice3
pip install -r requirements.txt
```

## Usage
```python
python main.py
```

## Project Structure
```
Practice3/
├── main.py
├── requirements.txt
└── README.md
```

## Getting Started
1. Review the source files
2. Run examples
3. Experiment with modifications

## Resources
- [Python Documentation](https://docs.python.org)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

## License
MIT

---
*Last updated: 2024*
## Contributing
Contributions are welcome! Please follow the PEP 8 style guide and include docstrings for all functions.

## Examples
See the `examples/` directory for sample scripts demonstrating key concepts from Practice 3.
These examples cover object-oriented programming including classes, inheritance, and functional programming with lambda expressions.

### Class Example
```python
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return f"{self.name} makes a sound"

class Dog(Animal):
    def speak(self):
        return f"{self.name} barks"
```

### Lambda Example
```python
# Simple lambda
square = lambda x: x ** 2
print(square(5))  # Output: 25

# Lambda with map
numbers = [1, 2, 3, 4]
doubled = list(map(lambda x: x * 2, numbers))
```

### Combined Example
```python
# Using lambda to sort objects by attribute
animals = [Dog("Rex"), Dog("Max"), Dog("Buddy")]
sorted_animals = sorted(animals, key=lambda animal: animal.name)
```