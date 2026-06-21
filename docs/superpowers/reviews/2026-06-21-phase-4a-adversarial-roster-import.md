# Phase 4A Adversarial Review - Roster Import Safety

Date: 2026-06-21

## Review Scope

Adversarial reviewers evaluate hostile input handling, protected-data/IP guardrails, source
authority separation, readiness wording, and QA adequacy for Phase 4A.

## Findings

Reviewer: `019ee97a-7851-7022-8617-8c6ecdd8845b`

Initial status: approve only quarantine/admission sub-slice; block direct roster/profile adapter
implementation.

- P1: do not implement roster/profile adapters until Phase 4 is split into quarantine/parse,
  canonical roster, and profile-resolution sub-slices with malicious archive/XML fixtures and
  artifact scans.
- P1: protected roster/profile/rules leakage is a release blocker.
- P1: community-data authority confusion is a release blocker for legality/points claims.
- P2: existing source/ref primitives need roster/archive import records carrying member path,
  compressed/uncompressed sizes, decompression ratio, parser version, schema version, selected XML
  hash, and quarantine status.
- P2: XML parsing needs `defusedxml` or an equivalent fail-closed gate that blocks DTD/entity
  attacks, external entities, and network access from parsed content.
- P3: pasted roster text and UI upload workflows should wait.

## Triage

- Accepted: Phase 4A is quarantine/admission plus shallow canonical snapshot only.
- Accepted: no profile resolution, official points, legality, downstream solver, pasted text, or UI
  in Phase 4A.
- Accepted: reject unsafe archives and XML before canonicalization.
- Accepted: add archive member metadata and selected XML hash to source records.
- Accepted: use a fail-closed pre-screen gate plus stdlib XML parser for this slice because
  `defusedxml` is not currently installed in the project venv.
- Accepted: tests must generate tiny synthetic fixtures in memory and avoid real roster/community
  data.

## Final Approval Gate

Final adversarial approval requires:

- Unsafe archive/XML inputs produce blocked results with no canonical army or overlays.
- Safe imports remain estimated local evidence, not trusted source authority.
- Costs remain as-presented snapshots, not official points.
- No protected text/raw data is staged.
- No web, desktop, LOS, rendering, or downstream solver behavior changed.

## Final Review

Reviewer: `019ee985-9f64-7c80-afec-f67ac382f36d`

Status: changes required.

- P1: excessive XML selection depth could crash through recursive extraction instead of returning a
  blocked `ToolkitResult`.
- P2: archive paths were normalized before enough raw checks, allowing names such as
  `safe/../evil.ros`, `C:evil.ros`, and `C:../evil.ros`.

Triage:

- Accepted: add depth-limit regression and block with `roster-xml-too-deep`.
- Accepted: check raw archive path components and colons before normalization.
- Accepted: add regressions for embedded traversal and Windows drive-qualified names.

## Final Re-Review

Reviewer: `019ee98c-29b8-7311-af5e-e45b6735a34c`

Status: changes required.

- P1: UTF-16LE/BE XML without a BOM still bypassed the XML safety gate because NUL-separated bytes
  did not contain the ASCII `encoding`, `DOCTYPE`, or `ENTITY` tokens.

Triage:

- Accepted: reject NUL-containing XML bytes before token scanning or parsing.
- Accepted: add explicit UTF-16LE and UTF-16BE no-BOM regressions.

## Final Re-Review 2

Reviewer: `019ee990-ee49-7d52-9795-b64b683da535`

Status: changes required.

- P1: selected `.ros` member reads could raise after archive metadata validation for corrupt
  payloads or unsupported compression methods.

Triage:

- Accepted: allowlist `ZIP_STORED` and `ZIP_DEFLATED`.
- Accepted: wrap selected member reads as blocked `archive-member-read-failed` results.
- Accepted: add corrupt payload and unsupported-compression regressions.

## ZIP Admission Hardening Reviews

Reviewers: `019ee99a-abb5-7273-a7d5-1bce78f0b2ff`,
`019ee9a2-6aaf-7322-bee9-6861c69deca0`,
`019ee9a8-7774-7791-ae6b-9fe71343ed80`,
`019ee9ae-3b04-7a20-99a2-e6445977e551`,
`019ee9b3-d5e0-7621-8ec5-ebd184b34aa2`,
`019ee9ba-47a6-7c43-8ac5-27f7f309406b`,
`019ee9c1-15af-7bb2-90ec-2f2890367271`,
`019ee9c8-2c47-7c50-949a-48e8b02fea82`

Status: changes required until final approval.

- P1: ZIP central-directory size metadata could be forged while the selected deflate stream
  inflated beyond `max_xml_bytes`.
- P1: local ZIP headers could disagree with central metadata for paths, encryption flags,
  compression methods, CRCs, sizes, local extra fields, data descriptor flags, and local payload
  spans.
- P1: unreferenced leading local entries, hidden bytes before the central directory, trailing bytes
  after EOCD, archive comments, member comments, central/local extra fields, and excessive directory
  entries were hidden admission paths.
- P2: unsafe directory entries were initially filtered before validation.

Triage:

- Accepted: replace selected `ZipFile.read()` with bounded local-entry reading for the selected
  roster member.
- Accepted: require local and central metadata agreement and reject data descriptors in Phase 4A.
- Accepted: require referenced local entries to cover the byte range from offset zero through the
  central directory with no hidden records or gaps.
- Accepted: reject archive comments, member comments, central extra fields, local extra fields,
  unsafe/payload-bearing directory entries, and member counts over the limit across all central
  entries.
- Accepted: keep directory entries allowed only as empty, fully validated folder markers.

## XML Admission Hardening Reviews

Reviewers: `019ee9ae-3b04-7a20-99a2-e6445977e551`,
`019ee9b3-d5e0-7621-8ec5-ebd184b34aa2`,
`019ee9c8-2c47-7c50-949a-48e8b02fea82`

Status: changes required until final approval.

- P1: URL tokens could be hidden with XML character references in attributes, namespaces, unused
  namespace declarations, comments, and processing instructions.

Triage:

- Accepted: keep the raw byte gate for DTD/entity/include/URL tokens.
- Accepted: reject XML comments and non-declaration processing instructions.
- Accepted: scan decoded element tags, attribute names, attribute values, text, tail, and namespace
  declarations via `ElementTree.iterparse(..., events=("start-ns",))`.

## Final Adversarial Approval

Reviewer: `019ee9ce-7261-7b23-8305-c58cf0beb084`

Status: approved.

- Critical: none.
- Important: none.
- Minor: none.
- Residual risks accepted for later phases: roster field values and filenames are caller-controlled
  strings and must be escaped/truncated/normalized before future UI or persistence work; XML
  hardening remains explicit pre-screening rather than `defusedxml`, which is acceptable for this
  no-network Phase 4A slice.
