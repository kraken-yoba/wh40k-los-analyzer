const canvas = document.querySelector("#board-canvas");
const context = canvas.getContext("2d");
const layoutSelect = document.querySelector("#layout-select");
const loadLayoutButton = document.querySelector("#load-layout-button");
const interactionMode = document.querySelector("#interaction-mode");
const layoutMetadata = document.querySelector("#layout-metadata");
const sourceStatus = document.querySelector("#source-status");
const rulesEvidence = document.querySelector("#rules-evidence");
const footprintEvidence = document.querySelector("#footprint-evidence");
const footprintMatchEvidence = document.querySelector("#footprint-match-evidence");
const footprintNormalizationEvidence = document.querySelector("#footprint-normalization-evidence");
const terrainSymmetryEvidence = document.querySelector("#terrain-symmetry-evidence");
const terrainReconciliationEvidence = document.querySelector("#terrain-reconciliation-evidence");
const reconciliationProcess = document.querySelector("#reconciliation-process");
const visualSanityEvidence = document.querySelector("#visual-sanity-evidence");
const terrainSemantics = document.querySelector("#terrain-semantics");
const featureProvenance = document.querySelector("#feature-provenance");
const validationPanel = document.querySelector("#validation-panel");
const losResult = document.querySelector("#los-result");
const analysisResult = document.querySelector("#analysis-result");
const baseDiameter = document.querySelector("#base-diameter");
const movementDistance = document.querySelector("#movement-distance");
const sourceUnderlayToggle = document.querySelector("#source-underlay-toggle");
const sourceUnderlayStatus = document.querySelector("#source-underlay-status");
const FOOTPRINT_EXTRACTION_METHOD = "terrain-footprint-vector-v1";
const FOOTPRINT_MATCH_METHOD = "terrain-footprint-match-v1";
const FOOTPRINT_NORMALIZATION_METHOD = "terrain-footprint-normalization-v1";
const TERRAIN_SYMMETRY_METHOD = "terrain-symmetry-v1";
const TERRAIN_RECONCILIATION_METHOD = "terrain-reconciliation-v1";
const RULES_TERRAIN_SEMANTICS_METHOD = "core-rules-terrain-semantics-v1";

const state = {
  layout: null,
  layoutHash: null,
  selectedPoints: [],
  selectedFeatureId: null,
  heatmap: null,
  sourceUnderlayImage: null,
  sourceUnderlayObjectUrl: null,
  sourceUnderlayRequestId: 0,
};

function boardToCanvas(point) {
  return {
    x: (point.x / state.layout.board.width) * canvas.width,
    y: canvas.height - (point.y / state.layout.board.height) * canvas.height,
  };
}

function canvasToBoard(event) {
  const rect = canvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * state.layout.board.width;
  const y = (1 - (event.clientY - rect.top) / rect.height) * state.layout.board.height;
  return {
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2)),
  };
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(formatApiDetail(payload.detail) || `${url} returned ${response.status}`);
  }
  return payload;
}

function formatApiDetail(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) return item.msg;
        if (item && typeof item === "object") return JSON.stringify(item);
        return String(item);
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  if (detail) return String(detail);
  return "";
}

function renderError(panel, error) {
  panel.textContent = `Error: ${error instanceof Error ? error.message : String(error)}`;
}

async function runPanelAction(panel, action) {
  try {
    await action();
  } catch (error) {
    renderError(panel, error);
  }
}

function appendDenseItem(container, label, value) {
  const item = window.document.createElement("div");
  const labelNode = window.document.createElement("span");
  const valueNode = window.document.createElement("strong");
  item.className = "dense-item";
  labelNode.textContent = label;
  valueNode.textContent = value;
  item.append(labelNode, valueNode);
  container.appendChild(item);
}

function terrainFill(feature) {
  switch (feature.terrain_category) {
    case "dense":
      return "#8fb59a";
    case "light":
      return "#d6c87d";
    case "exposed":
      return "#e7ded0";
    default:
      return "#d4d0c8";
  }
}

function terrainCategoryCounts(features) {
  const counts = { dense: 0, light: 0, exposed: 0, unknown: 0 };
  for (const feature of features) {
    const category = feature.terrain_category in counts ? feature.terrain_category : "unknown";
    counts[category] += 1;
  }
  return counts;
}

