import json
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import ezdxf


class StructureExportError(Exception):
    """Raised when structure export data is invalid or the format is unsupported."""


def export_structure_file(
    path: str,
    selected_filter: str,
    mode: str = "",
    list_pores: Sequence[Any] = (),
    list_aggregates_coarse: Sequence[Any] = (),
    list_aggregates_fine: Sequence[Any] = (),
    list_ptos_react: Sequence[Any] = (),
    domain: Optional[Dict[str, float]] = None,
    **kwargs: Any,
) -> str:
    """Export the structure to the format selected by extension/filter.

    Return the final written path (with normalized extension).
    """
    if not mode:
        mode = kwargs.get("modo", "")
    if not list_pores:
        list_pores = kwargs.get("lista_poros", list_pores)
    if not list_aggregates_coarse:
        list_aggregates_coarse = kwargs.get("lista_aridos_gruesos", list_aggregates_coarse)
    if not list_aggregates_fine:
        list_aggregates_fine = kwargs.get("lista_aridos_finos", list_aggregates_fine)
    if not list_ptos_react:
        list_ptos_react = kwargs.get("lista_ptos_react", list_ptos_react)
    if mode == "elipses":
        mode = "ellipses"

    format_name, final_path = _resolve_format_and_path(path, selected_filter)

    if format_name == "dxf":
        _export_dxf(final_path, mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react)
    elif format_name == "svg":
        _export_svg(final_path, mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react, domain)
    elif format_name == "json":
        _export_json(final_path, mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react, domain)
    elif format_name == "geo":
        _export_geo(final_path, mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react)
    else:
        raise StructureExportError(f"Unsupported format: {format_name}")

    return final_path


def _resolve_format_and_path(path: str, selected_filter: str) -> Tuple[str, str]:
    ext_map = {
        ".dxf": "dxf",
        ".svg": "svg",
        ".json": "json",
        ".geo": "geo",
    }

    lower_path = path.lower()
    for ext, fmt in ext_map.items():
        if lower_path.endswith(ext):
            return fmt, path

    filter_to_ext = {
        "dxf": ".dxf",
        "svg": ".svg",
        "json": ".json",
        "gmsh": ".geo",
        "geo": ".geo",
    }

    selected_filter_lower = (selected_filter or "").lower()
    for key, ext in filter_to_ext.items():
        if key in selected_filter_lower:
            return ext_map[ext], path + ext

    # Compatibility fallback: if filter is unknown, use DXF.
    return "dxf", path + ".dxf"


def _export_dxf(
    path: str,
    mode: str,
    list_pores: Sequence[Any],
    list_aggregates_coarse: Sequence[Any],
    list_aggregates_fine: Sequence[Any],
    list_ptos_react: Sequence[Any],
) -> None:
    doc = ezdxf.new()
    layer_names = ["Pores", "Aggregates coarse", "Aggregates fine", "Ptos_reactive"]
    for layer_name in layer_names:
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name)

    msp = doc.modelspace()

    for entity in _collect_entities(mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react):
        layer = entity["layer"]
        etype = entity["type"]
        if etype == "circle":
            msp.add_circle([entity["x"], entity["y"]], entity["r"], dxfattribs={"layer": layer})
        elif etype == "ellipse":
            pts = _ellipse_points(entity["x"], entity["y"], entity["a"], entity["b"], entity["angle_deg"], 72)
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        elif etype == "polygon":
            msp.add_lwpolyline(entity["points"], close=True, dxfattribs={"layer": layer})

    doc.saveas(path)


