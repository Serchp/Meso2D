import json
from pathlib import Path
from typing import Dict, Any

SUPPORTED_LANGUAGES = ("es", "en")

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "window.main.title": "Meso2D",
        "menu.file": "File",
        "menu.help": "Help",
        "menu.language": "Language",
        "selector.window.title": "Meso 2D",
        "selector.choose_morphology": "Choose the aggregate morphology",
        "selector.mode.circles": "Circles",
        "selector.mode.ellipses": "Ellipses",
        "selector.mode.polygons": "Polygons",
        "action.new_project": "New Project",
        "action.open_project": "Open Project",
        "action.save_project": "Save Project",
        "action.generate_report": "Generate Report",
        "action.exit": "Exit",
        "action.save_structure": "Save Structure",
        "action.tutorial": "Tutorial",
        "action.about": "About",
        "action.save_image": "Save Image",
        "action.load_example": "Load Example",
        "action.language.english": "English",
        "action.language.spanish": "Spanish",
        "button.run": "Run",
        "button.stop": "Stop",
        "button.view_structure": "View structure",
        "button.add": "Add",
        "button.remove": "Remove",
        "label.seed": "Seed",
        "label.specimen_dimensions": "Specimen dimensions",
        "label.axis_x": "X",
        "label.axis_y": "Y",
        "label.coef_f": "Coef F",
        "label.coef_a": "Coef A",
        "label.coef_b": "Coef B",
        "label.pores": "Pores",
        "label.reactive_points": "Reactive points",
        "label.in_aggregates": "In aggregates",
        "label.in_paste": "In paste",
        "label.dmin": "Dmin",
        "label.dmax": "Dmax",
        "label.percent": "%",
        "label.gradation": "Gradation",
        "table.sieve_size": "sieve_size",
        "table.tpp": "tpp",
        "app.title.about": "About Meso2D",
        "app.about.body": "Meso2D 1.0\n\nBy Servando Chinchon Paya, 2022\n\nPlease feel free to share any suggestions\n\nservando@ietcc.csic.es\n\nThank you!",
        "dialog.confirmation": "Confirmation",
        "dialog.exit.confirm": "Are you sure you want to exit?",
        "dialog.project.open.confirm": "Do you want to clear the current project and open another one?",
        "dialog.project.new.confirm": "Do you want to clear the current project and start a new one?",
        "dialog.structure.clear.confirm": "Do you want to clear the previous structure?",
        "dialog.error": "Error",
        "dialog.undefined_mode": "Undefined Mode",
        "dialog.tutorial.not_found.title": "Tutorial Not Found",
        "dialog.tutorial.not_found.body": "Could not find the tutorial PDF in the docs folder.",
        "dialog.open_error.title": "Open Error",
        "dialog.open_error.body": "Could not open tutorial file: {path}",
        "dialog.example_not_found.title": "Example Not Found",
        "dialog.example_not_found.body": "Could not find an example project file.",
        "dialog.export.mode_required": "You must select a mode before exporting.",
        "dialog.export.failed": "Could not export structure: {error}",
        "dialog.main_open_failed": "Could not open selected mode window: {error}",
        "filedialog.open_project": "Open Project",
        "filedialog.save_project": "Save Project",
        "filedialog.export_structure": "Export Structure",
        "filedialog.save_image": "Save Image",
        "viewer.window.title": "Structure Viewer",
        "viewer.action.save": "Save",
        "viewer.action.close": "Close",
        "log.language.changed": "Language changed to: {language}",
        "log.project.loaded": "---PROJECT LOADED---",
        "log.project.new": "---NEW PROJECT---",
        "log.example.loaded": "---EXAMPLE LOADED---",
        "log.project.saved": "---PROJECT SAVED---",
        "log.simulation.started": "---SIMULATION STARTED---",
        "log.simulation.finished": "---SIMULATION FINISHED---",
        "log.simulation.missing_data": "---ERROR: missing required data to start the simulation",
        "log.simulation.seed": "Seed value: {seed}",
        "log.simulation.time": "* Simulation time: {seconds} seconds",
        "log.structure.exported": "---STRUCTURE EXPORTED---",
        "log.image.saved": "---IMAGE SAVED---",
    },
    "es": {
        "window.main.title": "Meso2D",
        "menu.file": "Archivo",
        "menu.help": "Ayuda",
        "menu.language": "Idioma",
        "selector.window.title": "Meso 2D",
        "selector.choose_morphology": "Elige la morfologia de los aridos",
        "selector.mode.circles": "Circulos",
        "selector.mode.ellipses": "Elipses",
        "selector.mode.polygons": "Poligonos",
        "action.new_project": "Nuevo proyecto",
        "action.open_project": "Abrir proyecto",
        "action.save_project": "Guardar proyecto",
        "action.generate_report": "Generar informe",
        "action.exit": "Salir",
        "action.save_structure": "Guardar estructura",
        "action.tutorial": "Tutorial",
        "action.about": "Acerca de",
        "action.save_image": "Guardar imagen",
        "action.load_example": "Cargar ejemplo",
        "action.language.english": "Ingles",
        "action.language.spanish": "Espanol",
        "button.run": "Ejecutar",
        "button.stop": "Detener",
        "button.view_structure": "Ver estructura",
        "button.add": "Anadir",
        "button.remove": "Eliminar",
        "label.seed": "Semilla",
        "label.specimen_dimensions": "Dimensiones de probeta",
        "label.axis_x": "X",
        "label.axis_y": "Y",
        "label.coef_f": "Coef F",
        "label.coef_a": "Coef A",
        "label.coef_b": "Coef B",
        "label.pores": "Poros",
        "label.reactive_points": "Puntos reactivos",
        "label.in_aggregates": "En aridos",
        "label.in_paste": "En pasta",
        "label.dmin": "Dmin",
        "label.dmax": "Dmax",
        "label.percent": "%",
        "label.gradation": "Dosificacion",
        "table.sieve_size": "tamiz",
        "table.tpp": "ppt",
        "app.title.about": "Acerca de Meso2D",
        "app.about.body": "Meso2D 1.0\n\nPor Servando Chinchon Paya, 2022\n\nComparte cualquier sugerencia\n\nservando@ietcc.csic.es\n\nGracias!",
        "dialog.confirmation": "Confirmacion",
        "dialog.exit.confirm": "Estas seguro de que quieres salir?",
        "dialog.project.open.confirm": "Quieres limpiar el proyecto actual y abrir otro?",
        "dialog.project.new.confirm": "Quieres limpiar el proyecto actual y empezar uno nuevo?",
        "dialog.structure.clear.confirm": "Quieres limpiar la estructura anterior?",
        "dialog.error": "Error",
        "dialog.undefined_mode": "Modo no definido",
        "dialog.tutorial.not_found.title": "Tutorial no encontrado",
        "dialog.tutorial.not_found.body": "No se encontro el PDF del tutorial en la carpeta docs.",
        "dialog.open_error.title": "Error al abrir",
        "dialog.open_error.body": "No se pudo abrir el archivo de tutorial: {path}",
        "dialog.example_not_found.title": "Ejemplo no encontrado",
        "dialog.example_not_found.body": "No se pudo encontrar un archivo de proyecto de ejemplo.",
        "dialog.export.mode_required": "Debes seleccionar un modo antes de exportar.",
        "dialog.export.failed": "No se pudo exportar la estructura: {error}",
        "dialog.main_open_failed": "No se pudo abrir la ventana del modo seleccionado: {error}",
        "filedialog.open_project": "Abrir proyecto",
        "filedialog.save_project": "Guardar proyecto",
        "filedialog.export_structure": "Exportar estructura",
        "filedialog.save_image": "Guardar imagen",
        "viewer.window.title": "Visor de estructura",
        "viewer.action.save": "Guardar",
        "viewer.action.close": "Cerrar",
        "log.language.changed": "Idioma cambiado a: {language}",
        "log.project.loaded": "---PROYECTO CARGADO---",
        "log.project.new": "---NUEVO PROYECTO---",
        "log.example.loaded": "---EJEMPLO CARGADO---",
        "log.project.saved": "---PROYECTO GUARDADO---",
        "log.simulation.started": "---SIMULACION INICIADA---",
        "log.simulation.finished": "---SIMULACION FINALIZADA---",
        "log.simulation.missing_data": "---ERROR: faltan datos necesarios para iniciar la simulacion",
        "log.simulation.seed": "Valor de semilla: {seed}",
        "log.simulation.time": "* Tiempo de simulacion: {seconds} segundos",
        "log.structure.exported": "---ESTRUCTURA EXPORTADA---",
        "log.image.saved": "---IMAGEN GUARDADA---",
    },
}


def _config_path() -> Path:
    return Path.home() / ".meso2d" / "settings.json"


def _normalize_language(lang: str) -> str:
    if not lang:
        return "en"
    low = lang.lower()
    if low.startswith("es"):
        return "es"
    if low.startswith("en"):
        return "en"
    return "en"


def _load_settings() -> Dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_settings(data: Dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=True, indent=2)


def get_language() -> str:
    settings = _load_settings()
    configured = settings.get("language")
    if configured:
        return _normalize_language(configured)
    # Project requirement: default language must be English.
    return "en"


def set_language(language: str) -> str:
    normalized = _normalize_language(language)
    settings = _load_settings()
    settings["language"] = normalized
    _save_settings(settings)
    return normalized


class I18N:
    def __init__(self, language: str = ""):
        self.language = _normalize_language(language) if language else get_language()

    def tr(self, key: str, **kwargs: Any) -> str:
        table = _TRANSLATIONS.get(self.language, _TRANSLATIONS["en"])
        template = table.get(key, _TRANSLATIONS["en"].get(key, key))
        try:
            return template.format(**kwargs)
        except Exception:
            return template
