from __future__ import annotations

from math import isfinite
from pathlib import Path
from urllib.parse import quote, urlencode

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from warhammer_companion.application.services import WarhammerCompanionService
from warhammer_companion.domain.damage import (
    DEFAULT_DAMAGE_PROFILE_INPUT,
    DEFAULT_TARGET_PROFILE_INPUT,
)
from warhammer_companion.domain.repository import FileBackedMapRepository
from warhammer_companion.ingestion.artifacts import IngestionPaths
from warhammer_companion.integrations.codex_backend import CodexBackend, sanitize_status_message
from warhammer_companion.sample_data import SAMPLE_PACKETS

PACKAGE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Warhammer Tournament Companion")
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
ingestion_paths = IngestionPaths()
repository = FileBackedMapRepository(ingestion_paths.map_packets_dir, fallback=SAMPLE_PACKETS)
codex_backend = CodexBackend()
service = WarhammerCompanionService(
    paths=ingestion_paths,
    repository=repository,
    codex_backend=codex_backend,
)


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/viewer", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request) -> HTMLResponse:
    state = service.settings_state()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "active_page": "settings",
            "app_backend_status": state.app_backend_status,
            "app_backend_detail": state.app_backend_detail,
            "codex_status": state.codex_status,
            "codex_action": request.query_params.get("codex_action"),
            "codex_message": request.query_params.get("codex_message"),
            "codex_login_url": request.query_params.get("codex_login_url"),
            "codex_user_code": request.query_params.get("codex_user_code"),
        },
    )


@app.post("/settings/codex/login", response_class=HTMLResponse)
def start_codex_login(method: str = Form("browser")) -> RedirectResponse:
    try:
        if method == "device-code":
            login = service.start_codex_device_code_login()
            return RedirectResponse(
                "/settings?"
                + urlencode(
                    {
                        "codex_action": "device-code-started",
                        "codex_login_url": login.verification_url or "",
                        "codex_user_code": login.user_code or "",
                    }
                ),
                status_code=303,
            )
        login = service.start_codex_login()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    if not login.auth_url:
        return RedirectResponse("/settings?codex_action=login-started", status_code=303)
    return RedirectResponse(login.auth_url, status_code=303)


@app.post("/settings/codex/logout", response_class=HTMLResponse)
def logout_codex() -> RedirectResponse:
    try:
        service.logout_codex()
    except Exception as exc:
        return _settings_codex_error_redirect(exc)
    return RedirectResponse("/settings?codex_action=logout-complete", status_code=303)


@app.get("/map-data", response_class=HTMLResponse)
def map_data(request: Request) -> HTMLResponse:
    state = service.map_data_state()
    return templates.TemplateResponse(
        request,
        "map_data.html",
        {
            "active_page": "map-data",
            "packets": state.packets,
            "deletable_packet_ids": state.deletable_packet_ids,
            "sources": state.sources,
            "pipeline": state.pipeline,
            "report": state.report,
            "ingestion_status": request.query_params.get("ingestion"),
            "ingestion_message": request.query_params.get("message"),
            "deleted": request.query_params.get("deleted"),
        },
    )


@app.post("/map-data/ingest", response_class=HTMLResponse)
def trigger_ingestion() -> RedirectResponse:
    try:
        service.run_ingestion()
    except Exception as exc:
        return RedirectResponse(
            f"/map-data?ingestion=failed&message={quote(str(exc))}",
            status_code=303,
        )
    return RedirectResponse("/map-data?ingestion=complete", status_code=303)


@app.post("/map-data/delete", response_class=HTMLResponse)
def delete_packet(packet_id: str = Form(...)) -> RedirectResponse:
    deleted = service.delete_packet(packet_id)
    return RedirectResponse(f"/map-data?deleted={int(deleted)}", status_code=303)


