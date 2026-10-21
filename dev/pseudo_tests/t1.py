# Bubble sort
def bubble_sort(numbers):
    for i in range(len(numbers) - 1):
        for j in range(len(numbers) - 1 - i):
            if numbers[j] > numbers[j + 1]:
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]

scores = [72, 88, 95, 60]
bubble_sort(scores)
print("Sorted:", scores[0], scores[1])