def _export_svg(
    path: str,
    mode: str,
    list_pores: Sequence[Any],
    list_aggregates_coarse: Sequence[Any],
    list_aggregates_fine: Sequence[Any],
    list_ptos_react: Sequence[Any],
    domain: Optional[Dict[str, float]],
) -> None:
    entities = _collect_entities(mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react)
    width, height = _svg_canvas_size(entities, domain)

    layer_style = {
        "Pores": "fill:#f28b82;fill-opacity:.7;stroke:#b3261e;stroke-width:.12;",
        "Aggregates coarse": "fill:#93c5fd;fill-opacity:.8;stroke:#1e3a8a;stroke-width:.12;",
        "Aggregates fine": "fill:#bae6fd;fill-opacity:.7;stroke:#0c4a6e;stroke-width:.1;",
        "Ptos_reactive": "fill:#fde047;fill-opacity:.95;stroke:#a16207;stroke-width:.1;",
    }
    layer_ids = {
        "Pores": "layer_Pores",
        "Aggregates coarse": "layer_Aggregates_coarse",
        "Aggregates fine": "layer_Aggregates_fine",
        "Ptos_reactive": "layer_Ptos_reactive",
    }
    layer_order = ["Pores", "Aggregates coarse", "Aggregates fine", "Ptos_reactive"]
    layer_entities: Dict[str, List[Dict[str, Any]]] = {layer: [] for layer in layer_order}

    lines: List[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.6g}mm" height="{height:.6g}mm" viewBox="0 0 {width:.6g} {height:.6g}">'
    )

    for entity in entities:
        layer_name = entity.get("layer")
        if layer_name in layer_entities:
            layer_entities[layer_name].append(entity)

    for layer_name in layer_order:
        lines.append(
            f'<g id="{layer_ids[layer_name]}" transform="translate(0 {height:.6g}) scale(1 -1)">'
        )
        style = layer_style[layer_name]
        for entity in layer_entities[layer_name]:
            if entity["type"] == "circle":
                lines.append(
                    f'<circle style="{style}" cx="{entity["x"]:.6g}" cy="{entity["y"]:.6g}" r="{entity["r"]:.6g}"/>'
                )
            elif entity["type"] == "ellipse":
                lines.append(
                    f'<ellipse style="{style}" cx="{entity["x"]:.6g}" cy="{entity["y"]:.6g}" '
                    f'rx="{entity["a"]:.6g}" ry="{entity["b"]:.6g}" '
                    f'transform="rotate({entity["angle_deg"]:.6g} {entity["x"]:.6g} {entity["y"]:.6g})"/>'
                )
            elif entity["type"] == "polygon":
                pts = " ".join(f"{x:.6g},{y:.6g}" for x, y in entity["points"])
                lines.append(f'<polygon style="{style}" points="{pts}"/>')
        lines.append("</g>")

    lines.append("</svg>")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _export_json(
    path: str,
    mode: str,
    list_pores: Sequence[Any],
    list_aggregates_coarse: Sequence[Any],
    list_aggregates_fine: Sequence[Any],
    list_ptos_react: Sequence[Any],
    domain: Optional[Dict[str, float]],
) -> None:
    entities = _collect_entities(mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react)
    summary = {
        "Pores": 0,
        "Aggregates coarse": 0,
        "Aggregates fine": 0,
        "Ptos_reactive": 0,
    }
    for entity in entities:
        layer = entity.get("layer")
        if layer in summary:
            summary[layer] += 1

    payload = {
        "version": 1,
        "mode": mode,
        "domain": domain or {},
        "summary": summary,
        "entities": entities,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _export_geo(
    path: str,
    mode: str,
    list_pores: Sequence[Any],
    list_aggregates_coarse: Sequence[Any],
    list_aggregates_fine: Sequence[Any],
    list_ptos_react: Sequence[Any],
) -> None:
    entities = _collect_entities(mode, list_pores, list_aggregates_coarse, list_aggregates_fine, list_ptos_react)
    loops = _entities_to_geo_loops(entities)
    lc = _estimate_geo_lc(entities)

    lines: List[str] = []
    lines.append("// .geo file generated by Meso2D")
    lines.append("SetFactory(\"OpenCASCADE\");")
    lines.append("Geometry.AutoCoherence = 0;")
    lines.append(f"lc = {lc:.8f};")
    lines.append("Mesh.CharacteristicLengthMin = lc;")
    lines.append("Mesh.CharacteristicLengthMax = lc;")

    point_id = 1
    line_id = 1
    loop_id = 1
    surface_id = 1

    physical_groups = {
        "Pores": [],
        "Aggregates coarse": [],
        "Aggregates fine": [],
        "Ptos_reactive": [],
    }

    for layer_name, loop_points in loops:
        if len(loop_points) < 3:
            continue

        point_ids: List[int] = []
        for x, y in loop_points:
            lines.append(f"Point({point_id}) = {{{x:.8f}, {y:.8f}, 0.0, lc}};")
            point_ids.append(point_id)
            point_id += 1

        curve_ids: List[int] = []
        for idx in range(len(point_ids)):
            p1 = point_ids[idx]
            p2 = point_ids[(idx + 1) % len(point_ids)]
            lines.append(f"Line({line_id}) = {{{p1}, {p2}}};")
            curve_ids.append(line_id)
            line_id += 1

        curves = ", ".join(str(cid) for cid in curve_ids)
        lines.append(f"Curve Loop({loop_id}) = {{{curves}}};")
        lines.append(f"Plane Surface({surface_id}) = {{{loop_id}}};")

        physical_groups[layer_name].append(surface_id)

        loop_id += 1
        surface_id += 1

    for layer_name, surfaces in physical_groups.items():
        if surfaces:
            ids = ", ".join(str(sid) for sid in surfaces)
            safe_name = layer_name.replace(" ", "_")
            lines.append(f'Physical Surface("{safe_name}") = {{{ids}}};')

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _entities_to_geo_loops(entities: Sequence[Dict[str, Any]]) -> List[Tuple[str, List[Tuple[float, float]]]]:
    loops: List[Tuple[str, List[Tuple[float, float]]]] = []
    for entity in entities:
        layer = entity["layer"]
        if entity["type"] == "circle":
            points = _circle_points(entity["x"], entity["y"], entity["r"], 48)
        elif entity["type"] == "ellipse":
            points = _ellipse_points(entity["x"], entity["y"], entity["a"], entity["b"], entity["angle_deg"], 64)
        else:
            points = entity["points"]
        loops.append((layer, points))
    return loops


def _estimate_geo_lc(entities: Sequence[Dict[str, Any]]) -> float:
    """Conservative mesh-size estimate to avoid losing small entities in Gmsh."""
    feature_sizes: List[float] = []

    for entity in entities:
        etype = entity.get("type")
        if etype == "circle":
            r = float(entity.get("r", 0.0))
            if r > 0.0:
                feature_sizes.append(r)
        elif etype == "ellipse":
            a = float(entity.get("a", 0.0))
            b = float(entity.get("b", 0.0))
            m = min(a, b)
            if m > 0.0:
                feature_sizes.append(m)
        elif etype == "polygon":
            points = entity.get("points", [])
            if len(points) >= 2:
                for i in range(len(points)):
                    x1, y1 = points[i]
                    x2, y2 = points[(i + 1) % len(points)]
                    edge = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
                    if edge > 0.0:
                        feature_sizes.append(edge)

    if not feature_sizes:
        return 0.25

    min_feature = min(feature_sizes)
    return max(1e-4, min_feature / 3.0)


def _svg_canvas_size(entities: Sequence[Dict[str, Any]], domain: Optional[Dict[str, float]]) -> Tuple[float, float]:
    if domain and domain.get("x") and domain.get("y"):
        return float(domain["x"]), float(domain["y"])

    min_x = 0.0
    min_y = 0.0
    max_x = 1.0
    max_y = 1.0

    for entity in entities:
        if entity["type"] == "circle":
            min_x = min(min_x, entity["x"] - entity["r"])
            min_y = min(min_y, entity["y"] - entity["r"])
            max_x = max(max_x, entity["x"] + entity["r"])
            max_y = max(max_y, entity["y"] + entity["r"])
        elif entity["type"] == "ellipse":
            radius = max(entity["a"], entity["b"])
            min_x = min(min_x, entity["x"] - radius)
            min_y = min(min_y, entity["y"] - radius)
            max_x = max(max_x, entity["x"] + radius)
            max_y = max(max_y, entity["y"] + radius)
        else:
            xs = [p[0] for p in entity["points"]]
            ys = [p[1] for p in entity["points"]]
            min_x = min(min_x, min(xs))
            min_y = min(min_y, min(ys))
            max_x = max(max_x, max(xs))
            max_y = max(max_y, max(ys))

    width = max(1.0, max_x - min_x)
    height = max(1.0, max_y - min_y)
    return width, height


def _collect_entities(
    mode: str,
    list_pores: Sequence[Any],
    list_aggregates_coarse: Sequence[Any],
    list_aggregates_fine: Sequence[Any],
    list_ptos_react: Sequence[Any],
) -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []

    entities.extend(_build_circle_entities(list_pores, "Pores"))
    entities.extend(_build_circle_entities(list_ptos_react, "Ptos_reactive"))

    if mode == "circulos":
        entities.extend(_build_circle_entities(list_aggregates_coarse, "Aggregates coarse"))
        entities.extend(_build_circle_entities(list_aggregates_fine, "Aggregates fine"))
    elif mode == "ellipses":
        entities.extend(_build_ellipse_entities(list_aggregates_coarse, "Aggregates coarse"))
        entities.extend(_build_ellipse_entities(list_aggregates_fine, "Aggregates fine"))
    elif mode == "poligonos":
        entities.extend(_build_polygon_entities(list_aggregates_coarse, "Aggregates coarse"))
        entities.extend(_build_polygon_entities(list_aggregates_fine, "Aggregates fine"))
    else:
        raise StructureExportError(f"Undefined mode: {mode}")

    return entities


def _build_circle_entities(items: Sequence[Any], layer_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items or []:
        circle = _as_circle(item)
        if circle is None:
            continue
        out.append({"layer": layer_name, "type": "circle", **circle})
    return out


def _build_ellipse_entities(items: Sequence[Any], layer_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items or []:
        ellipse = _as_ellipse(item)
        if ellipse is None:
            continue
        out.append({"layer": layer_name, "type": "ellipse", **ellipse})
    return out


def _build_polygon_entities(items: Sequence[Any], layer_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items or []:
        points = _as_polygon_points(item)
        if points is None:
            continue
        out.append({"layer": layer_name, "type": "polygon", "points": points})
    return out


def _as_circle(item: Any) -> Optional[Dict[str, float]]:
    if isinstance(item, (list, tuple)) and len(item) >= 3:
        try:
            return {"x": float(item[0]), "y": float(item[1]), "r": float(item[2])}
        except (TypeError, ValueError):
            return None
    return None


def _as_ellipse(item: Any) -> Optional[Dict[str, float]]:
    if isinstance(item, (list, tuple)) and len(item) >= 4:
        try:
            angle = float(item[4]) if len(item) >= 5 else 0.0
            return {
                "x": float(item[0]),
                "y": float(item[1]),
                "a": float(item[2]),
                "b": float(item[3]),
                "angle_deg": angle,
            }
        except (TypeError, ValueError):
            return None
    return None


def _as_polygon_points(item: Any) -> Optional[List[Tuple[float, float]]]:
    # Polygon Shapely
    if hasattr(item, "exterior"):
        try:
            points = [(float(x), float(y)) for x, y in list(item.exterior.coords)]
        except Exception:
            return None
    # Vertex list
    elif isinstance(item, (list, tuple)) and len(item) >= 3 and all(
        isinstance(p, (list, tuple)) and len(p) >= 2 for p in item
    ):
        try:
            points = [(float(p[0]), float(p[1])) for p in item]
        except (TypeError, ValueError):
            return None
    else:
        return None

    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]

    if len(points) < 3:
        return None

    return points


def _circle_points(x: float, y: float, r: float, num_points: int) -> List[Tuple[float, float]]:
    return [
        (x + r * math.cos(2.0 * math.pi * i / num_points), y + r * math.sin(2.0 * math.pi * i / num_points))
        for i in range(num_points)
    ]


def _ellipse_points(
    x: float,
    y: float,
    a: float,
    b: float,
    angle_deg: float,
    num_points: int,
) -> List[Tuple[float, float]]:
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    points: List[Tuple[float, float]] = []

    for i in range(num_points):
        t = 2.0 * math.pi * i / num_points
        px = a * math.cos(t)
        py = b * math.sin(t)
        xr = px * cos_a - py * sin_a + x
        yr = px * sin_a + py * cos_a + y
        points.append((xr, yr))

    return points

