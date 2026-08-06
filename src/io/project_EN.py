import json


def build_project_payload(window):
    return {
        "sieve_size": window.sieve_size,
        "tpp": window.tpp,
        "x": window.x,
        "y": window.y,
        "Pagg": window.Pagg,
        "Pporos": window.Pporos,
        "dporo_min": window.dporo_min,
        "dporo_max": window.dporo_max,
        "r_react": window.r_react,
        "dpto_max_aggregates": window.dpto_max_aggregates,
        "dpto_min_aggregates": window.dpto_min_aggregates,
        "dpto_max_pasta": window.dpto_max_pasta,
        "dpto_min_pasta": window.dpto_min_pasta,
        "Ppto_react_aggregates": window.Ppto_react_aggregates,
        "Ppto_react_pasta": window.Ppto_react_pasta,
        "seed": window.seed,
    }


def save_project_to_file(path, payload):
    if "." not in path:
        path += ".txt"
    with open(path, "w", encoding="utf-8") as archivo:
        json.dump(payload, archivo)


def load_project_from_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def apply_project_payload(window, diccionario):
    project_fields = [
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
    for name in project_fields:
        if name in diccionario:
            setattr(window, str(name), diccionario[name])
        else:
            setattr(window, str(name), "")
