import numpy as np
import pandas as pd

df = pd.read_csv("csvfiles/pin0.csv")
df = pd.DataFrame(pd.read_csv("csvfiles/pin0.csv"))
df.plot.line()