@app.get("/viewer", response_class=HTMLResponse)
def viewer(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
) -> HTMLResponse:
    state = service.viewer_state(
        packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return templates.TemplateResponse(
        request,
        "viewer.html",
        {
            "active_page": "viewer",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "map_svg": state.map_svg,
        },
    )


@app.get("/heatmap", response_class=HTMLResponse)
def heatmap(
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    zone_id: str = "attacker",
    source: str = "edge",
    offset_inches: int = 0,
) -> RedirectResponse:
    return RedirectResponse(
        "/los?"
        + urlencode(
            _without_none(
                {
                    "mode": "heatmap",
                    "packet_id": packet_id,
                    "player_a": player_a,
                    "player_b": player_b,
                    "layout_variant": layout_variant,
                    "zone_id": zone_id,
                    "source": source,
                    "offset_inches": offset_inches,
                }
            )
        ),
        status_code=303,
    )


@app.get("/los", response_class=HTMLResponse)
def los_analysis(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    mode: str = "heatmap",
    zone_id: str = "attacker",
    source: str = "edge",
    offset_inches: str = "0",
    x: str = "22.0",
    y: str = "10.0",
    base: str = "1.57",
) -> HTMLResponse:
    active_mode = "checker" if mode == "checker" else "heatmap"
    active_offset_inches = (
        0 if active_mode == "checker" else _parse_int_param(offset_inches, "offset_inches")
    )
    active_x = 22.0 if active_mode == "heatmap" else _parse_float_param(x, "x")
    active_y = 10.0 if active_mode == "heatmap" else _parse_float_param(y, "y")
    active_base = 1.57 if active_mode == "heatmap" else _parse_float_param(base, "base")
    state = service.los_analysis_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        mode=active_mode,
        zone_id=zone_id,
        source=source,
        offset_inches=active_offset_inches,
        x=active_x,
        y=active_y,
        base=active_base,
    )
    return templates.TemplateResponse(
        request,
        "los_analysis.html",
        {
            "active_page": "los",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "mode": state.mode,
            "modes": state.modes,
            "heatmap": state.heatmap,
            "checker": state.checker,
            "map_svg": state.map_svg,
        },
    )


@app.get("/los-checker", response_class=HTMLResponse)
def los_checker(
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    x: float = 22.0,
    y: float = 10.0,
    base: float = 1.57,
) -> RedirectResponse:
    return RedirectResponse(
        "/los?"
        + urlencode(
            _without_none(
                {
                    "mode": "checker",
                    "packet_id": packet_id,
                    "player_a": player_a,
                    "player_b": player_b,
                    "layout_variant": layout_variant,
                    "x": x,
                    "y": y,
                    "base": base,
                }
            )
        ),
        status_code=303,
    )


@app.get("/movement-reach", response_class=HTMLResponse)
def movement_reach(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    start_x: float = 16.0,
    start_y: float = 10.0,
    target_x: float = 22.0,
    target_y: float = 10.0,
    base: float = 1.57,
    move: float = 6.0,
    mode: str = "normal",
    movement_profile: str = "ground-non-mobile",
) -> HTMLResponse:
    state = service.movement_reach_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        start_x=start_x,
        start_y=start_y,
        target_x=target_x,
        target_y=target_y,
        base=base,
        move=move,
        mode=mode,
        movement_profile=movement_profile,
    )
    return templates.TemplateResponse(
        request,
        "movement_reach.html",
        {
            "active_page": "movement-reach",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "start_x": state.start_x,
            "start_y": state.start_y,
            "target_x": state.target_x,
            "target_y": state.target_y,
            "base": state.base,
            "move": state.move,
            "mode": state.mode,
            "movement_modes": state.movement_modes,
            "movement_profile": state.movement_profile,
            "movement_profiles": state.movement_profiles,
            "movement_profile_label": state.movement_profile_label,
            "effective_move": state.effective_move,
            "input_hash": state.input_hash,
            "endpoint_estimated_reachable": state.endpoint_estimated_reachable,
            "endpoint_reason_details": state.endpoint_reason_details,
            "map_svg": state.map_svg,
        },
    )


