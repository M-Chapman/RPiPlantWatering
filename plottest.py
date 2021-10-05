import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("csvfiles/pin0.csv")
df = pd.DataFrame(df, columns=['Time', 'Moisture'])

print(len(df))

df.plot(x='Time', y='Moisture', kind='line')

plt.show()
