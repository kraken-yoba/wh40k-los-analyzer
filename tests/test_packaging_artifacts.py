from __future__ import annotations

from pathlib import Path


def test_windows_packaging_artifacts_are_defined() -> None:
    workflow = Path(".github/workflows/build-windows-app.yml").read_text()
    spec = Path("packaging/pyinstaller/WarhammerTournamentCompanion.spec").read_text()
    installer = Path("packaging/windows/WarhammerTournamentCompanion.iss").read_text()

    assert "name: Build windows app" in workflow
    assert (
        "pyinstaller --noconfirm packaging/pyinstaller/WarhammerTournamentCompanion.spec"
        in workflow
    )
    assert (
        "python -m warhammer_companion.cli validate-packets --packet-dir "
        "src/warhammer_companion/seed_data/map-packets"
    ) in workflow
    assert "Start-Process" in workflow
    assert '"--require-official-data"' in workflow
    assert '"--smoke-output"' in workflow
    assert "desktop-smoke.json" in workflow
    assert "WaitForExit(120000)" in workflow
    assert "WarhammerTournamentCompanionSetup.exe" in workflow
    assert 'name="WarhammerTournamentCompanion"' in spec
    assert "seed_data/map-packets/*.json" in spec
    assert "WarhammerTournamentCompanion.exe" in installer
    assert r"{localappdata}\Programs\WarhammerTournamentCompanion" in installer
