#visualization of density field measurements 
import pandas as pd
import matplotlib.pyplot as plt

def load_csv(file_name): 
    df = pd.read_excel(file_name) 
    snowdepth = df["snowdepth"]
    #density1 = df.iloc[:, 1].dropna().values
    mean = df["mean"]
    return snowdepth, mean


def plot_density(snowdepth, mean, snowdepthslf, meanslf):
    # Plot erstellen
    plt.figure(figsize=(8, 5))
    plt.scatter(snowdepth, mean, color='blue')
    plt.plot(snowdepth, mean, color='blue', label='Density Cutter')
    plt.scatter(snowdepthslf, meanslf, color='red')
    plt.plot(snowdepthslf, meanslf, color='red', label='Density SLF')
    plt.xlabel("Snowdepth (cm)")
    plt.ylabel("Density (kg/m^3)")
    plt.title("Density over snowdepth")
    plt.legend()
    plt.grid()
    plt.show()


#Daten Density Cutter
snowdepth, mean = load_csv("data/01-31-densitycutter.xlsx") 

#Daten Density SLF 
snowdepthslf, meanslf = load_csv("data/01-31-densitySLF.xlsx") 

#Daten visualisieren
plot_density(snowdepth, mean, snowdepthslf, meanslf)