move = input()
if move == "W":
    position = position - 10
elif move == "E":
    position = position + 10
elif move == "A":
    position = position - 1
else:
    print("Beep")
word = "Happy Days"
print(len(word), word.upper(), word[0:5], word[6:])
for letter in word:
    if letter in ["a", "e"]:
        print(letter)
x = 17 % 5
y = 17 // 5
z = 2 ** 3
done = not (x == 2 and y != 3)
import random
dice = random.randint(1, 6)
items = []
items.append(5)
grid = [[0, 0], [0, 0]]
grid[1][0] = 5
with open("FileA.txt") as f:
    line = f.readline()
out = open("FileB.txt", "w")
out.write(line)
out.close()
values = [x * 2 for x in range(5)]
