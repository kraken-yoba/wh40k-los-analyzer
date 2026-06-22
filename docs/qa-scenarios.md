# QA Scenarios

Date: 2026-06-18

These scripts define the web MVP baseline and the desktop parity target. The same scenarios should be run against the server-rendered web app, the development desktop app, and the packaged Windows desktop build.

## Common Preconditions

- Official Event Companion packets for pages 9-53 are available in the active app-data directory, or the ingestion workflow can generate them.
- The app has access to the official source PDFs in the configured raw-data directory for ingestion tests.
- Page 9 is used as the primary regression smoke packet because it exercises merged terrain groups, official dense feature labels, heatmap safe-zone outlines, and LOS checker overlays.
- Page 20 is used for multi-label dense-feature extraction regression coverage.
- Page 52 is used for diagonal terrain footprint and rotated dense-feature regression coverage.
- Web and desktop runs should use the same packet directory when parity is being checked.

## Roadmap Phase QA

Each player-toolkit roadmap phase must have a phase-specific QA pathway under `docs/superpowers/qa/` before implementation is considered complete. The pathway must be executable by a fresh subagent and must identify the required local data, exact commands, expected results, reviewer approval evidence, work-log evidence, and commit checks.

Every phase QA pathway should include consultant review and adversarial review gates. Any phase that uses mutable external data must include freshness/source-refresh checks for official rules and balance documents, public sheets, MFM data, roster formats, mission-pack data, community-pack data, and source timestamps. Runtime phases must include the standard Python checks plus targeted unit, integration, web, desktop, and packaging checks that match the files changed. Browser verification is required when web routes, controls, maps, rendered HTML, generated SVG, or visual layout behavior change. Computer Use verification is required when native Windows desktop behavior, OS dialogs, installers, or packaged app interactions change.

Phase QA must include page 9 and page 52 regression checks when map overlays, geometry, terrain, deployment, LOS, movement, threat, exposure, or mission-zone rendering behavior changes. A phase may skip Browser or Computer Use only when it documents that the phase is docs-only or otherwise has no runtime surface to exercise.

## Scenario 1: App Shell And Navigation

Steps:

1. Launch the app.
2. Open Settings.
3. Open Map Data.
4. Open Map Viewer.
5. Open LOS Heatmap.
6. Open LOS Checker.
7. Open Movement Reach.
8. Open Hidden Coverage.
9. Open Threat Range.
10. Open Deployment Exposure.

Expected result:

- Each screen opens without a blank page, crash, traceback, or missing navigation state.
- The active screen is visually identifiable.
- Core controls are visible without horizontal overflow at a normal desktop viewport/window size.
- Desktop and web labels use the same product vocabulary.

Automation:

- Web: browser DOM checks for screen headings, active navigation, and no horizontal overflow.
- Desktop: widget smoke checks for screen names and navigation actions.

Manual check:

- Resize the desktop window and confirm text, controls, and maps remain usable.

## Scenario 2: Settings And Backend Status

Steps:

1. Open Settings.
2. Inspect the Python backend status.
3. Inspect the Codex account/runtime status.
4. If available, start and cancel or complete the non-secret login flow.
5. If authenticated, run logout.

Expected result:

- Python ingestion backend reports ready.
- Codex runtime state is readable and sanitized.
- Missing runtime, missing authentication, and login errors are presented as user-facing status, not stack traces.
- No auth files, tokens, API keys, or browser-session data are displayed.

Automation:

- Web and desktop checks for expected labels and absence of secret-like strings.
- Unit tests for sanitized status messages.

Manual check:

- Browser/device-code login and logout behavior.

## Scenario 3: Map Data And Official Sources

Steps:

1. Open Map Data.
2. Inspect official source status.
3. Confirm packet list contains official layouts after ingestion.
4. Confirm packet rows show name, source, player dispositions, missions, and layout variant.
5. Open a packet from the list.

Expected result:

- Official source URLs and extraction stages are visible.
- All generated official packets for pages 9-53 are discoverable.
- Opening a packet navigates to Map Viewer with that packet selected.
- Packet metadata is consistent with the Event Companion layout organization.

Automation:

- Repository/HTTP/widget tests for packet count, metadata, and navigation target.

Manual check:

- External PDF/source link behavior in the desktop app.

## Scenario 4: Ingest And Classify

Steps:

1. Use a clean or known fixture app-data directory.
2. Trigger official ingestion.
3. Wait for completion.
4. Inspect the ingestion report.
5. Open page 9, page 20, and page 52 in Map Viewer.

Expected result:

- UI remains responsive or shows a clear busy/progress state.
- Ingestion produces 45 official packets for pages 9-53.
- Packet validation passes.
- Page 20 contains two each of official dense feature codes `AB`, `CD`, `EF`, and `GH`.
- Page 52 diagonal footprints have dense features aligned with the footprint angle.
- Validation failures and extraction errors are surfaced to the user.

Automation:

- CLI validation, packet JSON assertions, and service-level tests.
- Desktop worker tests once ingestion is wired to Qt.

Manual check:

- Long-running job responsiveness and user-facing error text.

## Scenario 5: Delete Packet

Steps:

1. Choose a generated, deletable packet.
2. Delete it.
3. Return to Map Data.
4. Check packet selectors on Viewer, Heatmap, and LOS Checker.

Expected result:

- The packet JSON is removed.
- The packet disappears from all selectors.
- A success or failure message is shown.
- Sample/fallback packets remain protected from accidental deletion.

Automation:

- Temp-directory repository tests.
- Web/desktop UI checks for selector refresh.

Manual check:

- Desktop confirmation dialog text and cancellation behavior.

## Scenario 6: Map Viewer Packet Inspection

Steps:

1. Open Map Viewer.
2. Select Player A disposition, Player B disposition, and terrain layout A/B/C.
3. Load page 9 by choosing Take and Hold / Take and Hold / Layout A.
4. Confirm the packet summary above the map.
5. Inspect terrain, dense, light/review, and deployment counts.
6. Load page 20 by choosing Take and Hold / Reconnaissance / Layout C.
7. Load page 52 by choosing Priority Assets / Priority Assets / Layout B.

Expected result:

- The selected packet persists after load.
- Viewer, Heatmap, and LOS Checker expose the same Player A / Player B / terrain layout selector model.
- Force-disposition matchup, primary-mission matchup, layout variant, and Event Companion source page are visible.
- The map renders board, terrain footprints, dense features, light/review features, labels, and deployment zones.
- Counts match the loaded packet.
- Page 52 shows diagonal dense L-shaped features following diagonal footprints.

Automation:

- Web DOM and generated SVG checks.
- Desktop widget checks plus image/snapshot comparison.

Manual check:

- Visual plausibility, map orientation, and official terrain feature symmetry.

## Scenario 7: LOS Heatmap

Steps:

1. Open LOS Heatmap.
2. Select page 9.
3. Generate attacker heatmap from deployment edge with offsets 0, 6, and 12.
4. Switch to defender and repeat at 6.
5. Switch source mode to full deployment zone.

Expected result:

- Heatmap renders as a pixel-resolution raster overlay.
- Own deployment or deployment-plus-offset risk area is blanked out.
- Fully obscured safe zones are outlined.
- Edge offset uses rounded distance from corners, not a stepped copy of the deployment edge.
- Switching packet, zone, source, or offset updates the rendered map.

Automation:

- SVG/PNG alpha checks for blanked own-risk area.
- DOM/widget checks for selected controls and safe-zone outline count.

Manual check:

- Color readability and tactical plausibility.

## Scenario 8: LOS Checker Base Placement

Steps:

1. Open LOS Checker.
2. Select page 9.
3. Enter a normal base center and 1.57 inch base diameter.
4. Enter out-of-bounds coordinates.
5. Test base diameters 0.5, 1.57, and 6.
6. Test a base touching a terrain footprint.

Expected result:

- Base center clamps so the entire base fits on the board.
- Coverage raster, base marker, clear rays, and blocked rays render.
- A base touching a terrain footprint can see through that footprint, but dense features on it still block LOS.
- Terrain footprints and dense features create shadows when the base is not touching them.
- Changing packet, base size, or position updates the overlay.

Automation:

- Geometry tests for clamping, touching, shadows, and dense blockers.
- Web/desktop rendered overlay presence checks.

Manual check:

- Visual ray plausibility around merged/touching footprints.

## Scenario 9: Deployment Exposure Diagnostics

Steps:

1. Open Deployment Exposure.
2. Select page 9.
3. Use the attacker deployment zone with a friendly 1.57 inch base and enemy 1.57 inch base.
4. Generate a threat-and-LOS diagnostic.
5. Repeat for page 52 with the defender deployment zone.
6. Test an invalid friendly base diameter.

Expected result:

- The map renders candidate staging centers, enemy threat projection, enemy LOS projection, the
  friendly base, and the enemy source base.
- The placement summary uses cautious diagnostic wording and does not claim legal, recommended,
  guaranteed, or optimized placement.
- Invalid manual inputs are blocked with user-facing messages and no diagnostic overlays.
- Page 9 and page 52 both render without losing deployment-zone, dense-feature, terrain, or overlay
  geometry.

Automation:

- Service and web tests for readiness, warning copy, selected controls, overlay classes, and POST
  preservation.
- Desktop smoke checks for screen presence and rendered SVG.
- Browser QA checks `/deployment-exposure` plus mandatory page 9 and page 52 regression query
  paths.

Manual check:

- Visual plausibility of candidate staging regions, enemy threat/LOS overlap, and warning copy.

## Scenario 10: Cross-Workflow Consistency

Steps:

1. Load the same packet in Viewer, Heatmap, LOS Checker, Movement Reach, Hidden Coverage, Threat
   Range, and Deployment Exposure.
2. Compare packet labels, page metadata, board dimensions, terrain shapes, deployment zones, and blocker counts.
3. Repeat for page 9 and page 52.

Expected result:

- The same packet model drives every workflow.
- Terrain and dense feature geometry do not diverge between screens.
- Heatmap, LOS checker, movement, threat, hidden coverage, and deployment exposure tools use the
  documented blocker semantics for their selected assumptions.

Automation:

- Shared application-service assertions.
- Snapshot or image hash comparison where rendering should match.

Manual check:

- Side-by-side web/desktop rendering comparison for known complex layouts.

## Scenario 11: Packaged Windows Desktop Smoke

Steps:

1. Install or unzip the Windows desktop build on a clean profile with no Python installed.
2. Launch from the Start Menu or desktop shortcut.
3. Run the built-in smoke command if available.
4. Open Viewer, Heatmap, LOS Checker, Movement Reach, Hidden Coverage, Threat Range, and Deployment
   Exposure with bundled or generated packet data.
5. Trigger a non-destructive settings/status check.

Expected result:

- The app starts without requiring Python, a local repo checkout, or development paths.
- App data is written under a user-writable application-data directory or a documented portable directory.
- Missing PDFs, missing network, and missing Codex auth are handled gracefully.
- Bundled Codex runtime dependencies resolve or fail with sanitized status.
- The packaged build can render page 9 and page 52 maps.

Automation:

- GitHub Actions Windows artifact smoke command.
- Silent installer smoke test where CI runner tooling supports it.

Manual check:

- Installer copy, Start Menu shortcut, uninstall entry, SmartScreen/signing warning, high-DPI rendering, and path-with-spaces behavior.
