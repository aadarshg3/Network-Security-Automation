import math

# Get input from user
try:
    number = int(input("Enter any number: "))
except ValueError:
    print("Invalid input. Please enter a valid integer.")
    exit()

print("\n🔹 Odd numbers up to", number)
for i in range(1, number + 1):
    if i % 2 != 0:
        print(i, end=" ")

print("\n\n🔹 Even numbers up to", number)
for i in range(1, number + 1):
    if i % 2 == 0:
        print(i, end=" ")

# Square
square = number ** 2
print(f"\n\n🔹 Square of {number} is {square}")

# Cube
cube = number ** 3
print(f"🔹 Cube of {number} is {cube}")

# Square Root
if number >= 0:
    sqrt = math.sqrt(number)
    print(f"🔹 Square root of {number} is {sqrt}")
else:
    print("🔹 Square root is not defined for negative numbers in real numbers.")


# Without Using Module===========

# Get input from user
try:
    number = int(input("Enter any number: "))
except ValueError:
    print("Invalid input. Please enter a valid integer.")
    exit()

# Odd numbers up to N
print("\n🔹 Odd numbers up to", number)
for i in range(1, number + 1):
    if i % 2 != 0:
        print(i, end=" ")

# Even numbers up to N
print("\n\n🔹 Even numbers up to", number)
for i in range(1, number + 1):
    if i % 2 == 0:
        print(i, end=" ")

# Square of the number
square = number * number
print(f"\n\n🔹 Square of {number} is {square}")

# Cube of the number
cube = number * number * number
print(f"🔹 Cube of {number} is {cube}")

# Square root of the number (approximation using simple loop)
if number < 0:
    print("🔹 Square root is not defined for negative numbers in real numbers.")
else:
    x = number
    guess = x / 2
    for _ in range(10):  # 10 iterations of Newton-Raphson method
        guess = (guess + x / guess) / 2
    print(f"🔹 Approximate square root of {number} is {guess}")
