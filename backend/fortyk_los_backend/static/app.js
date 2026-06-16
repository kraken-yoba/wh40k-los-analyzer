const canvas = document.querySelector("#board-canvas");
const context = canvas.getContext("2d");
const layoutSelect = document.querySelector("#layout-select");
const layoutMetadata = document.querySelector("#layout-metadata");
const sourceStatus = document.querySelector("#source-status");
const footprintEvidence = document.querySelector("#footprint-evidence");
const validationPanel = document.querySelector("#validation-panel");
const losResult = document.querySelector("#los-result");
const analysisResult = document.querySelector("#analysis-result");
const baseDiameter = document.querySelector("#base-diameter");
const movementDistance = document.querySelector("#movement-distance");
const FOOTPRINT_EXTRACTION_METHOD = "terrain-footprint-vector-v1";

const state = {
  layout: null,
  layoutHash: null,
  selectedPoints: [],
  heatmap: null,
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

function renderBoard() {
  if (!state.layout) return;
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#fffdf8";
  context.fillRect(0, 0, canvas.width, canvas.height);
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
    context.fillStyle = feature.movement_blocking ? "#b9c4a8" : "#d8d0c0";
    context.fill();
    context.strokeStyle = "#746a5c";
    context.lineWidth = 2;
    context.stroke();
  }

  for (const blocker of state.layout.blockers) {
    const start = boardToCanvas(blocker.start);
    const end = boardToCanvas(blocker.end);
    context.beginPath();
    context.moveTo(start.x, start.y);
    context.lineTo(end.x, end.y);
    context.strokeStyle = "#8f2f2f";
    context.lineWidth = 6;
    context.stroke();
  }

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

function renderValidation() {
  validationPanel.replaceChildren();
  const records = state.layout.validation_records;
  if (!records.length) {
    validationPanel.textContent = "No validation records.";
    return;
  }
  for (const record of records) {
    appendDenseItem(validationPanel, record.code, record.severity);
  }
}

async function loadLayout(layoutId) {
  const payload = await getJson(`/api/layouts/${layoutId}`);
  state.layout = payload.layout;
  state.layoutHash = payload.layout_hash;
  state.selectedPoints = [];
  state.heatmap = null;
  losResult.textContent = `Loaded ${state.layout.name}\n${state.layoutHash}`;
  analysisResult.textContent = "Run heatmap, exposure, or terrain coverage.";
  renderLayoutMetadata();
  renderValidation();
  renderBoard();
}

async function initialize() {
  const [layouts, sources, footprints] = await Promise.all([
    getJson("/api/layouts"),
    getJson("/api/sources"),
    getJson("/api/extraction/terrain-footprints"),
  ]);
  renderSources(sources);
  renderFootprintEvidence(footprints);
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
  const status = layout.validation_status ? ` ${layout.validation_status}` : "";
  return `${layout.name} (${source}${status})`;
}

canvas.addEventListener("click", (event) => {
  void runPanelAction(losResult, async () => {
    if (!state.layout) return;
    state.selectedPoints.push(canvasToBoard(event));
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
  void runPanelAction(losResult, async () => {
    await loadLayout(layoutSelect.value);
  });
});

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
