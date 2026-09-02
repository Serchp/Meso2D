import json
from typing import Any, Dict

_CANONICAL_FIELDS = [
    "sieve_size",
    "tpp",
    "x",
    "y",
    "Pagg",
    "Pporos",
    "dporo_min",
    "dporo_max",
    "r_react",
    "dpto_max_aggregates",
    "dpto_min_aggregates",
    "dpto_max_pasta",
    "dpto_min_pasta",
    "Ppto_react_aggregates",
    "Ppto_react_pasta",
    "seed",
]

_ES_TO_CANONICAL = {
    "dpto_max_aridos": "dpto_max_aggregates",
    "dpto_min_aridos": "dpto_min_aggregates",
    "Ppto_react_aridos": "Ppto_react_aggregates",
}


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload)
    for old_key, new_key in _ES_TO_CANONICAL.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized[old_key]
    return normalized


def build_project_payload(window: Any) -> Dict[str, Any]:
    payload = {
        "sieve_size": getattr(window, "sieve_size", None),
        "tpp": getattr(window, "tpp", None),
        "x": getattr(window, "x", None),
        "y": getattr(window, "y", None),
        "Pagg": getattr(window, "Pagg", None),
        "Pporos": getattr(window, "Pporos", None),
        "dporo_min": getattr(window, "dporo_min", None),
        "dporo_max": getattr(window, "dporo_max", None),
        "r_react": getattr(window, "r_react", None),
        "dpto_max_aggregates": getattr(window, "dpto_max_aggregates", getattr(window, "dpto_max_aridos", None)),
        "dpto_min_aggregates": getattr(window, "dpto_min_aggregates", getattr(window, "dpto_min_aridos", None)),
        "dpto_max_pasta": getattr(window, "dpto_max_pasta", None),
        "dpto_min_pasta": getattr(window, "dpto_min_pasta", None),
        "Ppto_react_aggregates": getattr(window, "Ppto_react_aggregates", getattr(window, "Ppto_react_aridos", None)),
        "Ppto_react_pasta": getattr(window, "Ppto_react_pasta", None),
        "seed": getattr(window, "seed", None),
    }
    return payload


def save_project_to_file(path: str, payload: Dict[str, Any]) -> None:
    if "." not in path:
        path += ".txt"
    with open(path, "w", encoding="utf-8") as archivo:
        json.dump(payload, archivo)


def load_project_from_file(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return _normalize_payload(data)


def apply_project_payload(window: Any, payload: Dict[str, Any]) -> None:
    normalized = _normalize_payload(payload)
    for field in _CANONICAL_FIELDS:
        setattr(window, field, normalized.get(field, None))

    # Keep legacy Spanish names synchronized for old code paths.
    window.dpto_max_aridos = getattr(window, "dpto_max_aggregates", None)
    window.dpto_min_aridos = getattr(window, "dpto_min_aggregates", None)
    window.Ppto_react_aridos = getattr(window, "Ppto_react_aggregates", None)
