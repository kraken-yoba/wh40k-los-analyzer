from __future__ import annotations

import hashlib

from warhammer_companion.application.roster_import import build_roster_import_result_from_bytes


def _roster_with_snapshot_profiles(
    *,
    characteristic_value: str = "6",
    rule_description: str = "Synthetic local test note.",
) -> bytes:
    return (
        f"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="Synthetic Army" gameSystemId="game-system-1"
  gameSystemName="Synthetic System">
  <costs>
    <cost id="roster-cost-1" name="pts" typeId="points" value="200"/>
  </costs>
  <forces>
    <force id="force-1" name="Main Force" catalogueId="catalogue-1"
      catalogueName="Synthetic Catalogue">
      <selections>
        <selection id="unit-1" name="Example Unit" type="unit">
          <costs>
            <cost id="cost-1" name="pts" typeId="points" value="125"/>
          </costs>
          <profiles>
            <profile id="profile-1" name="Example Unit Profile" typeId="profile-type-1"
              typeName="Synthetic Unit">
              <characteristics>
                <characteristic id="characteristic-1" name="M" typeId="movement">
                  {characteristic_value}
                </characteristic>
              </characteristics>
            </profile>
          </profiles>
          <rules>
            <rule id="rule-1" name="Synthetic Rule">
              <description>{rule_description}</description>
            </rule>
          </rules>
          <selections>
            <selection id="model-1" name="Example Model" type="model">
              <costs>
                <cost id="cost-2" name="pts" typeId="points" value="25"/>
              </costs>
              <profiles>
                <profile id="profile-2" name="Example Model Profile" typeId="profile-type-2"
                  typeName="Synthetic Model">
                  <characteristics>
                    <characteristic id="characteristic-2" name="T" typeId="toughness">
                      4
                    </characteristic>
                  </characteristics>
                </profile>
              </profiles>
            </selection>
          </selections>
        </selection>
        <selection id="upgrade-1" name="Example Upgrade" type="upgrade"/>
      </selections>
    </force>
  </forces>
</roster>
"""
    ).encode()


def _roster_with_duplicate_selection_ids() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="Synthetic Army">
  <forces>
    <force id="force-1" name="Main Force">
      <selections>
        <selection id="duplicate-selection" name="First Copy" type="unit"/>
        <selection id="duplicate-selection" name="Second Copy" type="unit"/>
      </selections>
    </force>
  </forces>
</roster>
"""


def _multi_force_roster() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="Synthetic Army">
  <forces>
    <force id="force-1" name="Main Force">
      <selections><selection id="unit-1" name="Unit 1" type="unit"/></selections>
    </force>
    <force id="force-2" name="Second Force">
      <selections><selection id="unit-2" name="Unit 2" type="unit"/></selections>
    </force>
  </forces>
</roster>
"""


def _roster_with_fragmented_rule_description() -> bytes:
    fragments = "".join(f"<fragment>{'x' * 1000}</fragment>" for _ in range(3))
    return (
        f"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="Synthetic Army">
  <forces>
    <force id="force-1" name="Main Force">
      <selections>
        <selection id="unit-1" name="Example Unit" type="unit">
          <rules>
            <rule id="rule-1" name="Synthetic Rule">
              <description>{fragments}</description>
            </rule>
          </rules>
        </selection>
      </selections>
    </force>
  </forces>
</roster>
"""
    ).encode()


def _roster_with_fragmented_characteristic_value() -> bytes:
    fragments = "".join(f"<fragment>{'x' * 1000}</fragment>" for _ in range(3))
    return (
        f"""<?xml version="1.0" encoding="UTF-8"?>
<roster id="roster-1" name="Synthetic Army">
  <forces>
    <force id="force-1" name="Main Force">
      <selections>
        <selection id="unit-1" name="Example Unit" type="unit">
          <profiles>
            <profile id="profile-1" name="Example Profile" typeId="profile-type-1">
              <characteristics>
                <characteristic id="characteristic-1" name="Synthetic" typeId="synthetic">
                  {fragments}
                </characteristic>
              </characteristics>
            </profile>
          </profiles>
        </selection>
      </selections>
    </force>
  </forces>
</roster>
"""
    ).encode()


def _non_selection_deep_roster(depth: int) -> bytes:
    opening = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<roster id="roster-1" name="Synthetic Army">',
    ]
    closing = ["</roster>"]
    for index in range(depth):
        opening.append(f'<metadata id="metadata-{index}">')
        closing.append("</metadata>")
    return "".join((*opening, *reversed(closing))).encode()