function denseWallCandidateCount() {
  if (!state.layout) return 0;
  const denseFeatureIds = new Set(
    state.layout.terrain_features
      .filter((feature) => feature.terrain_category === "dense")
      .map((feature) => feature.feature_id),
  );
  return state.layout.blockers.filter((blocker) => denseFeatureIds.has(blocker.feature_id)).length;
}

function appendTerrainSemanticItem(container, label, value, color, style = "fill") {
  const item = window.document.createElement("div");
  const swatch = window.document.createElement("span");
  const labelNode = window.document.createElement("span");
  const valueNode = window.document.createElement("strong");
  item.className = "terrain-item";
  if (style === "line") {
    swatch.className = "terrain-line-swatch";
  } else {
    swatch.className = "terrain-swatch";
    swatch.style.background = color;
  }
  labelNode.textContent = label;
  valueNode.textContent = value;
  item.append(swatch, labelNode, valueNode);
  container.appendChild(item);
}

function renderTerrainSemantics() {
  terrainSemantics.replaceChildren();
  if (!state.layout) return;
  const counts = terrainCategoryCounts(state.layout.terrain_features);
  appendTerrainSemanticItem(terrainSemantics, "Dense", `${counts.dense} features`, "#8fb59a");
  appendTerrainSemanticItem(terrainSemantics, "Light", `${counts.light} features`, "#d6c87d");
  appendTerrainSemanticItem(terrainSemantics, "Exposed", `${counts.exposed} features`, "#e7ded0");
  appendTerrainSemanticItem(terrainSemantics, "Unknown", `${counts.unknown} features`, "#d4d0c8");
  appendTerrainSemanticItem(
    terrainSemantics,
    "Dense wall candidates",
    `${denseWallCandidateCount()} segments`,
    "#b7791f",
    "line",
  );
}

function hasValidationCode(code) {
  if (!state.layout || !Array.isArray(state.layout.validation_records)) return false;
  return state.layout.validation_records.some((record) => record.code === code);
}

function pointInPolygon(point, polygon) {
  let inside = false;
  const vertices = polygon.points;
  for (let index = 0, previousIndex = vertices.length - 1; index < vertices.length; previousIndex = index, index += 1) {
    const current = vertices[index];
    const previous = vertices[previousIndex];
    const crosses =
      current.y > point.y !== previous.y > point.y &&
      point.x < ((previous.x - current.x) * (point.y - current.y)) / (previous.y - current.y) + current.x;
    if (crosses) inside = !inside;
  }
  return inside;
}

function featureAtPoint(point) {
  if (!state.layout) return null;
  const features = state.layout.terrain_features;
  for (let index = features.length - 1; index >= 0; index -= 1) {
    if (pointInPolygon(point, features[index].footprint)) return features[index];
  }
  return null;
}

function selectedFeature() {
  if (!state.layout || !state.selectedFeatureId) return null;
  return (
    state.layout.terrain_features.find(
      (feature) => feature.feature_id === state.selectedFeatureId,
    ) || null
  );
}

