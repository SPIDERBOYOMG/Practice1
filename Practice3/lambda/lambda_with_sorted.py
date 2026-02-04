#lambda_with_sorted.py
# Using sorted with lambda functions for basic operations
greet = lambda sort_obj: sorted(map(lambda name: f"Hello, {name}!", sort_obj))
add = lambda sort_obj: sorted(map(lambda nums: sum(nums), sort_obj))
multiply = lambda sort_obj: sorted(map(lambda nums: __import__('functools').reduce(lambda x, y: x * y, nums, 1), sort_obj))
divide = lambda sort_obj: sorted(map(lambda pair: "Error: Division by zero" if pair[1] == 0 else pair[0] / pair[1], sort_obj))
# End of lambda_with_sorted.py