@app.get("/threat-range", response_class=HTMLResponse)
def threat_range(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    source_x: str = "16.0",
    source_y: str = "10.0",
    target_x: float = 24.0,
    target_y: float = 10.0,
    base: float = 1.57,
    move: float = 6.0,
    threat: float = 2.0,
    mode: str = "fixed-move-plus-range",
    movement_profile: str = "ground-non-mobile",
    source_mode: str = "point",
    source_deployment_zone_id: str = "attacker",
) -> HTMLResponse:
    active_source_x = _parse_float_param(source_x, "source_x") if source_mode == "point" else 16.0
    active_source_y = _parse_float_param(source_y, "source_y") if source_mode == "point" else 10.0
    state = service.threat_range_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        source_x=active_source_x,
        source_y=active_source_y,
        target_x=target_x,
        target_y=target_y,
        base=base,
        move=move,
        threat=threat,
        mode=mode,
        movement_profile=movement_profile,
        source_mode=source_mode,
        source_deployment_zone_id=source_deployment_zone_id,
    )
    return templates.TemplateResponse(
        request,
        "threat_range.html",
        {
            "active_page": "threat-range",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "source_x": state.source_x,
            "source_y": state.source_y,
            "target_x": state.target_x,
            "target_y": state.target_y,
            "base": state.base,
            "move": state.move,
            "threat": state.threat,
            "mode": state.mode,
            "threat_modes": state.threat_modes,
            "source_mode": state.source_mode,
            "source_modes": state.source_modes,
            "source_deployment_zone_id": state.source_deployment_zone_id,
            "source_deployment_zone_options": state.source_deployment_zone_options,
            "source_label": state.source_label,
            "movement_profile": state.movement_profile,
            "movement_profiles": state.movement_profiles,
            "movement_profile_label": state.movement_profile_label,
            "effective_move": state.effective_move,
            "input_hash": state.input_hash,
            "measurement_convention": state.measurement_convention,
            "target_probability": state.target_probability,
            "distribution": state.distribution,
            "warning_details": state.warning_details,
            "map_svg": state.map_svg,
        },
    )


@app.get("/hidden-coverage", response_class=HTMLResponse)
def hidden_coverage(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    terrain_area_id: str | None = None,
    detection_range: int = 15,
) -> HTMLResponse:
    state = service.hidden_coverage_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        terrain_area_id=terrain_area_id,
        detection_range=detection_range,
    )
    return templates.TemplateResponse(
        request,
        "hidden_coverage.html",
        {
            "active_page": "hidden-coverage",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "terrain_options": state.terrain_options,
            "selected_terrain_area_id": state.selected_terrain_area_id,
            "selected_detection_range": state.selected_detection_range,
            "detection_range_options": state.detection_range_options,
            "map_svg": state.map_svg,
        },
    )