function renderBoard() {
  if (!state.layout) return;
  context.clearRect(0, 0, canvas.width, canvas.height);
  if (state.sourceUnderlayImage) {
    context.drawImage(state.sourceUnderlayImage, 0, 0, canvas.width, canvas.height);
    context.fillStyle = "rgba(255, 253, 248, 0.18)";
    context.fillRect(0, 0, canvas.width, canvas.height);
  } else {
    context.fillStyle = "#fffdf8";
    context.fillRect(0, 0, canvas.width, canvas.height);
  }
  context.strokeStyle = "#1e272b";
  context.lineWidth = 4;
  context.strokeRect(2, 2, canvas.width - 4, canvas.height - 4);

  for (const feature of state.layout.terrain_features) {
    const points = feature.footprint.points.map(boardToCanvas);
    context.beginPath();
    points.forEach((point, index) => {
      if (index === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    });
    context.closePath();
    context.fillStyle = terrainFill(feature);
    context.globalAlpha = state.sourceUnderlayImage ? 0.58 : 1;
    context.fill();
    context.globalAlpha = 1;
    context.strokeStyle = "#746a5c";
    context.lineWidth = 2;
    context.stroke();
    if (feature.feature_id === state.selectedFeatureId) {
      context.setLineDash([8, 5]);
      context.strokeStyle = "#1f5f99";
      context.lineWidth = 5;
      context.stroke();
      context.setLineDash([]);
    }
  }

  for (const blocker of state.layout.blockers) {
    const start = boardToCanvas(blocker.start);
    const end = boardToCanvas(blocker.end);
    context.beginPath();
    context.moveTo(start.x, start.y);
    context.lineTo(end.x, end.y);
    context.setLineDash([]);
    context.strokeStyle = "#8f2f2f";
    context.lineWidth = 6;
    context.stroke();
  }
  context.setLineDash([]);

  if (state.heatmap) {
    for (const cell of state.heatmap.cells) {
      const center = boardToCanvas(cell.center);
      context.fillStyle = cell.no_data
        ? "rgba(70, 70, 70, 0.28)"
        : `rgba(32, 114, 157, ${0.15 + cell.normalized_visibility * 0.55})`;
      context.beginPath();
      context.arc(center.x, center.y, 14, 0, Math.PI * 2);
      context.fill();
    }
  }

  state.selectedPoints.forEach((point, index) => {
    const canvasPoint = boardToCanvas(point);
    context.fillStyle = index === 0 ? "#206b3f" : "#1f5f99";
    context.beginPath();
    context.arc(canvasPoint.x, canvasPoint.y, 11, 0, Math.PI * 2);
    context.fill();
  });
}

function renderSources(payload) {
  sourceStatus.replaceChildren();
  for (const sourceDocument of payload.documents) {
    appendDenseItem(
      sourceStatus,
      sourceDocument.document_id,
      sourceDocument.cache_status.status,
    );
  }
}

function ruleLabel(code) {
  switch (code) {
    case "dense_solid_blocks_2d_los":
      return "Dense/Solid";
    case "light_exposed_not_opaque_blockers":
      return "Light/Exposed";
    case "future_3d_rules_scope":
      return "future 3D-aware LOS";
    default:
      return code;
  }
}

function renderRulesEvidence(payload) {
  rulesEvidence.replaceChildren();
  const cacheStatus = payload.cache_status ? payload.cache_status.status : "unavailable";
  appendDenseItem(rulesEvidence, "Status", cacheStatus);
  appendDenseItem(
    rulesEvidence,
    "Method",
    payload.extraction_method || RULES_TERRAIN_SEMANTICS_METHOD,
  );
  appendDenseItem(rulesEvidence, "Backing", payload.backing_status || "source_unavailable");
  for (const rule of payload.rules || []) {
    const pages = (rule.source_pages || []).map((page) => `p${page}`).join(",");
    appendDenseItem(
      rulesEvidence,
      ruleLabel(rule.code),
      `${pages} ${rule.engine_implication}`,
    );
  }
  for (const code of payload.missing_anchor_codes || []) {
    appendDenseItem(rulesEvidence, "Missing anchor", code);
  }
}

async function loadRulesEvidence() {
  rulesEvidence.textContent = "Loading rules evidence.";
  try {
    const payload = await getJson("/api/rules/terrain-semantics");
    renderRulesEvidence(payload);
  } catch (error) {
    renderError(rulesEvidence, error);
  }
}

function renderFootprintEvidence(payload) {
  footprintEvidence.replaceChildren();
  const cacheStatus = payload.cache_status ? payload.cache_status.status : "unavailable";
  appendDenseItem(footprintEvidence, "Status", cacheStatus);
  appendDenseItem(
    footprintEvidence,
    "Method",
    payload.extraction_method || FOOTPRINT_EXTRACTION_METHOD,
  );
  appendDenseItem(footprintEvidence, "Outlines", String(payload.outlines.length));
  for (const outline of payload.outlines) {
    appendDenseItem(
      footprintEvidence,
      outline.footprint_id,
      `p${outline.page_number} ${formatBounds(outline.bounds)}`,
    );
  }
}

function renderFootprintMatches(payload) {
  footprintMatchEvidence.replaceChildren();
  const cacheStatus = payload.cache_status ? payload.cache_status.status : "unavailable";
  appendDenseItem(footprintMatchEvidence, "Status", cacheStatus);
  appendDenseItem(
    footprintMatchEvidence,
    "Method",
    payload.extraction_method || FOOTPRINT_MATCH_METHOD,
  );
  appendDenseItem(footprintMatchEvidence, "Matches", String(payload.matches.length));
  for (const match of payload.matches) {
    const score = Number(match.score).toFixed(3);
    appendDenseItem(
      footprintMatchEvidence,
      match.feature_id,
      `${match.template_id} score=${score} ${match.status} ${match.review_reason}`,
    );
  }
}

function renderFootprintNormalization(payload) {
  footprintNormalizationEvidence.replaceChildren();
  appendDenseItem(footprintNormalizationEvidence, "Status", payload.status || "unavailable");
  appendDenseItem(
    footprintNormalizationEvidence,
    "Method",
    payload.extraction_method || FOOTPRINT_NORMALIZATION_METHOD,
  );
  appendDenseItem(footprintNormalizationEvidence, "Options", String(payload.options.length));
  appendDenseItem(
    footprintNormalizationEvidence,
    "Detected",
    String(payload.detected_elements.length),
  );
  appendDenseItem(footprintNormalizationEvidence, "Matches", String(payload.matches.length));
  for (const option of payload.options || []) {
    appendDenseItem(
      footprintNormalizationEvidence,
      option.option_id,
      `${Number(option.width_inches).toFixed(1)}x${Number(option.height_inches).toFixed(1)}in count=${option.count}`,
    );
  }
  for (const match of payload.matches || []) {
    appendDenseItem(
      footprintNormalizationEvidence,
      match.feature_id || match.element_id,
      `${match.option_id} ${match.status} ${match.review_reason} rot=${match.rotation_degrees} delta=${Number(match.dimension_delta_inches).toFixed(2)}in x=${Number(match.width_delta_inches).toFixed(2)}in y=${Number(match.height_delta_inches).toFixed(2)}in`,
    );
  }
  for (const code of payload.warning_codes || []) {
    appendDenseItem(footprintNormalizationEvidence, "Warning", code);
  }
}

function renderTerrainSymmetry(payload) {
  terrainSymmetryEvidence.replaceChildren();
  appendDenseItem(terrainSymmetryEvidence, "Status", payload.status || "warning");
  appendDenseItem(
    terrainSymmetryEvidence,
    "Method",
    payload.extraction_method || TERRAIN_SYMMETRY_METHOD,
  );
  appendDenseItem(terrainSymmetryEvidence, "Kind", payload.symmetry_kind || "rotational_180");
  appendDenseItem(
    terrainSymmetryEvidence,
    "Matched",
    `${payload.matched_feature_count}/${payload.feature_count}`,
  );
  const residual =
    payload.max_residual_inches === null || payload.max_residual_inches === undefined
      ? "n/a"
      : `${Number(payload.max_residual_inches).toFixed(2)}in`;
  appendDenseItem(terrainSymmetryEvidence, "Max residual", residual);
  if ((payload.unmatched_feature_ids || []).length) {
    appendDenseItem(
      terrainSymmetryEvidence,
      "Unmatched",
      payload.unmatched_feature_ids.join(", "),
    );
  }
  for (const match of payload.matches || []) {
    appendDenseItem(
      terrainSymmetryEvidence,
      match.feature_id,
      `${match.status} mirror=${match.mirrored_feature_id || "none"} residual=${Number(match.residual_inches).toFixed(2)}in`,
    );
  }
}

function processStepLabel(code) {
  switch (code) {
    case "standard_terrain_options":
      return "Source footprint catalog";
    case "image_extraction":
      return "Map extraction";
    case "grid_snap":
      return "Grid snap";
    case "measurement_corner_check":
      return "Measurement gate";
    case "symmetry_candidate_check":
      return "Symmetry gate";
    case "final_reconciliation":
      return "Final layout gate";
    default:
      return code;
  }
}

function processStepStatus(code, payload) {
  switch (code) {
    case "measurement_corner_check":
      return payload.final_measurement_status || payload.measurement_status || "unavailable";
    case "symmetry_candidate_check":
      return payload.final_symmetry_status || payload.symmetry_status || "warning";
    case "final_reconciliation":
      return payload.status || "warning";
    case "standard_terrain_options":
      return (payload.standard_options || []).length ? "available" : "unavailable";
    case "image_extraction":
    case "grid_snap":
      return payload.layout_id && payload.source_document_id ? "available" : "unavailable";
    default:
      return "";
  }
}

function renderReconciliationProcess(payload) {
  reconciliationProcess.replaceChildren();
  const steps = payload.process_steps || [];
  steps.forEach((code, index) => {
    const step = window.document.createElement("div");
    const numberNode = window.document.createElement("span");
    const labelNode = window.document.createElement("strong");
    const codeNode = window.document.createElement("small");
    step.className = "process-step";
    numberNode.textContent = String(index + 1);
    labelNode.textContent = processStepLabel(code);
    codeNode.textContent = `${code} ${processStepStatus(code, payload)}`.trim();
    step.append(numberNode, labelNode, codeNode);
    reconciliationProcess.appendChild(step);
  });
}

function renderTerrainReconciliation(payload) {
  renderReconciliationProcess(payload);
  terrainReconciliationEvidence.replaceChildren();
  appendDenseItem(terrainReconciliationEvidence, "Status", payload.status || "warning");
  appendDenseItem(
    terrainReconciliationEvidence,
    "Method",
    payload.extraction_method || TERRAIN_RECONCILIATION_METHOD,
  );
  appendDenseItem(
    terrainReconciliationEvidence,
    "Raw measurement",
    payload.measurement_status || "unavailable",
  );
  appendDenseItem(
    terrainReconciliationEvidence,
    "Raw symmetry",
    payload.symmetry_status || "warning",
  );
  appendDenseItem(
    terrainReconciliationEvidence,
    "Final measurement",
    payload.final_measurement_status || "unavailable",
  );
  appendDenseItem(
    terrainReconciliationEvidence,
    "Final symmetry",
    payload.final_symmetry_status || "warning",
  );
  appendDenseItem(
    terrainReconciliationEvidence,
    "Viable candidates",
    String(payload.viable_alternative_count || 0),
  );
  if ((payload.unresolved_feature_ids || []).length) {
    appendDenseItem(
      terrainReconciliationEvidence,
      "Unresolved",
      payload.unresolved_feature_ids.join(", "),
    );
  }
  for (const option of payload.standard_options || []) {
    const templates = (option.template_ids || []).length
      ? ` templates=${option.template_ids.join(",")}`
      : "";
    appendDenseItem(
      terrainReconciliationEvidence,
      option.option_id,
      `${Number(option.width_inches).toFixed(1)}x${Number(option.height_inches).toFixed(1)}in source=${option.source_kind || "layout_geometry"} evidence=${option.dimension_evidence_count || 0} count=${option.count} dense=${option.dense_feature_count} dense wall candidates=${option.wall_segment_count}${templates}`,
    );
  }
  for (const check of payload.measurement_checks || []) {
    appendDenseItem(
      terrainReconciliationEvidence,
      check.feature_id,
      `${check.status} corners=${check.verified_corner_count} ${check.review_reason}`,
    );
  }
  for (const alternative of payload.alternatives || []) {
    appendDenseItem(
      terrainReconciliationEvidence,
      `${alternative.feature_id} viable candidate`,
      `${alternative.status} ${alternative.review_reason} bounds=${formatBounds(alternative.proposed_bounds_inches)} measurement=${alternative.measurement_status} residual=${Number(alternative.symmetry_residual_inches).toFixed(2)}in`,
    );
  }
  for (const code of payload.warning_codes || []) {
    appendDenseItem(terrainReconciliationEvidence, "Warning", code);
  }
}

function renderVisualSanity(payload) {
  visualSanityEvidence.replaceChildren();
  appendDenseItem(visualSanityEvidence, "Status", payload.status || "unavailable");
  appendDenseItem(
    visualSanityEvidence,
    "Method",
    payload.extraction_method || "event-companion-cv-sanity-v1",
  );
  const advisoryStatus = payload.vision_advisory ? payload.vision_advisory.status : "not_run";
  appendDenseItem(visualSanityEvidence, "Vision", advisoryStatus);
  for (const check of payload.checks || []) {
    const residual =
      check.max_residual_inches === null || check.max_residual_inches === undefined
        ? "n/a"
        : `${Number(check.max_residual_inches).toFixed(2)}in`;
    appendDenseItem(
      visualSanityEvidence,
      check.code,
      `${check.status} ${check.match_count}/${check.expected_count} residual=${residual}`,
    );
  }
}

function renderFeatureProvenance(feature, point = null) {
  featureProvenance.replaceChildren();
  if (!feature) {
    const suffix = point ? ` at ${point.x}, ${point.y}` : "";
    featureProvenance.textContent = `No feature selected${suffix}.`;
    return;
  }
  const blockers = state.layout.blockers.filter(
    (blocker) => blocker.feature_id === feature.feature_id,
  );
  const reviewCodes = state.layout.validation_records
    .filter((record) => record.severity === "warning")
    .map((record) => `${record.code}:${record.review_status}`);
  appendDenseItem(featureProvenance, "Feature", feature.feature_id);
  appendDenseItem(featureProvenance, "Label", feature.label);
  appendDenseItem(featureProvenance, "Category", feature.terrain_category);
  appendDenseItem(featureProvenance, "blocker count", String(blockers.length));
  appendDenseItem(featureProvenance, "Footprint points", String(feature.footprint.points.length));
  appendDenseItem(featureProvenance, "Document", state.layout.provenance.source_document_id);
  appendDenseItem(featureProvenance, "Page", String(state.layout.provenance.source_page));
  appendDenseItem(featureProvenance, "Method", state.layout.provenance.extraction_method);
  appendDenseItem(
    featureProvenance,
    "Layout warnings",
    reviewCodes.length ? reviewCodes.join(", ") : "not_required",
  );
}

function renderSelectedFeatureProvenance() {
  renderFeatureProvenance(selectedFeature());
}

async function loadVisualSanity(layoutId) {
  visualSanityEvidence.textContent = "Loading sanity evidence.";
  try {
    const payload = await getJson(`/api/layouts/${layoutId}/visual-sanity`);
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderVisualSanity(payload);
  } catch (error) {
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderError(visualSanityEvidence, error);
  }
}

async function loadFootprintNormalization(layoutId) {
  footprintNormalizationEvidence.textContent = "Loading normalization evidence.";
  try {
    const payload = await getJson(`/api/layouts/${layoutId}/footprint-normalization`);
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderFootprintNormalization(payload);
  } catch (error) {
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderError(footprintNormalizationEvidence, error);
  }
}

async function loadTerrainSymmetry(layoutId) {
  terrainSymmetryEvidence.textContent = "Loading symmetry evidence.";
  try {
    const payload = await getJson(`/api/layouts/${layoutId}/terrain-symmetry`);
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderTerrainSymmetry(payload);
  } catch (error) {
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderError(terrainSymmetryEvidence, error);
  }
}

async function loadTerrainReconciliation(layoutId) {
  reconciliationProcess.textContent = "Loading process evidence.";
  terrainReconciliationEvidence.textContent = "Loading reconciliation evidence.";
  try {
    const payload = await getJson(`/api/layouts/${layoutId}/terrain-reconciliation`);
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderTerrainReconciliation(payload);
  } catch (error) {
    if (!state.layout || state.layout.layout_id !== layoutId) return;
    renderError(reconciliationProcess, error);
    renderError(terrainReconciliationEvidence, error);
  }
}

function formatBounds(bounds) {
  return bounds.map((value) => Number(value).toFixed(1)).join(", ");
}

function renderLayoutMetadata() {
  layoutMetadata.replaceChildren();
  if (!state.layout) return;
  appendDenseItem(layoutMetadata, "Status", state.layout.validation_status);
  appendDenseItem(layoutMetadata, "Document", state.layout.provenance.source_document_id);
  appendDenseItem(layoutMetadata, "Page", String(state.layout.provenance.source_page));
  appendDenseItem(layoutMetadata, "Method", state.layout.provenance.extraction_method);
}

function clearSourceUnderlayImage() {
  if (state.sourceUnderlayObjectUrl) URL.revokeObjectURL(state.sourceUnderlayObjectUrl);
  state.sourceUnderlayObjectUrl = null;
  state.sourceUnderlayImage = null;
}

function isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId) {
  return (
    state.layout &&
    state.layout.layout_id === layoutId &&
    sourceUnderlayToggle.checked &&
    sourceUnderlayRequestId === state.sourceUnderlayRequestId
  );
}

