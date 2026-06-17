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
    if (!svg || !base || !xInput || !yInput) {
      return;
    }

    const viewBox = svg.viewBox.baseVal;
    const boardWidth = Number(xInput.max || 44);
    const boardHeight = Number(yInput.max || 60);
    const scaleX = viewBox.width / boardWidth;
    const scaleY = viewBox.height / boardHeight;
    let dragging = false;
    let moved = false;

    function moveBase(event) {
      const local = boardPointFromPointer(svg, event);
      if (!local) {
        return;
      }
      const boardX = clamp(local.x / scaleX, 0, boardWidth);
      const boardY = clamp(boardHeight - local.y / scaleY, 0, boardHeight);
      base.setAttribute('cx', (boardX * scaleX).toFixed(1));
      base.setAttribute('cy', ((boardHeight - boardY) * scaleY).toFixed(1));
      xInput.value = boardX.toFixed(2);
      yInput.value = boardY.toFixed(2);
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

    base.addEventListener('pointerup', finishDrag);
    base.addEventListener('pointercancel', finishDrag);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.los-checker-form').forEach(setupLosBaseDrag);
  });
})();
