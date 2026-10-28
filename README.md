# TP1 - Panorámicas con homografías

Trabajo grupal de **I308 - Visión Artificial**, Universidad de San Andrés.
**Autores: García, González y Turkie.** Informe original fechado el 16 de septiembre de 2026.

Unión de tres fotografías superpuestas en una panorámica: detección SIFT, selección A-NMS,
matching con ratio de Lowe y cross-check, homografías mediante DLT/RANSAC y blending ponderado.

[Consigna](docs/consigna.pdf) · [Informe del equipo](docs/informe.pdf) ·
[Notebook liviano](tp1_pano_sin_salidas.ipynb) · [Notebook original con salidas](tp1_pano.ipynb)

![Panorámica del campus UdeSA generada con la implementación del equipo](resultados/udesa.jpg)

## Implementación

- **OpenCV:** SIFT, comparación de descriptores, warping y transformada de distancia.
- **Implementación del equipo con NumPy:** A-NMS, DLT, RANSAC, cálculo del lienzo y mezcla.
- **Imagen central como ancla:** las dos vistas laterales se proyectan a sus coordenadas.
- Tres conjuntos incluidos: `cuadro` y `udesa` provistos por la cátedra; `test`, fotos propias.

## Archivos

```text
docs/consigna.pdf                 Enunciado de la cátedra
docs/informe.pdf                  Informe original del equipo
docs/origen_archivos.json         Origen y SHA-256 de archivos recibidos
tp1_pano.ipynb                    Notebook original, conservando sus salidas
tp1_pano_sin_salidas.ipynb        Copia liviana de las mismas celdas para leer en GitHub
panorama.py                      Implementación original reutilizable
inputs/                          Nueve imágenes: tres por conjunto
referencias/cuadro_result.jpg    Resultado de referencia incluido con la consigna
scripts/generar_ejemplos.py       Ejecución de los tres conjuntos sin Jupyter
resultados/                      Panorámicas regeneradas y métricas
```

El notebook original pesa aproximadamente 34 MB por sus imágenes incrustadas. Si GitHub no
lo renderiza, usar la copia liviana o descargarlo. Ambas copias conservan las mismas celdas;
la liviana solo elimina outputs y contadores de ejecución.

## Ejecutar

Preparación con [uv](https://docs.astral.sh/uv/), desde la raíz del repositorio:

```bash
git clone https://github.com/TomaasGonzalezzz/i308-tp1-panoramicas.git
cd i308-tp1-panoramicas
uv venv --python 3.11.18 --seed
uv pip install -r requirements.txt
```

Regenerar panorámicas y métricas con el código original:

```bash
uv run --no-project python scripts/generar_ejemplos.py --dataset all
```

Se puede elegir `--dataset cuadro`, `udesa` o `test` y otro directorio con `--output`.
Para explorar el desarrollo paso a paso:

```bash
uv run --no-project jupyter lab
```

Abrir el notebook desde la raíz para que encuentre `inputs/` y `panorama.py`. La primera celda
original instala [i308-utils](https://github.com/udesa-vision/i308-utils), herramienta de
visualización de la cátedra, y requiere conexión a internet.

## Resultados regenerados

Ejecución de `panorama.py` con parámetros originales: factor 0,25; A-NMS 400; ratio 0,8;
RANSAC 2000 iteraciones y umbral 3 px. **RMSE de reproyección sobre inliers**, en píxeles de
las imágenes reducidas; no es error contra un panorama ground truth. Izq/der respecto del ancla.

| Conjunto | Tamaño final (ancho x alto) | Matches izq / der | Inliers izq / der | RMSE izq / der (px) |
|---|---|---|---|---|
| cuadro | 1542 x 1651 | 85 / 51 | 47 / 22 | 1.461 / 1.819 |
| udesa | 1394 x 825 | 106 / 46 | 97 / 30 | 0.731 / 0.849 |
| test | 3197 x 2309 | 92 / 50 | 38 / 14 | 0.726 / 0.582 |

[Cuadro](resultados/cuadro.jpg) · [UdeSA](resultados/udesa.jpg) · [Fotos propias](resultados/test.jpg)

La comprobación de publicación ejecutó los tres conjuntos mediante el script; no reejecutó
completo el notebook, que incluye una selección manual de correspondencias. Entorno:
Python 3.11.18, NumPy 2.4.6, OpenCV 5.0.0. Los valores originales y el análisis
académico se conservan en el informe y en el notebook con salidas.

## Créditos y procedencia

Resolución realizada en equipo por **García, González y Turkie**; publicación de Tomás González.
La consigna, las imágenes `cuadro`/`udesa` y la referencia de resultado corresponden al material
de I308 de UdeSA. Los ZIP originales se conservaron fuera del repo; se excluyeron únicamente
archivos de metadatos de macOS (`__MACOSX`, `.DS_Store` y `._*`).

`panorama.py`, el notebook original y los PDF se preservan sin cambios de contenido.
README, dependencias, script de ejecución y resultados regenerados se agregaron para facilitar
su consulta y reproducción. No se atribuye todo el trabajo a quien publicó el repositorio.