async function loadSourceUnderlay(layoutId) {
  state.sourceUnderlayRequestId += 1;
  const sourceUnderlayRequestId = state.sourceUnderlayRequestId;
  clearSourceUnderlayImage();
  if (!sourceUnderlayToggle.checked) {
    sourceUnderlayStatus.textContent = "Underlay off";
    return;
  }
  sourceUnderlayStatus.textContent = "Loading underlay";
  let objectUrl = null;
  try {
    const response = await fetch(`/api/layouts/${layoutId}/source-underlay.png`);
    if (!isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)) return;
    if (!response.ok) {
      sourceUnderlayStatus.textContent = "Underlay unavailable";
      return;
    }
    const blob = await response.blob();
    if (!isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)) return;
    objectUrl = URL.createObjectURL(blob);
    const image = new Image();
    await new Promise((resolve, reject) => {
      image.addEventListener("load", resolve, { once: true });
      image.addEventListener("error", reject, { once: true });
      image.src = objectUrl;
    });
    if (!isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    state.sourceUnderlayObjectUrl = objectUrl;
    state.sourceUnderlayImage = image;
    sourceUnderlayStatus.textContent = "Underlay visible";
  } catch (_error) {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    if (!isCurrentSourceUnderlayRequest(layoutId, sourceUnderlayRequestId)) return;
    sourceUnderlayStatus.textContent = "Underlay unavailable";
  }
}

