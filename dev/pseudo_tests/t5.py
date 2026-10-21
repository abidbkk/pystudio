if a > 5:
    print("big")
elif a > 2:
    print("medium")
elif a > 0:
    print("small")
else:
    print("none")
if b == 1:
    print("one")
else:
    if b == 2:
        print("two")
match move:
    case "W":
        position = position - 10
    case "E" | "D":
        position = position + 10
    case _:
        print("Beep")
