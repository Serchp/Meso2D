from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

INCLUDE_DIRS = [
    ROOT,
    ROOT / "src",
    ROOT / "tests",
    ROOT / "obsoletos",
]

EXCLUDE_PARTS = {".git", ".venv", ".idea", ".vscode", "__pycache__", ".agents"}

REPLACEMENTS = [
    ("poros", "pores"),
    ("poro", "pore"),
    ("aridos", "aggregates"),
    ("arido", "aggregate"),
    ("gruesos", "coarse"),
    ("grueso", "coarse"),
    ("finos", "fine"),
    ("fino", "fine"),
    ("puntos", "points"),
    ("punto", "point"),
    ("reactivos", "reactive"),
    ("reactivo", "reactive"),
    ("semilla", "seed"),
    ("estructura", "structure"),
    ("imagen", "image"),
    ("progreso", "progress"),
    ("guardar", "save"),
    ("cargar", "load"),
    ("abrir", "open"),
    ("cerrar", "close"),
    ("ejecutar", "run"),
    ("inicio", "start"),
    ("nuevo", "new"),
    ("anyadir", "add"),
    ("eliminar", "remove"),
    ("actualizar", "update"),
    ("mostrar", "show"),
    ("informar", "log"),
    ("simular", "simulate"),
    ("datos", "data"),
    ("lista", "list"),
    ("proyecto", "project"),
    ("dosificacion", "gradation"),
    ("ejemplo", "example"),
    ("visor", "viewer"),
    ("modo", "mode"),
    ("acerca", "about"),
    ("salir", "exit"),
]


def match_case(src: str, dst: str) -> str:
    if src.isupper():
        return dst.upper()
    if len(src) > 1 and src[0].isupper() and src[1:].islower():
        return dst.capitalize()
    return dst


patterns = [
    (re.compile(rf"(?<![A-Za-z0-9]){re.escape(src)}(?![A-Za-z0-9])", re.IGNORECASE), dst)
    for src, dst in REPLACEMENTS
]

seen = set()
created = 0
for base in INCLUDE_DIRS:
    if not base.exists():
        continue
    for src in base.rglob("*.py"):
        if src in seen:
            continue
        seen.add(src)
        if src.stem.endswith("_EN"):
            continue
        if any(part in EXCLUDE_PARTS for part in src.parts):
            continue

        text = src.read_text(encoding="utf-8", errors="ignore")
        for pattern, dst in patterns:
            text = pattern.sub(lambda m: match_case(m.group(0), dst), text)

        if text and not text.endswith("\n"):
            text += "\n"

        dst_path = src.with_name(src.stem + "_EN" + src.suffix)
        dst_path.write_text(text, encoding="utf-8")
        created += 1

print(f"Created/updated {created} *_EN files")