@app.get("/deployment-exposure", response_class=HTMLResponse)
def deployment_exposure(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    deployment_zone_id: str = "attacker",
    friendly_x: float = 19.24,
    friendly_y: float = 51.48,
    friendly_base: float = 1.57,
    enemy_x: float = 24.77,
    enemy_y: float = 8.46,
    enemy_base: float = 1.57,
    enemy_move: float = 0.0,
    enemy_threat: float = 1.0,
    enemy_mode: str = "raw-range",
    enemy_movement_profile: str = "ground-non-mobile",
    exposure_mode: str = "threat-and-los",
) -> HTMLResponse:
    state = service.deployment_exposure_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        deployment_zone_id=deployment_zone_id,
        friendly_x=friendly_x,
        friendly_y=friendly_y,
        friendly_base=friendly_base,
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        enemy_base=enemy_base,
        enemy_move=enemy_move,
        enemy_threat=enemy_threat,
        enemy_mode=enemy_mode,
        enemy_movement_profile=enemy_movement_profile,
        exposure_mode=exposure_mode,
    )
    return templates.TemplateResponse(
        request,
        "deployment_exposure.html",
        {
            "active_page": "deployment-exposure",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "deployment_zone_options": state.deployment_zone_options,
            "deployment_zone_id": state.deployment_zone_id,
            "friendly_x": state.friendly_x,
            "friendly_y": state.friendly_y,
            "friendly_base": state.friendly_base,
            "enemy_x": state.enemy_x,
            "enemy_y": state.enemy_y,
            "enemy_base": state.enemy_base,
            "enemy_move": state.enemy_move,
            "enemy_threat": state.enemy_threat,
            "enemy_mode": state.enemy_mode,
            "enemy_movement_profile": state.enemy_movement_profile,
            "enemy_movement_profiles": state.enemy_movement_profiles,
            "enemy_movement_profile_label": state.enemy_movement_profile_label,
            "enemy_effective_move": state.enemy_effective_move,
            "exposure_mode": state.exposure_mode,
            "enemy_threat_modes": state.enemy_threat_modes,
            "exposure_modes": state.exposure_modes,
            "not_exposed_under_assumptions": state.not_exposed_under_assumptions,
            "threat_probability_at_center": state.threat_probability_at_center,
            "placement_reason_details": state.placement_reason_details,
            "warning_details": state.warning_details,
            "input_hash": state.input_hash,
            "map_svg": state.map_svg,
        },
    )


@app.get("/deployment-scorecard", response_class=HTMLResponse)
def deployment_scorecard(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    deployment_zone_id: str = "attacker",
    friendly_x: float = 19.24,
    friendly_y: float = 51.48,
    friendly_base: float = 1.57,
    enemy_x: float = 24.77,
    enemy_y: float = 8.46,
    enemy_base: float = 1.57,
    enemy_move: float = 0.0,
    enemy_threat: float = 1.0,
    enemy_mode: str = "raw-range",
    enemy_movement_profile: str = "ground-non-mobile",
    exposure_mode: str = "threat-and-los",
    turn_order: str = "going-first",
) -> HTMLResponse:
    state = service.deployment_scorecard_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        deployment_zone_id=deployment_zone_id,
        friendly_x=friendly_x,
        friendly_y=friendly_y,
        friendly_base=friendly_base,
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        enemy_base=enemy_base,
        enemy_move=enemy_move,
        enemy_threat=enemy_threat,
        enemy_mode=enemy_mode,
        enemy_movement_profile=enemy_movement_profile,
        exposure_mode=exposure_mode,
        turn_order=turn_order,
    )
    return templates.TemplateResponse(
        request,
        "deployment_scorecard.html",
        {
            "active_page": "deployment-scorecard",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "deployment_zone_options": state.deployment_zone_options,
            "deployment_zone_id": state.deployment_zone_id,
            "friendly_x": state.friendly_x,
            "friendly_y": state.friendly_y,
            "friendly_base": state.friendly_base,
            "enemy_x": state.enemy_x,
            "enemy_y": state.enemy_y,
            "enemy_base": state.enemy_base,
            "enemy_move": state.enemy_move,
            "enemy_threat": state.enemy_threat,
            "enemy_mode": state.enemy_mode,
            "enemy_movement_profile": state.enemy_movement_profile,
            "enemy_movement_profiles": state.enemy_movement_profiles,
            "enemy_movement_profile_label": state.enemy_movement_profile_label,
            "enemy_effective_move": state.enemy_effective_move,
            "exposure_mode": state.exposure_mode,
            "turn_order": state.turn_order,
            "enemy_threat_modes": state.enemy_threat_modes,
            "exposure_modes": state.exposure_modes,
            "turn_order_options": state.turn_order_options,
            "readiness": state.readiness,
            "is_blocked": state.is_blocked,
            "not_exposed_under_assumptions": state.not_exposed_under_assumptions,
            "threat_probability_at_center": state.threat_probability_at_center,
            "components": state.components,
            "block_reason_details": state.block_reason_details,
            "warning_details": state.warning_details,
            "input_hash": state.input_hash,
            "map_svg": state.map_svg,
        },
    )