function renderValidation() {
  validationPanel.replaceChildren();
  const records = state.layout.validation_records;
  if (!records.length) {
    validationPanel.textContent = "No validation records.";
    return;
  }
  for (const record of records) {
    const item = window.document.createElement("div");
    const labelNode = window.document.createElement("span");
    const valueNode = window.document.createElement("strong");
    const reviewStatus =
      record.review_status === "accepted" ? "accepted_with_warnings" : record.review_status;
    item.className = "dense-item validation-item";
    labelNode.textContent = record.code;
    valueNode.textContent = `${record.severity} ${reviewStatus || "not_required"}`;
    item.append(labelNode, valueNode);
    validationPanel.appendChild(item);
  }
}

async function loadLayout(layoutId) {
  const [payload, matches] = await Promise.all([
    getJson(`/api/layouts/${layoutId}`),
    getJson(`/api/layouts/${layoutId}/footprint-matches`),
  ]);
  state.layout = payload.layout;
  state.layoutHash = payload.layout_hash;
  state.selectedPoints = [];
  state.selectedFeatureId = null;
  state.heatmap = null;
  losResult.textContent = `Loaded ${state.layout.name}\n${state.layoutHash}`;
  analysisResult.textContent = "Run heatmap, exposure, or terrain coverage.";
  await loadSourceUnderlay(layoutId);
  renderLayoutMetadata();
  renderValidation();
  renderTerrainSemantics();
  renderFeatureProvenance(null);
  renderFootprintMatches(matches);
  renderBoard();
  void loadFootprintNormalization(layoutId);
  void loadTerrainSymmetry(layoutId);
  void loadTerrainReconciliation(layoutId);
  void loadVisualSanity(layoutId);
}

