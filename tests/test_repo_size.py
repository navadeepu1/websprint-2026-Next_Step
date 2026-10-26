from pathlib import Path
import subprocess
import sys


def test_repo_size_script_passes() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_repo_size.py"
    result = subprocess.run([sys.executable, str(script)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Repository size OK" in result.stdout
