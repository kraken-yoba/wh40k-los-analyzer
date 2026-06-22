# Phase 10.5 Deployment Map Rendering Housekeeping Spec

Date: 2026-06-22

## Roadmap Anchor

Phase 10 added the first Mission-Aware Deployment Toolkit slice through the Manual Deployment
Scorecard. The new scorecard and the older Deployment Exposure screen now duplicate the same
application-service map projection logic.

This Phase 10.5 housekeeping slice is behavior-preserving. It should reduce duplication without
changing user-facing outputs, geometry, toolkit results, or route contracts.

## Goal

Centralize the deployment exposure SVG projection used by `deployment_exposure_state(...)` and
`deployment_scorecard_state(...)` inside the shared application service layer.

## Supported In This Slice

- Add a private service-layer helper for rendering a deployment exposure payload as SVG.
- Use the helper from Deployment Exposure and Deployment Scorecard state builders.
- Preserve blocked behavior: blocked states render the base packet map with no tactical overlays.
- Preserve estimated behavior: valid states render the same candidate staging, LOS, threat, friendly
  base, and enemy source overlays as before.
- Add characterization coverage proving scorecard and exposure states share the same map projection
  for the same valid deployment inputs.
- Add current-output SVG hash characterization for page 9 and page 52 valid deployment inputs so
  the refactor cannot pass by changing both screens the same way.

## Explicitly Out Of Scope

- Geometry, renderer, SVG style, or CSS changes.
- Deployment-scorecard component/warning copy changes.
- New route, template, or desktop behavior.
- Mission, roster, rules, public-sheet, or source-ingestion work.
- Any new public data fetch, copied source content, screenshots, or generated artifacts.

## Acceptance Criteria

- The refactor is private to the application service layer.
- Existing toolkit result ids, input hashes, payloads, warnings, and block reasons are unchanged.
- Deployment Exposure and Deployment Scorecard valid map SVGs match for identical deployment inputs.
- Page 9 and page 52 valid map SVG hashes match the pre-refactor characterized hashes.
- Blocked scorecard and blocked exposure states do not render `safe-zone-outline`, `coverage-image`,
  or `threat-projection-image`.
- Web and desktop tests remain green.
- Browser QA confirms `/deployment-exposure` and `/deployment-scorecard` still render without
  traceback/internal-error text, custom JavaScript, or console warning/error logs.
