#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fill_metadata_excel.py
Escanea ../hcs_clips (no recursivo), toma nombres .mp4 con formato:
  participante_gesto_lentes_angulo_fechaYHora.mp4
y llena/actualiza clips-metadata.xlsx con columnas:
  video, angulo, lentes, gesto, inicio, peak, fin

- Orden alfabético por nombre de archivo.
- Si el Excel ya existe, preserva 'inicio', 'peak' y 'fin' para videos coincidentes.
- Solo guarda el NOMBRE del archivo (no la ruta).

Requisitos: pandas, openpyxl
Uso:
  python fill_metadata_excel.py
Opcional:
  python fill_metadata_excel.py --dir ../hcs_clips --excel clips-metadata.xlsx
"""

import argparse
from pathlib import Path
import pandas as pd

EXPECTED_COLUMNS = ["video", "angulo", "lentes", "gesto", "inicio", "peak", "fin"]

def scan_mp4s(clips_dir: Path):
    if not clips_dir.exists():
        raise FileNotFoundError(f"No existe el directorio: {clips_dir}")
    files = [p for p in clips_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"]
    files.sort(key=lambda p: p.name.lower())
    return files

def parse_by_split(filename: str):
    """
    Espera: participante_gesto_lentes_angulo_fechaYHora.mp4
    Devuelve dict con gesto/lentes/angulo (en minúscula), o None si falla.
    """
    stem = Path(filename).stem  # sin .mp4
    parts = stem.split("_", 4)  # máximo 5 partes
    if len(parts) != 5:
        return None
    _, gesto, lentes, angulo, _ = parts
    return {
        "gesto": gesto,
        "lentes": lentes.lower(),
        "angulo": angulo.lower(),
    }

def load_or_init_excel(path: Path):
    if not path.exists():
        # Crear DF vacío con cabeceras
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    df = pd.read_excel(path, engine="openpyxl")
    # Asegurar columnas esperadas
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[EXPECTED_COLUMNS].copy()

def merge_preserving_times(new_df: pd.DataFrame, old_df: pd.DataFrame) -> pd.DataFrame:
    if old_df.empty:
        return new_df
    merged = new_df.merge(
        old_df[["video", "inicio", "peak", "fin"]],
        on="video",
        how="left",
        suffixes=("", "_old"),
    )
    # Conservar tiempos previos si no están vacíos
    for col in ["inicio", "peak", "fin"]:
        prev = merged[f"{col}_old"]
        keep_prev = prev.notna() & (prev.astype(str).str.strip() != "")
        merged[col] = prev.where(keep_prev, merged[col])
        merged.drop(columns=[f"{col}_old"], inplace=True)

    return merged.fillna("")[EXPECTED_COLUMNS]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="../hcs_clips", help="Directorio con .mp4 (no recursivo)")
    parser.add_argument("--excel", default="clips-metadata.xlsx", help="Excel a llenar/actualizar")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    clips_dir = (base / args.dir).resolve()
    excel_path = (base / args.excel).resolve()

    files = scan_mp4s(clips_dir)

    rows = []
    for p in files:
        meta = parse_by_split(p.name)
        if meta is None:
            print(f"[AVISO] Nombre fuera de formato (omitido): {p.name}")
            continue
        rows.append({
            "video": p.name,               # solo nombre de archivo
            "angulo": meta["angulo"],      # 'laptop' | 'ojos' (según nombre)
            "lentes": meta["lentes"],      # 'si' | 'no' (según nombre)
            "gesto": meta["gesto"],
            "inicio": "",
            "peak": "",
            "fin": "",
        })

    new_df = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
    old_df = load_or_init_excel(excel_path)
    final_df = merge_preserving_times(new_df, old_df)

    final_df.to_excel(excel_path, index=False, engine="openpyxl")
    print(f"[OK] Excel actualizado: {excel_path} | Filas: {len(final_df)}")

if __name__ == "__main__":
    main()
