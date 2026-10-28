"""Ejecuta la implementación original sobre los conjuntos incluidos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from panorama import generar_panoramica  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["all", "cuadro", "udesa", "test"], default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "resultados")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    datasets = ["cuadro", "udesa", "test"] if args.dataset == "all" else [args.dataset]
    metrics = {}
    for dataset in datasets:
        images = [cv2.imread(str(ROOT / "inputs" / f"{dataset}_{i}.jpg")) for i in range(3)]
        if any(image is None for image in images):
            parser.error(f"No se pudieron leer las tres imágenes del conjunto {dataset}")
        panorama, info = generar_panoramica(*images, info=True)
        output = args.output / f"{dataset}.jpg"
        if not cv2.imwrite(str(output), panorama):
            raise RuntimeError(f"No se pudo guardar {output}")
        metrics[dataset] = {
            key: value.tolist() if hasattr(value, "tolist") else value
            for key, value in info.items()
        }
        print(f"{dataset}: {output.name}, tamaño={info['tamaño']}, "
              f"RMSE izq={info['rmse_izq']:.3f} px, der={info['rmse_der']:.3f} px")
    (args.output / "metricas.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
