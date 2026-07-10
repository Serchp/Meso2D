import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from opensimplex import OpenSimplex

# Parámetros comunes
n_points = 1000
domain_size = (100, 100)
np.random.seed(42)

# 1. Distribución homogénea aleatoria
x_uniform = np.random.uniform(0, domain_size[0], n_points)
y_uniform = np.random.uniform(0, domain_size[1], n_points)

# 2. Agrupamientos por clusters
n_clusters = 5
cluster_centers = np.random.uniform(20, 80, (n_clusters, 2))
cluster_std = 5
x_clusters = []
y_clusters = []
for cx, cy in cluster_centers:
    x_clusters.extend(np.random.normal(cx, cluster_std, n_points // n_clusters))
    y_clusters.extend(np.random.normal(cy, cluster_std, n_points // n_clusters))

# 3. Gaussian Mixture Model
gmm = GaussianMixture(n_components=4, covariance_type='full', random_state=42)
gmm.means_ = np.array([[30, 30], [70, 30], [30, 70], [70, 70]])
gmm.covariances_ = np.array([[[50, 0], [0, 50]]] * 4)
gmm.weights_ = np.array([0.25] * 4)
gmm.precisions_cholesky_ = np.linalg.cholesky(np.linalg.inv(gmm.covariances_))
samples_gmm, _ = gmm.sample(n_points)
x_gmm, y_gmm = samples_gmm[:, 0], samples_gmm[:, 1]

# 4. Ruido Simplex
noise = OpenSimplex(seed=42)
x_simplex = []
y_simplex = []
while len(x_simplex) < n_points:
    x = np.random.uniform(0, domain_size[0])
    y = np.random.uniform(0, domain_size[1])
    value = (noise.noise2(x * 0.05, y * 0.05) + 1) / 2
    if value > 0.3:
        x_simplex.append(x)
        y_simplex.append(y)

# Visualización
fig, axs = plt.subplots(1, 4, figsize=(20, 5))

axs[0].scatter(x_uniform, y_uniform, s=10, color='gray')
axs[0].set_title("Distribución Aleatoria")

axs[1].scatter(x_clusters, y_clusters, s=10, color='blue')
axs[1].set_title("Agrupamientos por Clusters")

axs[2].scatter(x_gmm, y_gmm, s=10, color='green')
axs[2].set_title("Gaussian Mixture Model (GMM)")

axs[3].scatter(x_simplex, y_simplex, s=10, color='purple')
axs[3].set_title("Distribución con Ruido Simplex")

for ax in axs:
    ax.set_xlim(0, domain_size[0])
    ax.set_ylim(0, domain_size[1])
    ax.set_aspect('equal')
    ax.grid(True)

plt.tight_layout()
plt.show()
