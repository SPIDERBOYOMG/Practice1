import math

degree = 15
radian = math.radians(degree)
print("Input degree:", degree)
print("Output radian:", radian)

height = 5
base1 = 5
base2 = 6

area = ((base1 + base2) / 2) * height
print("Height:", height)
print("Base, first value:", base1)
print("Base, second value:", base2)
print("Expected Output:", area)

import math

n_sides = 4
side_length = 25

area = (n_sides * side_length**2) / (4 * math.tan(math.pi / n_sides))
print("Input number of sides:", n_sides)
print("Input the length of a side:", side_length)
print("The area of the polygon is:", area)

base = 5
height = 6

area = base * height
print("Length of base:", base)
print("Height of parallelogram:", height)
print("Expected Output:", area)
