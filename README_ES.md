<p align="center">
  <img src="docs/images/circles.png" alt="Mesoestructura 2D generada por Meso2D con áridos circulares" width="760">
</p>

<h1 align="center">Meso2D</h1>

<p align="center">
  Genera, explora y exporta mesoestructuras bidimensionales de materiales cementicios.
  <br>
  Tres morfologías de árido. Parámetros reproducibles. Geometría lista para otras herramientas.
</p>

<p align="center">
  <a href="#instalacion">Instalación</a> ·
  <a href="#prueba-rapida">Prueba rápida</a> ·
  <a href="#capturas">Capturas</a> ·
  <a href="#exportaciones">Exportaciones</a>
</p>

## Qué es Meso2D

Meso2D es una aplicación de escritorio en Python para construir y visualizar modelos mesoscópicos 2D. Permite elegir la forma de los áridos —círculos, elipses o polígonos—, definir la granulometría y las dimensiones de la probeta, y configurar poros y puntos reactivos en los áridos y la pasta.

La semilla aleatoria permite repetir una configuración. La estructura generada se puede guardar como imagen o exportar a formatos vectoriales y de geometría.

## Instalación

Necesitas Git y Python instalado. Clona el repositorio, crea un entorno virtual e instala las dependencias:

```bash
git clone https://github.com/Serchp/Meso_2D_enconstruccion.git
cd Meso_2D_enconstruccion
python -m venv .venv
```

Activa el entorno virtual:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Instala los paquetes y ejecuta la aplicación:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python Meso2d.py
```

## Prueba rápida

Con las dependencias ya instaladas, puedes obtener una primera estructura en unos 30 segundos:

1. Ejecuta `python Meso2d.py` y elige **Circles**, **Ellipses** o **Polygons**.
2. En **File > Open Project**, abre el ejemplo que corresponde al modo, por ejemplo `example_circles.txt`.
3. Para una prueba ligera, desmarca **Pores** y **Reactive points**.
4. Pulsa **Run** para generar y visualizar la estructura.

Los ejemplos incluyen una semilla y cargan sus opciones de poros y puntos automáticamente. Déjalas activadas para probar una estructura más completa; la duración depende del equipo y de las opciones elegidas. Los archivos `.txt` son configuraciones de proyecto con contenido JSON; no son exportaciones de geometría.

## Capturas

Vistas de salida generadas por Meso2D con la configuración de ejemplo y las opciones de poros y puntos desactivadas, para destacar la morfología de los áridos.

<table>
  <tr>
    <td align="center"><strong>Círculos</strong></td>
    <td align="center"><strong>Elipses</strong></td>
    <td align="center"><strong>Polígonos</strong></td>
  </tr>
  <tr>
    <td><img src="docs/images/circles.png" alt="Estructura generada con áridos circulares" width="280"></td>
    <td><img src="docs/images/ellipses.png" alt="Estructura generada con áridos elípticos" width="280"></td>
    <td><img src="docs/images/polygons.png" alt="Estructura generada con áridos poligonales" width="280"></td>
  </tr>
</table>

## Exportaciones

Tras generar una estructura, usa **File > Save Structure** y elige el formato:

- **DXF** (`.dxf`): entidades organizadas en capas para flujos de CAD.
- **Gmsh GEO** (`.geo`): geometría para abrir o mallar con Gmsh.
- **SVG** (`.svg`): dibujo vectorial escalable.
- **JSON** (`.json`): dominio, resumen y entidades de la estructura.

También puedes guardar la vista como imagen. La exportación JSON contiene la geometría generada; los archivos `.txt` de ejemplo contienen parámetros para cargar un proyecto.

## Documentación

- [Tutorial en español](docs/Meso2D_user_tutorial.pdf)
- [Tutorial en inglés](docs/Meso2D_user_tutorial_EN.pdf)
