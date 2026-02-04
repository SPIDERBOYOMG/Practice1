#args_kwargs.py
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"
def add(*args):
    return sum(args)
def multiply(*args):
    result = 1
    for num in args:
        result *= num
    return result
#example of using **kwargs
def introduce(**kwargs):
    introduction = "Introduction:\n"
    for key, value in kwargs.items():
        introduction += f"{key}: {value}\n"
    return introduction
# End of args_kwargs.py