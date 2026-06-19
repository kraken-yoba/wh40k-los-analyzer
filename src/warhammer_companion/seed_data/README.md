# Seed Data

This directory contains generated map-packet JSON used as bundled starter data
for standalone desktop builds.

The packet files are derived from the official Warhammer 40,000 Event Companion
terrain layout PDF listed in `warhammer_companion.ingestion.sources`. They are
not hand-authored rules text and should be regenerated from the public source
PDFs when the ingestion model changes.

Before a public release, confirm that redistributing these derived layout JSON
files is acceptable. If that is not acceptable, replace this bundle with a
first-run download/import flow that generates the same packets locally.