async function initialize() {
  const [layouts, sources, footprints] = await Promise.all([
    getJson("/api/layouts"),
    getJson("/api/sources"),
    getJson("/api/extraction/terrain-footprints"),
  ]);
  renderSources(sources);
  renderFootprintEvidence(footprints);
  void loadRulesEvidence();
  layoutSelect.replaceChildren();
  for (const layout of layouts.layouts) {
    const option = window.document.createElement("option");
    option.value = layout.layout_id;
    option.textContent = formatLayoutOption(layout);
    layoutSelect.appendChild(option);
  }
  await loadLayout(layouts.layouts[0].layout_id);
}

function formatLayoutOption(layout) {
  const source = layout.source === "extracted" ? "extracted" : "fixture";
  const page = layout.source === "extracted" && layout.source_page ? ` p${layout.source_page}` : "";
  const status = layout.validation_status ? ` ${layout.validation_status}` : "";
  return `${layout.name} (${source}${page}${status})`;
}

canvas.addEventListener("click", (event) => {
  void runPanelAction(losResult, async () => {
    if (!state.layout) return;
    const boardPoint = canvasToBoard(event);
    if (interactionMode.value === "inspect") {
      const feature = featureAtPoint(boardPoint);
      state.selectedFeatureId = feature ? feature.feature_id : null;
      renderFeatureProvenance(feature, boardPoint);
      renderBoard();
      return;
    }
    state.selectedPoints.push(boardPoint);
    if (state.selectedPoints.length > 2) state.selectedPoints.shift();
    renderBoard();
    if (state.selectedPoints.length === 1) {
      losResult.textContent = `Source selected at ${JSON.stringify(state.selectedPoints[0])}`;
      return;
    }
    if (state.selectedPoints.length === 2) {
      const payload = await postJson(`/api/layouts/${state.layout.layout_id}/los`, {
        source: state.selectedPoints[0],
        target: state.selectedPoints[1],
        source_base_diameter: Number(baseDiameter.value),
        target_base_diameter: Number(baseDiameter.value),
        boundary_sample_count: 16,
      });
      losResult.textContent = JSON.stringify(payload, null, 2);
    }
  });
});

