from .Worker_clusters_EN import WorkerTodos
from .Worker_ellipses_EN import WorkerElipses
from .Worker_poligonos_EN import WorkerPoligonos

# EN aliases kept for new codepaths; ES names kept for legacy imports.
WorkerEllipses = WorkerElipses
WorkerPolygons = WorkerPoligonos

__all__ = [
	"WorkerTodos",
	"WorkerElipses",
	"WorkerPoligonos",
	"WorkerEllipses",
	"WorkerPolygons",
]
