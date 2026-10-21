a, b = 0, 1
for k in range(10):
    a, b = b, a + b
print(a)
def linear_search(items, target):
    for index in range(len(items)):
        if items[index] == target:
            return index
    return -1
data = [5, 3, 8]
position = linear_search(data, 8)
for n in range(10, 0, -1):
    print(n)
