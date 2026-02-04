#lambda_with_filter.py
# Using filter with lambda functions for basic operations
greet = lambda filter_obj: list(filter(lambda name: len(name) > 0, map(lambda name: f"Hello, {name}!", filter_obj)))
add = lambda filter_obj: list(filter(lambda total: total > 0, map(lambda nums: sum(nums), filter_obj)))
multiply = lambda filter_obj: list(filter(lambda product: product > 0, map(lambda nums: __import__('functools').reduce(lambda x, y: x * y, nums, 1), filter_obj)))
divide = lambda filter_obj: list(filter(lambda result: result != "Error: Division by zero", map(lambda pair: "Error: Division by zero" if pair[1] == 0 else pair[0] / pair[1], filter_obj)))
# End of lambda_with_filter.py