def test_import_enriches_canonical_index_and_snapshot_profiles() -> None:
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(),
        source_kind="ros_xml",
        source_ref_ids=("local-file:synthetic",),
    )

    assert result.readiness == "estimated"
    assert not result.overlays
    assert not result.allows_recommendation_language()

    assert result.payload.army is not None
    index = result.payload.roster_index
    assert index is not None
    assert index.roster_id == "roster-1"
    assert index.selection_count == 3
    assert index.top_level_selection_count == 2
    assert [(entry.selection_type, entry.count) for entry in index.selection_type_counts] == [
        ("model", 1),
        ("unit", 1),
        ("upgrade", 1),
    ]

    unit_entry = next(entry for entry in index.entries if entry.selection_id == "unit-1")
    model_entry = next(entry for entry in index.entries if entry.selection_id == "model-1")
    assert unit_entry.selection_key
    assert unit_entry.source_path == "roster/force-1/unit-1"
    assert unit_entry.depth == 0
    assert unit_entry.child_count == 1
    assert unit_entry.cost_count == 1
    assert unit_entry.profile_count == 1
    assert unit_entry.rule_count == 1
    assert model_entry.source_path == "roster/force-1/unit-1/model-1"
    assert model_entry.depth == 1
    assert model_entry.profile_count == 1

    pack = result.payload.snapshot_profile_pack
    assert pack is not None
    assert pack.readiness == "estimated"
    assert pack.source_policy == "local_evidence"
    assert pack.authority == "not_source_authority"
    assert pack.source_ref_ids == ("local-file:synthetic",)
    assert len(pack.profiles) == 2
    assert len(pack.rules) == 1
    assert pack.profiles[0].source_path == "roster/force-1/unit-1/profile-1"
    assert pack.profiles[0].characteristics[0].value == "6"
    assert pack.profiles[0].characteristics[0].value_length == 1
    assert pack.profiles[0].characteristics[0].value_sha256 == hashlib.sha256(b"6").hexdigest()
    assert pack.profiles[0].characteristics[0].source_ref_ids == ("local-file:synthetic",)
    assert pack.profiles[1].source_path == "roster/force-1/unit-1/model-1/profile-2"
    assert pack.profiles[1].characteristics[0].value == "4"
    assert pack.profiles[1].source_ref_ids == ("local-file:synthetic",)
    assert pack.profiles[1].characteristics[0].source_ref_ids == ("local-file:synthetic",)

    army = result.payload.army
    assert army is not None
    assert army.selections[0].profiles[0].source_ref_ids == ("local-file:synthetic",)
    assert army.selections[0].profiles[0].characteristics[0].source_ref_ids == (
        "local-file:synthetic",
    )
    nested_model = army.selections[0].children[0]
    assert nested_model.profiles[0].source_ref_ids == ("local-file:synthetic",)
    assert nested_model.profiles[0].characteristics[0].source_ref_ids == ("local-file:synthetic",)


def test_rule_descriptions_are_hashed_not_retained_as_canonical_text() -> None:
    description = "Synthetic local test note."
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(rule_description=description),
        source_kind="ros_xml",
    )

    pack = result.payload.snapshot_profile_pack
    assert pack is not None
    assert len(pack.rules) == 1
    rule = pack.rules[0]
    assert rule.raw_id == "rule-1"
    assert rule.name == "Synthetic Rule"
    assert rule.source_path == "roster/force-1/unit-1/rule-1"
    assert rule.description_length == len(description)
    assert rule.description_sha256 == hashlib.sha256(description.encode("utf-8")).hexdigest()
    assert not hasattr(rule, "description")


def test_profile_candidates_remain_unresolved_local_evidence() -> None:
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(),
        source_kind="ros_xml",
        source_ref_ids=("local-file:synthetic",),
    )

    index = result.payload.roster_index
    assert index is not None
    candidates = {candidate.selection_id: candidate for candidate in index.profile_candidates}

    assert set(candidates) == {"unit-1", "model-1", "upgrade-1"}
    assert candidates["unit-1"].resolution_status == "unresolved"
    assert candidates["unit-1"].source_policy == "local_evidence"
    assert candidates["unit-1"].points_authority == "not_official_points"
    assert candidates["unit-1"].mechanics_authority == "not_profile_resolution"
    assert candidates["unit-1"].profile_ids == ("profile-1",)
    assert candidates["unit-1"].rule_ids == ("rule-1",)
    assert candidates["unit-1"].cost_ids == ("cost-1",)
    assert candidates["model-1"].resolution_status == "unresolved"
    assert candidates["model-1"].profile_ids == ("profile-2",)
    assert candidates["upgrade-1"].resolution_status == "unresolved"
    assert candidates["upgrade-1"].profile_ids == ()

    warning_text = " ".join(warning.detail.lower() for warning in result.warnings)
    for disallowed_claim in (" legal", " safe", "recommended", "likely", "trusted"):
        assert disallowed_claim not in warning_text


