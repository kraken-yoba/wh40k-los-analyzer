from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dev_script_uses_configurable_host_and_port() -> None:
    script = (REPO_ROOT / "scripts" / "dev.ps1").read_text(encoding="utf-8")

    assert "$env:FORTYK_LOS_HOST" in script
    assert "$env:FORTYK_LOS_PORT" in script
    assert "--host $bindHost" in script
    assert "--port $port" in script
    assert "--port 8000" not in script
