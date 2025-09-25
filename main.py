# main.py
# Python 3.12.0
# Grabador de clips para dataset de gestos (macOS)
# - Directorio de salida HARDCODEADO
# - No permite cambiar gesto/lentes/ángulo durante la grabación
# - Teclas:
#     1..5 = gesto
#     s/n  = lentes / sinLentes
#     l/o  = laptop / ojos
#     i    = iniciar grabación
#     f    = finalizar grabación
#     e    = salir

import os
import sys
import cv2
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("./hcs_clips")
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

GESTOS = {
    ord('1'): "guiñoDerecho",
    ord('2'): "guiñoIzquierdo",
    ord('3'): "cejasLevantadas",
    ord('4'): "ceñoFruncido",
    ord('5'): "comisurasLabialesExtendidas",
    ord('6'): "neutro"
}
LENTES = {
    ord('s'): "lentes",
    ord('S'): "lentes",
    ord('n'): "sinLentes",
    ord('N'): "sinLentes",
}
ANGULOS = {
    ord('l'): "laptop",
    ord('L'): "laptop",
    ord('o'): "ojos",
    ord('O'): "ojos",
}

def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def fourcc_mp4():
    """
    Devuelve el fourcc adecuado para .mp4 según el SO.
    - macOS: mp4v
    - Windows: avc1 (o mp4v si tu reproductor lo soporta)
    """
    import platform
    if platform.system() == "Windows":
        return cv2.VideoWriter_fourcc(*'avc1')
    else:
        return cv2.VideoWriter_fourcc(*'mp4v')

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def draw_hud(frame, sujeto, gesto, lentes, angulo, recording, can_change):
    overlay = frame.copy()
    hud_h = 110
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], hud_h), (0, 0, 0), -1)
    alpha = 0.45
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    x, y = 12, 24
    cv2.putText(frame, f"Sujeto: {sujeto}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
    y += 22
    cv2.putText(frame, f"Gesto: {gesto} | Lentes: {lentes} | Angulo: {angulo}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
    y += 22
    cambios_txt = "Puedes cambiar etiquetas (1..6, s/n, l/o)" if can_change else "GRABANDO: no puedes cambiar etiquetas"
    cv2.putText(frame, cambios_txt, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1, cv2.LINE_AA)

    if recording:
        rec_text = "REC"
        (tw, th), _ = cv2.getTextSize(rec_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        padding = 10
        px = frame.shape[1] - tw - 2*padding - 24
        py = 12

        cv2.circle(frame, (px + tw + padding + 10, py + th//2), 7, (0,0,255), -1)
        cv2.putText(frame, rec_text, (px, py + th), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2, cv2.LINE_AA)

def build_filename(sujeto, gesto, lentes, angulo) -> str:
    ts = timestamp()
    base = f"{sujeto}_{gesto}_{lentes}_{angulo}_{ts}.mp4"

    return base.replace(" ", "_")

def open_camera(index: int):
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    return cap

def create_writer(out_path: Path, frame_width: int, frame_height: int, fps: int):
    return cv2.VideoWriter(str(out_path), fourcc_mp4(), fps, (frame_width, frame_height))

def main():
    sujeto = input("Ingresa el nombre del sujeto: ").strip()
    if not sujeto:
        print("Nombre del sujeto vacío. Saliendo.")
        sys.exit(1)

    ensure_output_dir(OUTPUT_DIR)
    print(f"Los clips se guardarán en: {OUTPUT_DIR}")

    current_gesto = "guiñoDerecho"
    current_lentes = "sinLentes"
    current_angulo = "laptop"

    cap = open_camera(CAMERA_INDEX)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        sys.exit(2)

    window_name = "HCS Grabador de Clips (e=salir, i=iniciar, f=finalizar)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    recording = False
    writer = None
    frozen_gesto = frozen_lentes = frozen_angulo = None
    show_hud = True

    print("\nControles:")
    print("  1..5  -> gesto | 1: guiñoDerecho, 2: guiñoIzquierdo, 3: cejasLevantadas, 4: ceñoFruncido, 5: comisurasLabialesExtendidas, 6: neutro")
    print("  s/n   -> lentes/sinLentes")
    print("  l/o   -> laptop/ojos")
    print("  i     -> iniciar grabación")
    print("  f     -> finalizar grabación")
    print("  e     -> salir\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Frame no disponible desde la cámara. Saliendo.")
                break

            if show_hud:
                draw_hud(frame, sujeto, current_gesto, current_lentes, current_angulo, recording, can_change=not recording)

            if recording and writer is not None:
                writer.write(frame)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 255:
                continue

            if key in (ord('e'), ord('E')):
                if recording and writer is not None:
                    writer.release()
                break

            if not recording:
                if key in GESTOS:
                    current_gesto = GESTOS[key]
                elif key in LENTES:
                    current_lentes = LENTES[key]
                elif key in ANGULOS:
                    current_angulo = ANGULOS[key]

                if key in (ord('i'), ord('I')):
                    show_hud = False
                    frozen_gesto = current_gesto
                    frozen_lentes = current_lentes
                    frozen_angulo = current_angulo

                    filename = build_filename(sujeto, frozen_gesto, frozen_lentes, frozen_angulo)
                    out_path = OUTPUT_DIR / filename

                    writer = create_writer(out_path, FRAME_WIDTH, FRAME_HEIGHT, FPS)
                    if not writer or not writer.isOpened():
                        print("No se pudo iniciar el escritor de video. Verifica codecs/permisos.")
                        writer = None
                        continue

                    recording = True
                    print(f"Inició grabación -> {out_path.name}")

            else:
                if key in (ord('f'), ord('F')):
                    show_hud = True
                    recording = False
                    if writer is not None:
                        writer.release()
                        writer = None
                    print("Finalizó grabación (archivo cerrado).")

    finally:
        cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
