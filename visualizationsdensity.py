#visualization of field measurements 
import pandas as pd
import matplotlib.pyplot as plt

#Daten Density Cutter
df = pd.read_excel("data/01-31-densitycutter.xlsx") 

snowdepth = df.iloc[:, 0].dropna().values
density1 = df.iloc[:, 1].dropna().values
density2 = df.iloc[:, 2].dropna().values
density3= df.iloc[:, 3].values
mean = df.iloc[:, 6].dropna().values

#Daten Density SLF 
dslf = pd.read_excel("data/01-31-densitySLF.xlsx") 

snowdepthslf = dslf.iloc[:, 0].dropna().values
meanslf = dslf.iloc[:, 1].dropna().values
densityslf1 = dslf.iloc[:, 2].dropna().values
densityslf2= dslf.iloc[:, 3].values
# todo noch mean bilden aus den gemessenen Werten ..aktuell händisch im Excel berechnet


# Plot erstellen
plt.figure(figsize=(8, 5))
plt.scatter(snowdepth, mean, color='blue')
plt.plot(snowdepth, mean, color='blue', label='Mittelwert der Dichte')
plt.scatter(snowdepthslf, meanslf, color='red')
plt.plot(snowdepthslf, meanslf, color='red', label='Mittelwert der Dichte SLF')
plt.xlabel("Schneehöhe (cm)")
plt.ylabel("Dichte Density Cutter (kg/m³)")
plt.title("Dichte über Schneehöhe")
plt.gca().invert_xaxis() 
plt.legend()
plt.grid()
plt.show()