@app.get("/damage-profile", response_class=HTMLResponse)
def damage_profile(
    request: Request,
    attacks: float = DEFAULT_DAMAGE_PROFILE_INPUT.attacks,
    hit: int = DEFAULT_DAMAGE_PROFILE_INPUT.hit_target,
    wound: int = DEFAULT_DAMAGE_PROFILE_INPUT.wound_target,
    save: int = DEFAULT_DAMAGE_PROFILE_INPUT.save_target,
    damage: float = DEFAULT_DAMAGE_PROFILE_INPUT.damage_per_unsaved_wound,
    wounds: float = DEFAULT_TARGET_PROFILE_INPUT.wounds_per_model,
    models: float = DEFAULT_TARGET_PROFILE_INPUT.model_count,
) -> HTMLResponse:
    state = service.damage_profile_state(
        attacks=attacks,
        hit=hit,
        wound=wound,
        save=save,
        damage=damage,
        wounds=wounds,
        models=models,
    )
    return templates.TemplateResponse(
        request,
        "damage_profile.html",
        {
            "active_page": "damage-profile",
            "attacks": state.attacks,
            "hit": state.hit_target,
            "wound": state.wound_target,
            "save": state.save_target,
            "damage": state.damage_per_unsaved_wound,
            "wounds": state.target_wounds_per_model,
            "models": state.target_model_count,
            "is_blocked": state.is_blocked,
            "expected_hits": state.expected_hits,
            "expected_wounds": state.expected_wounds,
            "expected_unsaved_wounds": state.expected_unsaved_wounds,
            "expected_damage": state.expected_damage,
            "expected_models_destroyed": state.expected_models_destroyed,
            "probability_destroying_at_least_one_model": (
                state.probability_destroying_at_least_one_model
            ),
            "unsaved_wound_distribution": state.unsaved_wound_distribution,
            "models_destroyed_distribution": state.models_destroyed_distribution,
            "warning_details": state.warning_details,
            "block_reason_details": state.block_reason_details,
        },
    )


@app.get("/mission-pack", response_class=HTMLResponse)
def mission_pack(request: Request) -> HTMLResponse:
    state = service.mission_pack_state()
    return templates.TemplateResponse(
        request,
        "mission_pack.html",
        {
            "active_page": "mission-pack",
            "readiness": state.readiness,
            "mission_count": state.mission_count,
            "source_refs": state.source_refs,
            "primary_missions": state.primary_missions,
            "warning_details": state.warning_details,
            "pack": state.pack,
        },
    )


@app.get("/team-pairing", response_class=HTMLResponse)
def team_pairing(
    request: Request,
    packet_id: str | None = None,
    player_a: str | None = None,
    player_b: str | None = None,
    layout_variant: str | None = None,
    friendly_lists: str = "Alpha\nBeta",
    opponent_lists: str = "Gamma\nDelta",
) -> HTMLResponse:
    state = service.team_pairing_matrix_state(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
        friendly_lists=friendly_lists,
        opponent_lists=opponent_lists,
    )
    return templates.TemplateResponse(
        request,
        "team_pairing.html",
        {
            "active_page": "team-pairing",
            "packet": state.packet,
            "packet_groups": state.packet_groups,
            "packet_selector": state.packet_selector,
            "friendly_lists_text": state.friendly_lists_text,
            "opponent_lists_text": state.opponent_lists_text,
            "readiness": state.readiness,
            "is_blocked": state.is_blocked,
            "friendly_lists": state.friendly_lists,
            "opponent_lists": state.opponent_lists,
            "friendly_labels_by_id": {entry.list_id: entry.label for entry in state.friendly_lists},
            "opponent_labels_by_id": {entry.list_id: entry.label for entry in state.opponent_lists},
            "scenarios": state.scenarios,
            "cells": state.cells,
            "ranges": state.ranges,
            "warning_details": state.warning_details,
            "block_reason_details": state.block_reason_details,
        },
    )


