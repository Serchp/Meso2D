# -*- coding: utf-8 -*-
"""
Created on Wed Mar  2 15:02:53 2022

@author: 48560330Q
"""

import matplotlib.pyplot as plt
# import math
import numpy as np
import ezdxf


"""
Variables que declara el usuario
"""
sieve_size = [19.00, 12.70, 9.50, 4.75, 2.36]
#total_percentage_passing = tpp
tpp = [100, 97, 61, 10, 1.4]


x = 75
y = 75
z = 75
Pagg = 0.5
Pporos = 0.02
dporo_min = 2
dporo_max = 4
# r_react = 1
r_react = 0.05
Ppto_react = 0.002

""""
Variables necesarias
"""

np.random.seed(666)
A = x*z
Aagg = []
A_remanente = 0
num_particulas = 0
particulas = []
radios = []
lista_aridos = []
todos_aridos = []
radios_poros = []
todos_poros = []
lista_poros = []
lista_ptos_react = []
todos_ptos_react = []

aridos_puestos = False
poros_puestos = False


"""
función para calcular distancias euclideas de un elemento x1 con todos los pertenecientes a una lista (x2 en Y)
"""
 
def distancias(lista, coor_x, coor_y, radio):
    contador = 0
    for n in lista:
        dist = np.sqrt((coor_x - n[0])**2 + (coor_y - n[1])**2)
        if dist > radio + n[2]:
            contador +=1
        if contador == len(lista):
            return True


"""
calcular y colocar los poros
"""

A_poros = A*Pporos
print('el Aporo es ' + str(A_poros))

while A_poros > np.pi*(dporo_min/2)**2:
    rporo = (dporo_min + np.random.random()*(dporo_max-dporo_min))/2
    Aporo = np.pi*(rporo)**2
    A_poros = A_poros - Aporo
    radios_poros.append(rporo)

while len(radios_poros) > 0:
    r = radios_poros[0]
    loc_poro_x = np.random.uniform(0, x)
    loc_poro_z = np.random.uniform(0, z)
    dato_poro = [loc_poro_x, loc_poro_z, r]
    poro = plt.Circle((loc_poro_x, loc_poro_z), r, color='r')
    if aridos_puestos == False:
        if loc_poro_x + r < x and loc_poro_x - r > 0 and loc_poro_z + r < z and loc_poro_z - r > 0:
            if len(lista_poros) == 0:
                lista_poros.append(dato_poro)
                todos_poros.append(poro)
                radios_poros.remove(r)
            elif distancias(lista_poros, loc_poro_x, loc_poro_z, r):
                lista_poros.append(dato_poro)
                todos_poros.append(poro)
                radios_poros.remove(r)
    else:
        if loc_poro_x + r < x and loc_poro_x - r > 0 and loc_poro_z + r < z and loc_poro_z - r > 0:
            if distancias(lista_aridos, loc_poro_x, loc_poro_z, r):
                if len(lista_poros) == 0:
                    lista_poros.append(dato_poro)
                    todos_poros.append(poro)
                    radios_poros.remove(r)
                elif distancias(lista_poros, loc_poro_x, loc_poro_z, r):
                    lista_poros.append(dato_poro)
                    todos_poros.append(poro)
                    radios_poros.remove(r)
    poros_puestos = True

print(len(lista_poros))
print(A_poros)


"""
Step 1. Calculate the area of aggregate to be generated in the grading segment
"""

"""
Step 2. Generate a random number defining the size of an aggregate
particle. Assuming that the size d has a uniform distribution between ds 
and ds+1, it may be calculated using the following expression:
    
d = ds+1 + k(ds − ds+1),

where k is a random number uniformly distributed between 0 and 1
"""

"""
Step 3. Calculate the volume of the generated aggregate particle
and subtract it from the volume of aggregate within the grading segment
"""

"""
Step 4. Repeat steps 2 and 3 until the volume of aggregate
left to be generated is less than 4/3pi(ds+1/2)**3, i.e. not
enough for generating another particle. The remaining
volume of aggregate to be generated is then transferred
to the next grading segment.
"""

# A = A-A*Pporos
i = 0
while i+1 < len(sieve_size):
    area_intervalo = ((tpp[i]-tpp[i+1])/(tpp[0]-tpp[-1]))*Pagg*A
    Aagg.append(round(area_intervalo))
    i = i+1
print(Aagg)

j = 0
while j < len(Aagg):
    num_particulas = 0
    print(Aagg[j])
    area_c = 0
    Aagg[j] = Aagg[j] + A_remanente
    print(Aagg[j])
    while Aagg[j]-area_c > np.pi*(sieve_size[j+1]/2)**2:
        d = sieve_size[j+1] + np.random.rand()*(sieve_size[j]-sieve_size[j+1])
        area = np.pi*(d/2)**2
        if area + area_c < Aagg[j]:
            area_c = area_c + area
            radios.append(d/2)
            num_particulas = num_particulas+1
        A_remanente = Aagg[j]-area_c
    print(A_remanente)
    print(num_particulas)
    particulas.append(num_particulas)
    if j < len(Aagg):
        j += 1
