names = ["Alice", "Bob", "Charlie"]
scores = [85, 90, 95]

# Enumerate
for index, name in enumerate(names, start=1):
    print(f"{index}. {name}")

# Zip
for name, score in zip(names, scores):
    print(f"{name} scored {score}")
