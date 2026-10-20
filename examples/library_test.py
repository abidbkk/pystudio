# PyStudio library check
# Press Run. Each line says OK or FAILED.
# numpy / pandas / matplotlib are downloaded the first time, so the first run can take ~20 seconds.

def check(name, test):
    try:
        result = test()
        print(f"OK      {name:<12} {result}")
    except Exception as e:
        print(f"FAILED  {name:<12} {type(e).__name__}: {e}")

print("--- Built-in modules ---")

import math
check("math", lambda: f"sqrt(16) = {math.sqrt(16)}, pi = {math.pi:.4f}")

import random
check("random", lambda: f"randint(1, 6) = {random.randint(1, 6)}, choice = {random.choice(['rock', 'paper', 'scissors'])}")

import statistics
check("statistics", lambda: f"mean = {statistics.mean([72, 88, 95, 60])}, median = {statistics.median([72, 88, 95, 60])}")

import datetime
check("datetime", lambda: f"today is {datetime.date.today():%A %d %B %Y}")

import time
def time_test():
    start = time.time()
    time.sleep(0.5)
    return f"slept {time.time() - start:.1f} s"
check("time", time_test)

import string
check("string", lambda: f"letters = {string.ascii_lowercase[:10]}...")

import collections
check("collections", lambda: f"Counter = {collections.Counter('mississippi').most_common(2)}")

import itertools
check("itertools", lambda: f"permutations = {list(itertools.permutations('abc', 2))[:3]}...")

import json
check("json", lambda: json.dumps({"name": "Sara", "score": 95}))

import re
check("re", lambda: f"numbers found = {re.findall(r'[0-9]+', 'I have 3 cats and 12 fish')}")

import csv, io
check("csv", lambda: f"rows = {list(csv.reader(io.StringIO('a,b\n1,2')))}")

import fractions, decimal
check("fractions", lambda: f"1/3 + 1/6 = {fractions.Fraction(1, 3) + fractions.Fraction(1, 6)}")
check("decimal", lambda: f"0.1 + 0.2 = {decimal.Decimal('0.1') + decimal.Decimal('0.2')}")

print()
print("--- Extra libraries ---")

import numpy as np
check("numpy", lambda: f"array * 2 = {np.array([1, 2, 3]) * 2}, mean = {np.mean([72, 88, 95, 60])}")

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)   # hides a long pandas notice
import pandas as pd
def pandas_test():
    df = pd.DataFrame({"name": ["Sara", "Omar", "Lina"], "score": [95, 72, 88]})
    best = df.loc[df["score"].idxmax(), "name"]
    return f"{len(df)} rows, average = {df['score'].mean():.1f}, best = {best}"
check("pandas", pandas_test)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def matplotlib_test():
    plt.plot([1, 2, 3], [1, 4, 9])
    plt.title("Squares")
    return "chart created (charts are not displayed in PyStudio yet)"
check("matplotlib", matplotlib_test)

print()
print("--- input() ---")
name = input("Type your name and press Enter: ")
print(f"OK      input        Hello, {name}!")
print()
print("All checks finished.")
