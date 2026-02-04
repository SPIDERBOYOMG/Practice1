#lambda_with_map.py
# Using map with lambda functions for basic operations
greet = lambda map_obj: list(map(lambda name: f"Hello, {name}!", map_obj))
add = lambda map_obj: list(map(lambda nums: sum(nums), map_obj))
multiply = lambda map_obj: list(map(lambda nums: __import__('functools').reduce(lambda x, y: x * y, nums, 1), map_obj))
divide = lambda map_obj: list(map(lambda pair: "Error: Division by zero" if pair[1] == 0 else pair[0] / pair[1], map_obj))
# End of lambda_with_map.py