from Worker_clusters import WorkerTodos
from Worker_elipses import WorkerElipses
from Worker_poligonos import WorkerPoligonos


def create_worker(modo, params, todo_correcto, check_poros, check_puntos, check_puntos_aridos, check_puntos_pasta):
    if modo == 'circulos':
        return WorkerTodos(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    if modo == 'elipses':
        return WorkerElipses(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    if modo == 'poligonos':
        return WorkerPoligonos(
            params,
            todo_correcto=todo_correcto,
            check_poros=check_poros,
            check_puntos=check_puntos,
            check_puntos_aridos=check_puntos_aridos,
            check_puntos_pasta=check_puntos_pasta,
        )
    raise ValueError("Modo no definido")
