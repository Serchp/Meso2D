# Scrpit para generar elipses

from matplotlib import pyplot as plt
from shapely.geometry.point import Point
from shapely import affinity
from matplotlib.patches import Polygon
import numpy as np

lista_elipses = []
cuenta_1 = 0


# def generar_elipse(centro, radio1, radio2, ángulo):
#     circ = Point(centro).buffer(1)
#     ell = affinity.scale(circ, radio1, radio2)
#     ellr = affinity.rotate(ell, ángulo)
#     return ellr


# función para chequear si la nueva elipse se toca con alguna de las existentes
def chequear_elipse(elipse, lista):
    contador = 0
    for n in lista:
        intersection = elipse.intersection(n)
        if intersection:
            contador += 1
        if contador > 0:
            return True


def plotear_elipses(lista):
    fig, ax = plt.subplots()
    ax.set_xlim([-5, 5])
    ax.set_ylim([-5, 5])
    ax.set_aspect('equal')
    for elipse in lista:
        vertices = np.array(elipse.exterior.coords.xy)
        patch = Polygon(vertices.T, color = 'blue', alpha = 0.5)
        ax.add_patch(patch)
        print(elipse)
    plt.show()


# elipse1 = generar_elipse((-1,0), 2, 3, 0)
# elipse2 = generar_elipse((2.5, 1), 2, 1, 0)
#
# lista_elipses.append(elipse1)
# # lista_elipses.append(elipse2)
#
# chequear_elipse(elipse2, lista_elipses)
# # print('la cuenta es ' + str(cuenta_1))
# if cuenta_1 > 0:
#     elipse2 = affinity.rotate(elipse2, 30)
#
# lista_elipses.append(elipse2)
#
# plotear_elipses(lista_elipses)


def elipse(centro, radio1, radio2, ángulo):
    circ = Point(centro).buffer(1)
    ell = affinity.scale(circ, radio1, radio2)
    ellr = affinity.rotate(ell, ángulo)
    cuenta_giros = 0
    while chequear_elipse(ellr, lista_elipses):
        ellr = affinity.rotate(ellr, 10)
        cuenta_giros += 1
        if cuenta_giros == 18:
            print('ha girado mucho')
            break

    if not chequear_elipse(ellr, lista_elipses):
        lista_elipses.append(ellr)

elipse1 = elipse((-1,0), 2, 3, 0)
elipse2 = elipse((2.5, 1), 2, 1, 0)
# elipse2 = elipse((5, 1), 2, 1, 0)
elipse3 = elipse((0,0), 1, 4, 0)

plotear_elipses(lista_elipses)
