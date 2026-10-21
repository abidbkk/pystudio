"""PyStudio's turtle: the usual turtle commands, recorded and drawn in the Drawing panel."""
import math as _m

__all__ = ["Turtle", "Pen", "RawTurtle", "Screen", "Vec2D", "done", "mainloop", "exitonclick", "bye",
           "bgcolor", "title", "setup", "screensize", "tracer", "update", "delay", "colormode", "listen",
           "onkey", "onkeypress", "onkeyrelease", "onclick", "onscreenclick", "ontimer",
           "window_width", "window_height", "turtles"]

_MAX = 50000
_cmds = []
_turtles = []
_step = lambda: 0          # set by PyStudio: which debugger step is running
_colormode = [1.0]
_instant = [False]         # tracer(0): draw without animation
_pen = [None]


def _reset():
    _cmds.clear()
    _turtles.clear()
    Turtle._n = 0
    _pen[0] = None
    _colormode[0] = 1.0
    _instant[0] = False
    _screen._bg = "white"


def _record(c):
    if len(_cmds) >= _MAX:
        raise RuntimeError("Too many turtle drawing commands (over 50,000)")
    c["s"] = _step()
    _cmds.append(c)


def _col(args):
    a = args[0] if len(args) == 1 else args
    if isinstance(a, str):
        return a.replace(" ", "")
    if isinstance(a, (tuple, list)) and len(a) == 3:
        r, g, b = a
        if _colormode[0] == 1.0:
            r, g, b = (v * 255 for v in (r, g, b))
        return "rgb(%d,%d,%d)" % (round(r), round(g), round(b))
    raise TypeError("bad colour: %r" % (a,))


def _unsupported(*args, **kwargs):
    raise NotImplementedError("PyStudio's turtle can't react to keys, clicks or timers yet")


class Vec2D(tuple):
    def __new__(cls, x, y):
        return tuple.__new__(cls, (x, y))
    def __add__(self, o): return Vec2D(self[0] + o[0], self[1] + o[1])
    def __sub__(self, o): return Vec2D(self[0] - o[0], self[1] - o[1])
    def __abs__(self): return _m.hypot(self[0], self[1])
    def __repr__(self): return "(%.2f,%.2f)" % self


class Turtle:
    _n = 0

    def __init__(self, shape="classic", visible=True):
        Turtle._n += 1
        self._id = Turtle._n
        self._x = self._y = self._h = 0.0
        self._down = True
        self._pc = self._fc = "black"
        self._w = 1
        self._vis = visible
        self._fill = None
        self._speed = 3
        self._shape = shape
        _turtles.append(self)
        self._emit("r")

    def _emit(self, k, **kw):
        kw.update(k=k, id=self._id, x=round(self._x, 3), y=round(self._y, 3), h=round(self._h, 3),
                  v=self._vis, pc=self._pc, fc=self._fc, w=self._w, sh=self._shape,
                  sp=0 if _instant[0] else self._speed)
        _record(kw)

    # ---- moving
    def _goto(self, x, y):
        x0, y0 = self._x, self._y
        self._x, self._y = float(x), float(y)
        if self._fill is not None:
            self._fill.append((self._x, self._y))
        self._emit("m", x0=round(x0, 3), y0=round(y0, 3), d=self._down)

    def forward(self, distance):
        r = _m.radians(self._h)
        self._goto(self._x + distance * _m.cos(r), self._y + distance * _m.sin(r))
    fd = forward

    def backward(self, distance):
        self.forward(-distance)
    bk = back = backward

    def left(self, angle):
        self._h = (self._h + angle) % 360
        self._emit("r")
    lt = left

    def right(self, angle):
        self.left(-angle)
    rt = right

    def goto(self, x, y=None):
        if y is None:
            x, y = x
        self._goto(x, y)
    setpos = setposition = goto

    def setx(self, x): self._goto(x, self._y)
    def sety(self, y): self._goto(self._x, y)

    def setheading(self, angle):
        self._h = angle % 360
        self._emit("r")
    seth = setheading

    def home(self):
        self._goto(0, 0)
        self.setheading(0)

    def circle(self, radius, extent=None, steps=None):
        extent = 360 if extent is None else extent
        if steps is None:
            steps = 1 + int(min(11 + abs(radius) / 6.0, 59.0) * abs(extent) / 360.0)
        w = extent / steps
        w2 = 0.5 * w
        l = 2.0 * radius * _m.sin(_m.radians(w2))
        if radius < 0:
            l, w, w2 = -l, -w, -w2
        self.left(w2)
        for _ in range(steps):
            self.forward(l)
            self.left(w)
        self.left(-w2)

    def teleport(self, x=None, y=None, **kw):
        d = self._down
        self._down = False
        self._goto(self._x if x is None else x, self._y if y is None else y)
        self._down = d

    # ---- drawing
    def penup(self): self._down = False
    pu = up = penup

    def pendown(self): self._down = True
    pd = down = pendown

    def isdown(self): return self._down

    def pensize(self, width=None):
        if width is None:
            return self._w
        self._w = width
    width = pensize

    def pencolor(self, *args):
        if not args:
            return self._pc
        self._pc = _col(args)
        self._emit("r")

    def fillcolor(self, *args):
        if not args:
            return self._fc
        self._fc = _col(args)
        self._emit("r")

    def color(self, *args):
        if not args:
            return self._pc, self._fc
        if len(args) == 2:
            self._pc, self._fc = _col(args[:1]), _col(args[1:])
        else:
            self._pc = self._fc = _col(args)
        self._emit("r")

    def begin_fill(self):
        self._fill = [(self._x, self._y)]
        self._fill_from = len(_cmds)

    def end_fill(self):
        if self._fill and len(self._fill) > 2:
            self._emit("fill", pts=[round(c, 3) for p in self._fill for c in p], col=self._fc, frm=self._fill_from)
        self._fill = None

    def filling(self): return self._fill is not None

    def dot(self, size=None, *color):
        if size is None:
            size = max(self._w + 4, self._w * 2)
        self._emit("dot", r=size, col=_col(color) if color else self._pc)

    def stamp(self):
        self._emit("stamp")
        return len(_cmds)

    def write(self, arg, move=False, align="left", font=("Arial", 8, "normal")):
        font = tuple(font) + ("Arial", 8, "normal")[len(font):]
        self._emit("write", text=str(arg), align=str(align), font=[str(font[0]), float(font[1]), str(font[2])])

    def clear(self): self._emit("clear")

    def reset(self):
        self._emit("clear")
        self._down, self._pc, self._fc, self._w, self._vis = True, "black", "black", 1, True
        self.teleport(0, 0)
        self.setheading(0)

    # ---- turtle look
    def speed(self, speed=None):
        if speed is None:
            return self._speed
        speed = {"fastest": 0, "fast": 10, "normal": 6, "slow": 3, "slowest": 1}.get(speed, speed)
        self._speed = int(round(speed)) if 0.5 <= speed <= 10.5 else 0

    def hideturtle(self):
        self._vis = False
        self._emit("r")
    ht = hideturtle

    def showturtle(self):
        self._vis = True
        self._emit("r")
    st = showturtle

    def isvisible(self): return self._vis

    def shape(self, name=None):
        if name is None:
            return self._shape
        self._shape = name
        self._emit("r")

    def shapesize(self, *args, **kwargs): pass
    turtlesize = shapesize

    # ---- asking where the turtle is
    def position(self): return Vec2D(self._x, self._y)
    pos = position
    def xcor(self): return self._x
    def ycor(self): return self._y
    def heading(self): return self._h

    def distance(self, x, y=None):
        if y is None:
            x, y = x
        return _m.hypot(x - self._x, y - self._y)

    def towards(self, x, y=None):
        if y is None:
            x, y = x
        return _m.degrees(_m.atan2(y - self._y, x - self._x)) % 360

    def getscreen(self): return _screen

    onclick = onrelease = ondrag = _unsupported


