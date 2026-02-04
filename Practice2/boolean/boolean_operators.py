# boolean_operators.py
# Examples of using boolean operators in Python

def basic_examples():
    a = True
    b = False

    print("a =", a)
    print("b =", b)

    # AND operator
    print("a and b =", a and b)   # True AND False → False
    print("a and True =", a and True)  # True AND True → True

    # OR operator
    print("a or b =", a or b)     # True OR False → True
    print("b or False =", b or False)  # False OR False → False

    # NOT operator
    print("not a =", not a)       # NOT True → False
    print("not b =", not b)       # NOT False → True


def comparison_examples():
    x = 10
    y = 20

    print("\nComparisons:")
    print("x =", x, "y =", y)

    print("x < y:", x < y)        # True
    print("x > y:", x > y)        # False
    print("x == y:", x == y)      # False
    print("x != y:", x != y)      # True

    # Combining comparisons with boolean operators
    print("(x < y) and (x > 0):", (x < y) and (x > 0))   # True AND True → True
    print("(x > y) or (y == 20):", (x > y) or (y == 20)) # False OR True → True


def truthy_falsy_examples():
    print("\nTruthy / Falsy values:")
    print("bool(0):", bool(0))          # False
    print("bool(1):", bool(1))          # True
    print("bool(''):", bool(""))        # False
    print("bool('hello'):", bool("hello"))  # True
    print("bool([]):", bool([]))        # False
    print("bool([1,2,3]):", bool([1,2,3]))  # True


if __name__ == "__main__":
    basic_examples()
    comparison_examples()
    truthy_falsy_examples()
