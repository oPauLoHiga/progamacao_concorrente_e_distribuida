import pandas as pd

df = pd.read_csv('Painel_26.csv')

def soma_distm4_a():
    global df
    return df["distm4_a"].sum()

Total = soma_distm4_a()
print("soma de distm4_a", Total)