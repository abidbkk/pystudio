MAX_TRIES = 3
total_score = 0
name = input("What is your name? ")
age = int(input("Age: "))
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teenager")
else:
    print("Child")
for count in range(1, 11, 2):
    total_score += count  # add it up
average = total_score / 5
print(f"Hello {name}, your average is {average:.2f}")
while total_score > 9:
    total_score = total_score - 9
while True:
    password = input("Password: ")
    if password == "Secret":
        break
def square_sum(a, b):
    return a * a + b * b
print("Sum of squares =", square_sum(10, 20))
