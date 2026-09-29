from opensimplex import OpenSimplex
import numpy as np
import matplotlib.pyplot as plt

# Parámetros del dominio
ancho = 100
alto = 100
num_puntos_deseados = 1000
umbral_ruido = 0.3
escala = 0.1

# Inicializar el generador de ruido
ruido = OpenSimplex(seed=42)

# Generar puntos aceptados según el valor del ruido
puntos = []
while len(puntos) < num_puntos_deseados:
    x = np.random.uniform(0, ancho)
    y = np.random.uniform(0, alto)
    valor = (ruido.noise2d(x * escala, y * escala) + 1) / 2  # Normalizar a [0, 1]
    if valor > umbral_ruido:
        puntos.append((x, y))

# Visualizar los puntos aceptados
x_vals, y_vals = zip(*puntos)
plt.figure(figsize=(6, 6))
plt.scatter(x_vals, y_vals, s=10, color='blue')
plt.title("Distribución de puntos con ruido Simplex")
plt.xlabel("X")
plt.ylabel("Y")
plt.grid(True)
plt.axis("equal")
plt.tight_layout()
plt.show()
