from typing import Any, Dict, Optional, Sequence

from src.io.structure_export_EN import StructureExportError, export_structure_file as _export_structure_file_en


def _normalize_mode(mode: str) -> str:
    if mode == "elipses":
        return "ellipses"
    return mode


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
    # Accept both ES and EN keyword names from callers.
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

    normalized_mode = _normalize_mode(mode)
    return _export_structure_file_en(
        path=path,
        selected_filter=selected_filter,
        mode=normalized_mode,
        list_pores=list_pores,
        list_aggregates_coarse=list_aggregates_coarse,
        list_aggregates_fine=list_aggregates_fine,
        list_ptos_react=list_ptos_react,
        domain=domain,
    )