Pen = RawTurtle = Turtle


class _Screen:
    _bg = "white"

    def bgcolor(self, *args):
        if not args:
            return self._bg
        self._bg = _col(args)
        _record({"k": "bg", "col": self._bg})

    def setup(self, width=None, height=None, startx=None, starty=None):
        if isinstance(width, (int, float)) and isinstance(height, (int, float)) and width > 1 and height > 1:
            _record({"k": "size", "w": width, "h": height})

    def screensize(self, canvwidth=None, canvheight=None, bg=None):
        self.setup(canvwidth, canvheight)
        if bg is not None:
            self.bgcolor(bg)

    def tracer(self, n=None, delay=None):
        if n is None:
            return 0 if _instant[0] else 1
        _instant[0] = (n == 0)

    def colormode(self, cmode=None):
        if cmode is None:
            return _colormode[0]
        _colormode[0] = 255 if cmode == 255 else 1.0

    def clear(self):
        _record({"k": "clearall"})
    reset = clearscreen = resetscreen = clear

    def turtles(self): return list(_turtles)
    def window_width(self): return 800
    def window_height(self): return 600
    def title(self, *a): pass
    def update(self): pass
    def delay(self, *a): pass
    def listen(self, *a): pass
    def mainloop(self): pass
    done = exitonclick = bye = mainloop
    onkey = onkeypress = onkeyrelease = onclick = onscreenclick = ontimer = _unsupported


_screen = _Screen()


def Screen():
    return _screen


def _default():
    if _pen[0] is None:
        _pen[0] = Turtle()
    return _pen[0]


def _wrap(target, name):
    def f(*args, **kwargs):
        return getattr(target() if callable(target) else target, name)(*args, **kwargs)
    f.__name__ = name
    return f


_TURTLE_FUNCS = [n for n in dir(Turtle) if not n.startswith("_") and callable(getattr(Turtle, n)) and n not in ("onclick", "getscreen")]
for _n in _TURTLE_FUNCS:
    globals()[_n] = _wrap(_default, _n)
    __all__.append(_n)
for _n in ["bgcolor", "title", "setup", "screensize", "tracer", "update", "delay", "colormode", "listen",
           "mainloop", "done", "exitonclick", "bye", "onkey", "onkeypress", "onkeyrelease", "onscreenclick",
           "ontimer", "window_width", "window_height", "turtles"]:
    globals()[_n] = _wrap(_screen, _n)
onclick = _unsupported
del _n