layoutSelect.addEventListener("change", () => {
  void loadSelectedLayout();
});

loadLayoutButton.addEventListener("click", () => {
  void loadSelectedLayout();
});

sourceUnderlayToggle.addEventListener("change", () => {
  void runPanelAction(losResult, async () => {
    if (!state.layout) return;
    await loadSourceUnderlay(state.layout.layout_id);
    renderBoard();
  });
});

async function loadSelectedLayout() {
  void runPanelAction(losResult, async () => {
    await loadLayout(layoutSelect.value);
  });
}

document.querySelector("#heatmap-button").addEventListener("click", () => {
  void runPanelAction(analysisResult, async () => {
    const payload = await postJson(`/api/layouts/${state.layout.layout_id}/heatmap`, {
      source_region: { x_min: 0, y_min: 0, x_max: state.layout.board.width, y_max: 10 },
      source_step: 10,
      target_grid: { x_min: 2, y_min: 4, x_max: state.layout.board.width - 2, y_max: 24, step: 10 },
    });
    state.heatmap = payload;
    analysisResult.textContent = JSON.stringify(payload, null, 2);
    renderBoard();
  });
});

document.querySelector("#exposure-button").addEventListener("click", () => {
  void runPanelAction(analysisResult, async () => {
    const payload = await postJson(`/api/layouts/${state.layout.layout_id}/exposure`, {
      deployment_zone_id: "attacker",
      movement_distance: Number(movementDistance.value),
      threat_region: { x_min: state.layout.board.width - 2, y_min: 20, x_max: state.layout.board.width - 2, y_max: 20 },
      sample_step: 10,
    });
    analysisResult.textContent = JSON.stringify(payload, null, 2);
  });
});

document.querySelector("#terrain-coverage-button").addEventListener("click", () => {
  void runPanelAction(analysisResult, async () => {
    const featureId = state.layout.terrain_features[0].feature_id;
    const payload = await postJson(`/api/layouts/${state.layout.layout_id}/terrain/${featureId}/coverage`, {
      source_region: { x_min: 2, y_min: 4, x_max: 2, y_max: 4 },
      target_grid: { x_min: state.layout.board.width - 2, y_min: 4, x_max: state.layout.board.width - 2, y_max: 4, step: 1 },
    });
    analysisResult.textContent = JSON.stringify(payload, null, 2);
  });
});

document.querySelector("#export-button").addEventListener("click", () => {
  void runPanelAction(analysisResult, async () => {
    const bundle = {
      layout_id: state.layout.layout_id,
      layout_hash: state.layoutHash,
      selected_points: state.selectedPoints,
      heatmap: state.heatmap,
    };
    analysisResult.textContent = JSON.stringify(bundle, null, 2);
  });
});

initialize().catch((error) => {
  document.querySelector("#status").textContent = error.message;
});