print(j)
print(particulas)
# print(radios)
print(len(radios))



"""
función para colocar los áridos (algoritmo también usado para colocar los poros)
1: generar de forma aleatoria las coordenadas de posición. Generar el árido y
colocarlo
2: Chequear si la posición es buena:
    2a: todo el árido dentro de los límites
    2b: no se solapa con un árido ya puesto
    2c: cumple una distancia mínima
"""

while len(radios) > 0:
    i = radios[0]
    loc_x = np.random.uniform(0, x)
    loc_z = np.random.uniform(0, z)
    dato_arido = [loc_x, loc_z, i]
    arido = plt.Circle((loc_x, loc_z), i)
    if poros_puestos == False:
        if loc_x + i < x and loc_x - i > 0 and loc_z + i < z and loc_z - i > 0:
            if len(todos_aridos) == 0:
                lista_aridos.append(dato_arido)
                todos_aridos.append(arido)
                radios.remove(i)
            elif distancias(lista_aridos, loc_x, loc_z, i):
                lista_aridos.append(dato_arido)
                todos_aridos.append(arido)
                radios.remove(i)
    else:
        if loc_x + i < x and loc_x - i > 0 and loc_z + i < z and loc_z - i > 0:
            if distancias(lista_poros, loc_x, loc_z, i):
                if len(todos_aridos) == 0:
                    lista_aridos.append(dato_arido)
                    todos_aridos.append(arido)
                    radios.remove(i)
                elif distancias(lista_aridos, loc_x, loc_z, i):
                    lista_aridos.append(dato_arido)
                    todos_aridos.append(arido)
                    radios.remove(i)
    aridos_puestos = True
            
print(len(lista_aridos))
print(len(todos_aridos))
print(len(radios))



"""
Los puntos reactivos. Están tanto sobre áridos como sobre pasta (incluso poros)
"""

A_react = Ppto_react*A
N_react = round(A_react/(np.pi*(r_react)**2))
print('El número de puntos reactivos es ' + str(N_react))
cuenta_N_react = 0
while cuenta_N_react < N_react:
    loc_pto_x = np.random.uniform(0, x)
    loc_pto_z = np.random.uniform(0, z)
    dato_pto = [loc_pto_x, loc_pto_z, r_react]
    punto_react = plt.Circle((loc_pto_x, loc_pto_z), r_react, color='y')
    if poros_puestos == True:
        if loc_pto_x + r_react < x and loc_pto_x - r_react > 0 and loc_pto_z + r_react < z and loc_pto_z - r_react > 0:
            if distancias(lista_poros, loc_pto_x, loc_pto_z, r_react):
                if len(lista_ptos_react) == 0:
                    lista_ptos_react.append(dato_pto)
                    todos_ptos_react.append(punto_react)
                elif distancias(lista_ptos_react, loc_pto_x, loc_pto_z, r_react):
                    lista_ptos_react.append(dato_pto)
                    todos_ptos_react.append(punto_react)
    cuenta_N_react += 1
    

"""
Plotear áridos, poros y puntos reactivos
"""

figure, axes = plt.subplots(figsize=(4,4))
# axes.set_xlim(0, 150)
# axes.set_ylim(0, 300)
axes.set_xlim(0, 75)
axes.set_ylim(0, 75)

for i in todos_poros:
    axes.add_patch(i)

for i in todos_aridos:
    axes.add_patch(i)

for i in todos_ptos_react:
    axes.add_patch(i)

# crear el erctángulo de la probeta
probeta = plt.Rectangle((0, 0), x, z, color='black', fill=False)
axes.add_patch(probeta)
plt.title( 'áridos en la probeta' )
axes.autoscale_view()
plt.show()


# """
# Exportar distribución de áridos, poros y puntos reactivos en dxf
# """
#
# doc = ezdxf.new()
# doc.layers.new(name='Poros')
# doc.layers.new(name='Aridos')
# doc.layers.new(name='Ptos_reactivos')
# msp = doc.modelspace()
# for i in lista_poros:
#     msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer':'Poros'})
# for i in lista_aridos:
#     msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer':'Aridos'})
# for i in lista_ptos_react:
#     msp.add_circle([i[0], i[1]], i[2], dxfattribs={'layer':'Ptos_reactivos'})
#
# # doc.saveas('distribucionPoros.dxf')
# doc.saveas('distribucionPorosAridosPtos.dxf')

