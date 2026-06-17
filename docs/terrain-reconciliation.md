# Terrain Reconciliation

The reconciler keeps source footprint evidence separate from map placement evidence.
The current app does not treat a plausible map-image rectangle as final until
the snapped placement passes both printed measurement checks and symmetry checks.
When explicit inch dimensions are not printed in the Terrain Area Footprints PDF
text layer, the source catalog is built from official source-template matches
across the extracted official Event Companion corpus rather than from only the
currently selected map.

```mermaid
flowchart LR
    A["Terrain Area Footprints PDF"] --> B["Source footprint catalog\nforms + Dense wall fragments"]
    C["Event Companion map page"] --> D["Map image/vector extraction\nlikely footprint placements"]
    D --> E["Snap corners to inch grid"]
    B --> F["Candidate option set\nsource-backed dimensions when available"]
    E --> G["Positioned corner measurements"]
    E --> H["One-to-one 180 degree symmetry\nmaximum-cardinality assignment"]
    F --> I["Cycle alternatives\nself-center + mirror partner"]
    G --> J["Final reconciliation gate"]
    H --> J
    I --> J
```

The two final evidence gates are parallel. A candidate that satisfies only one
gate remains warning-state evidence.

```mermaid
flowchart TB
    A["Snapped footprint candidate"] --> B{"All four corners match nearby printed edge measurements?"}
    A --> C{"One-to-one symmetric partner or valid self-center candidate?"}
    B -- "yes" --> D["Measurement passed"]
    B -- "no" --> E["Measurement warning"]
    C -- "yes" --> F["Symmetry passed"]
    C -- "no" --> G["Symmetry warning"]
    D --> H{"Both gates passed?"}
    F --> H
    E --> I["Unresolved warning"]
    G --> I
    H -- "yes" --> J["Resolved layout evidence"]
    H -- "no" --> I
```

Current boundary: viable alternatives are reported as candidate evidence but are
not silently applied to canonical geometry. Future builds can add a deterministic
promotion step once the footprint catalog has explicit source-backed dimensions
for every standard GW footprint option.
