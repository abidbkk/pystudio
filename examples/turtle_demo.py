# Turtle demo for PyStudio
# Press Run to watch it draw. Use ⤢ above the drawing to make it bigger.
# Try Debug too: as you step through the code, the drawing builds up line by line.

import turtle

screen = turtle.Screen()
screen.bgcolor("white")

t = turtle.Turtle()
t.shape("turtle")
t.speed(6)

# 1. A filled square
t.penup()
t.goto(-200, 50)
t.pendown()
t.color("blue", "lightblue")
t.begin_fill()
for side in range(4):
    t.forward(100)
    t.left(90)
t.end_fill()

# 2. A star
t.penup()
t.goto(20, 120)
t.pendown()
t.color("orange", "gold")
t.begin_fill()
for point in range(5):
    t.forward(150)
    t.right(144)
t.end_fill()

# 3. A colourful spiral
colours = ["red", "orange", "green", "blue", "purple"]
t.penup()
t.goto(0, -120)
t.pendown()
t.speed(10)
for i in range(40):
    t.pencolor(colours[i % len(colours)])
    t.forward(i * 3)
    t.left(91)

# 4. Circles and text
t.penup()
t.goto(-150, -150)
t.pendown()
t.color("green")
t.circle(40)
t.dot(15, "red")

t.penup()
t.goto(-200, 180)
t.color("black")
t.write("Hello from PyStudio!", font=("Arial", 18, "bold"))

t.hideturtle()
turtle.done()