@app.post("/los-checker", response_class=HTMLResponse)
def update_los_checker(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    x: float = Form(...),
    y: float = Form(...),
    base: float = Form(...),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        "/los?"
        + urlencode(
            {
                "mode": "checker",
                "packet_id": resolved_packet_id,
                "x": x,
                "y": y,
                "base": base,
            }
        ),
        status_code=303,
    )


@app.post("/los", response_class=HTMLResponse)
def update_los_analysis(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    mode: str = Form("heatmap"),
    zone_id: str = Form("attacker"),
    source: str = Form("edge"),
    offset_inches: str = Form("0"),
    x: str = Form("22.0"),
    y: str = Form("10.0"),
    base: str = Form("1.57"),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    if mode == "checker":
        active_x = _parse_float_param(x, "x")
        active_y = _parse_float_param(y, "y")
        active_base = _parse_float_param(base, "base")
        params = {
            "mode": "checker",
            "packet_id": resolved_packet_id,
            "x": active_x,
            "y": active_y,
            "base": active_base,
        }
    else:
        active_offset_inches = _parse_int_param(offset_inches, "offset_inches")
        params = {
            "mode": "heatmap",
            "packet_id": resolved_packet_id,
            "zone_id": zone_id,
            "source": source,
            "offset_inches": active_offset_inches,
        }
    return RedirectResponse(
        "/los?" + urlencode(params),
        status_code=303,
    )


@app.post("/movement-reach", response_class=HTMLResponse)
def update_movement_reach(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    start_x: float = Form(...),
    start_y: float = Form(...),
    target_x: float = Form(...),
    target_y: float = Form(...),
    base: float = Form(...),
    move: float = Form(...),
    mode: str = Form("normal"),
    movement_profile: str = Form("ground-non-mobile"),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        "/movement-reach?"
        + urlencode(
            {
                "packet_id": resolved_packet_id,
                "start_x": start_x,
                "start_y": start_y,
                "target_x": target_x,
                "target_y": target_y,
                "base": base,
                "move": move,
                "mode": mode,
                "movement_profile": movement_profile,
            }
        ),
        status_code=303,
    )


@app.post("/deployment-exposure", response_class=HTMLResponse)
def update_deployment_exposure(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    deployment_zone_id: str = Form("attacker"),
    friendly_x: float = Form(...),
    friendly_y: float = Form(...),
    friendly_base: float = Form(...),
    enemy_x: float = Form(...),
    enemy_y: float = Form(...),
    enemy_base: float = Form(...),
    enemy_move: float = Form(...),
    enemy_threat: float = Form(...),
    enemy_mode: str = Form("raw-range"),
    enemy_movement_profile: str = Form("ground-non-mobile"),
    exposure_mode: str = Form("threat-and-los"),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        "/deployment-exposure?"
        + urlencode(
            {
                "packet_id": resolved_packet_id,
                "deployment_zone_id": deployment_zone_id,
                "friendly_x": friendly_x,
                "friendly_y": friendly_y,
                "friendly_base": friendly_base,
                "enemy_x": enemy_x,
                "enemy_y": enemy_y,
                "enemy_base": enemy_base,
                "enemy_move": enemy_move,
                "enemy_threat": enemy_threat,
                "enemy_mode": enemy_mode,
                "enemy_movement_profile": enemy_movement_profile,
                "exposure_mode": exposure_mode,
            }
        ),
        status_code=303,
    )


@app.post("/deployment-scorecard", response_class=HTMLResponse)
def update_deployment_scorecard(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    deployment_zone_id: str = Form("attacker"),
    friendly_x: float = Form(...),
    friendly_y: float = Form(...),
    friendly_base: float = Form(...),
    enemy_x: float = Form(...),
    enemy_y: float = Form(...),
    enemy_base: float = Form(...),
    enemy_move: float = Form(...),
    enemy_threat: float = Form(...),
    enemy_mode: str = Form("raw-range"),
    enemy_movement_profile: str = Form("ground-non-mobile"),
    exposure_mode: str = Form("threat-and-los"),
    turn_order: str = Form("going-first"),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        "/deployment-scorecard?"
        + urlencode(
            {
                "packet_id": resolved_packet_id,
                "deployment_zone_id": deployment_zone_id,
                "friendly_x": friendly_x,
                "friendly_y": friendly_y,
                "friendly_base": friendly_base,
                "enemy_x": enemy_x,
                "enemy_y": enemy_y,
                "enemy_base": enemy_base,
                "enemy_move": enemy_move,
                "enemy_threat": enemy_threat,
                "enemy_mode": enemy_mode,
                "enemy_movement_profile": enemy_movement_profile,
                "exposure_mode": exposure_mode,
                "turn_order": turn_order,
            }
        ),
        status_code=303,
    )


@app.post("/damage-profile", response_class=HTMLResponse)
def update_damage_profile(
    attacks: float = Form(...),
    hit: int = Form(...),
    wound: int = Form(...),
    save: int = Form(...),
    damage: float = Form(...),
    wounds: float = Form(...),
    models: float = Form(...),
) -> RedirectResponse:
    return RedirectResponse(
        "/damage-profile?"
        + urlencode(
            {
                "attacks": attacks,
                "hit": hit,
                "wound": wound,
                "save": save,
                "damage": damage,
                "wounds": wounds,
                "models": models,
            }
        ),
        status_code=303,
    )


@app.post("/team-pairing", response_class=HTMLResponse)
def update_team_pairing(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    friendly_lists: str = Form(""),
    opponent_lists: str = Form(""),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    return RedirectResponse(
        "/team-pairing?"
        + urlencode(
            {
                "packet_id": resolved_packet_id,
                "friendly_lists": friendly_lists,
                "opponent_lists": opponent_lists,
            }
        ),
        status_code=303,
    )


@app.post("/threat-range", response_class=HTMLResponse)
def update_threat_range(
    packet_id: str | None = Form(None),
    player_a: str | None = Form(None),
    player_b: str | None = Form(None),
    layout_variant: str | None = Form(None),
    source_mode: str = Form("point"),
    source_deployment_zone_id: str = Form("attacker"),
    source_x: str = Form("16.0"),
    source_y: str = Form("10.0"),
    target_x: float = Form(...),
    target_y: float = Form(...),
    base: float = Form(...),
    move: float = Form(...),
    threat: float = Form(...),
    mode: str = Form("fixed-move-plus-range"),
    movement_profile: str = Form("ground-non-mobile"),
) -> RedirectResponse:
    resolved_packet_id = service.resolve_packet_id(
        packet_id=packet_id,
        player_a=player_a,
        player_b=player_b,
        layout_variant=layout_variant,
    )
    params: dict[str, object] = {
        "packet_id": resolved_packet_id,
        "source_mode": source_mode,
        "source_deployment_zone_id": source_deployment_zone_id,
    }
    if source_mode == "point":
        params["source_x"] = _parse_float_param(source_x, "source_x")
        params["source_y"] = _parse_float_param(source_y, "source_y")
    params.update(
        {
            "target_x": target_x,
            "target_y": target_y,
            "base": base,
            "move": move,
            "threat": threat,
            "mode": mode,
            "movement_profile": movement_profile,
        }
    )
    return RedirectResponse(
        "/threat-range?" + urlencode(params),
        status_code=303,
    )


def _settings_codex_error_redirect(exc: Exception) -> RedirectResponse:
    return RedirectResponse(
        "/settings?"
        + urlencode(
            {
                "codex_action": "error",
                "codex_message": sanitize_status_message(str(exc)),
            }
        ),
        status_code=303,
    )


def _without_none(values: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in values.items() if value is not None}


def _parse_float_param(value: str, field_name: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"{field_name} must be a finite number"
        ) from exc
    if not isfinite(parsed):
        raise HTTPException(status_code=422, detail=f"{field_name} must be a finite number")
    return parsed


def _parse_int_param(value: str, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be an integer") from exc
