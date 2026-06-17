(function () {
  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function boardPointFromPointer(svg, event) {
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const matrix = svg.getScreenCTM();
    if (!matrix) {
      return null;
    }
    return point.matrixTransform(matrix.inverse());
  }

  function setupLosBaseDrag(form) {
    const svg = form.parentElement.querySelector('svg.map-svg');
    const base = svg ? svg.querySelector('[data-draggable-base="true"]') : null;
    const xInput = form.querySelector('input[name="x"]');
    const yInput = form.querySelector('input[name="y"]');
    const baseInput = form.querySelector('input[name="base"]');
    if (!svg || !base || !xInput || !yInput || !baseInput) {
      return;
    }

    const viewBox = svg.viewBox.baseVal;
    const boardWidth = Number(form.dataset.boardWidth || xInput.max || 44);
    const boardHeight = Number(form.dataset.boardHeight || yInput.max || 60);
    const scaleX = viewBox.width / boardWidth;
    const scaleY = viewBox.height / boardHeight;
    let dragging = false;
    let moved = false;

    function radiusInches() {
      return Math.max(Number(baseInput.value || 0) / 2, 0);
    }

    function constrainedCenter(boardX, boardY) {
      const radius = radiusInches();
      const minX = Math.min(radius, boardWidth / 2);
      const maxX = Math.max(boardWidth - radius, minX);
      const minY = Math.min(radius, boardHeight / 2);
      const maxY = Math.max(boardHeight - radius, minY);
      return {
        x: clamp(boardX, minX, maxX),
        y: clamp(boardY, minY, maxY),
      };
    }

    function updateBase(boardX, boardY) {
      const center = constrainedCenter(boardX, boardY);
      base.setAttribute('cx', (center.x * scaleX).toFixed(1));
      base.setAttribute('cy', ((boardHeight - center.y) * scaleY).toFixed(1));
      base.setAttribute('r', (radiusInches() * scaleX).toFixed(1));
      xInput.value = center.x.toFixed(2);
      yInput.value = center.y.toFixed(2);
      return center;
    }

    function syncBaseFromInputs() {
      updateBase(Number(xInput.value || 0), Number(yInput.value || 0));
    }

    function moveBase(event) {
      const local = boardPointFromPointer(svg, event);
      if (!local) {
        return;
      }
      const boardX = local.x / scaleX;
      const boardY = boardHeight - local.y / scaleY;
      updateBase(boardX, boardY);
      moved = true;
    }

    base.addEventListener('pointerdown', function (event) {
      dragging = true;
      moved = false;
      base.setPointerCapture(event.pointerId);
      base.classList.add('dragging');
      moveBase(event);
      event.preventDefault();
    });

    base.addEventListener('pointermove', function (event) {
      if (!dragging) {
        return;
      }
      moveBase(event);
      event.preventDefault();
    });

    function finishDrag(event) {
      if (!dragging) {
        return;
      }
      dragging = false;
      base.classList.remove('dragging');
      if (base.hasPointerCapture(event.pointerId)) {
        base.releasePointerCapture(event.pointerId);
      }
      if (moved) {
        form.requestSubmit();
      }
    }

    baseInput.addEventListener('input', syncBaseFromInputs);
    xInput.addEventListener('input', syncBaseFromInputs);
    yInput.addEventListener('input', syncBaseFromInputs);
    base.addEventListener('pointerup', finishDrag);
    base.addEventListener('pointercancel', finishDrag);
    syncBaseFromInputs();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.los-checker-form').forEach(setupLosBaseDrag);
  });
})();