def test_snapshot_pack_hash_changes_with_embedded_profile_or_rule_data() -> None:
    base = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(characteristic_value="6"),
        source_kind="ros_xml",
    )
    changed_characteristic = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(characteristic_value="7"),
        source_kind="ros_xml",
    )
    changed_rule = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(rule_description="Changed synthetic note."),
        source_kind="ros_xml",
    )

    assert base.payload.snapshot_profile_pack is not None
    assert changed_characteristic.payload.snapshot_profile_pack is not None
    assert changed_rule.payload.snapshot_profile_pack is not None
    assert (
        len(
            {
                base.payload.snapshot_profile_pack.pack_hash,
                changed_characteristic.payload.snapshot_profile_pack.pack_hash,
                changed_rule.payload.snapshot_profile_pack.pack_hash,
            }
        )
        == 3
    )


def test_blocked_import_has_no_index_or_snapshot_profile_pack() -> None:
    result = build_roster_import_result_from_bytes(
        filename="bad.ros",
        data=b'<!DOCTYPE roster [<!ENTITY x "boom">]><roster id="r" name="n"/>',
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.army is None
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert not result.overlays


def test_duplicate_raw_selection_ids_get_distinct_stable_keys() -> None:
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_duplicate_selection_ids(),
        source_kind="ros_xml",
    )

    index = result.payload.roster_index
    assert index is not None
    duplicate_entries = [
        entry for entry in index.entries if entry.selection_id == "duplicate-selection"
    ]

    assert len(duplicate_entries) == 2
    assert len({entry.selection_key for entry in duplicate_entries}) == 2
    assert all(entry.resolution_status == "unresolved" for entry in index.profile_candidates)


def test_long_characteristic_values_are_hashed_not_retained() -> None:
    long_value = "x" * 96
    result = build_roster_import_result_from_bytes(
        filename="synthetic.ros",
        data=_roster_with_snapshot_profiles(characteristic_value=long_value),
        source_kind="ros_xml",
    )

    pack = result.payload.snapshot_profile_pack
    assert pack is not None
    characteristic = pack.profiles[0].characteristics[0]
    assert characteristic.value is None
    assert characteristic.value_length == len(long_value)
    assert characteristic.value_sha256 == hashlib.sha256(long_value.encode("utf-8")).hexdigest()


def test_multi_force_rosters_block_instead_of_silently_discarding_later_forces() -> None:
    result = build_roster_import_result_from_bytes(
        filename="multi-force.ros",
        data=_multi_force_roster(),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.army is None
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert any(
        reason.reason_id == "unsupported-roster-force-count" for reason in result.block_reasons
    )


def test_excessive_non_selection_document_depth_blocks_before_snapshot_extraction() -> None:
    result = build_roster_import_result_from_bytes(
        filename="deep.ros",
        data=_non_selection_deep_roster(depth=96),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert any(
        reason.reason_id == "roster-xml-document-too-deep" for reason in result.block_reasons
    )


def test_excessive_rule_description_text_blocks_snapshot_extraction() -> None:
    result = build_roster_import_result_from_bytes(
        filename="long-rule.ros",
        data=_roster_with_snapshot_profiles(rule_description="x" * 4096),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert any(reason.reason_id == "roster-xml-field-too-long" for reason in result.block_reasons)


def test_fragmented_rule_description_text_blocks_on_aggregate_length() -> None:
    result = build_roster_import_result_from_bytes(
        filename="fragmented-rule.ros",
        data=_roster_with_fragmented_rule_description(),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert any(reason.reason_id == "roster-xml-field-too-long" for reason in result.block_reasons)


def test_fragmented_characteristic_text_blocks_on_aggregate_length() -> None:
    result = build_roster_import_result_from_bytes(
        filename="fragmented-characteristic.ros",
        data=_roster_with_fragmented_characteristic_value(),
        source_kind="ros_xml",
    )

    assert result.readiness == "blocked"
    assert result.payload.roster_index is None
    assert result.payload.snapshot_profile_pack is None
    assert any(reason.reason_id == "roster-xml-field-too-long" for reason in result.block_reasons)
