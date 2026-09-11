import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from new_project import REPO, scaffold  # noqa: E402


def test_scaffold_tabular_and_simulation(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    shutil.copytree(REPO / "templates", root / "templates")

    tab = scaffold("Demo_Comp", group="Kaggles", template="tabular", slug="demo-comp", root=root)
    assert (tab / "src" / "train.py").exists()
    readme = (tab / "README.md").read_text()
    assert "{{" not in readme and "demo-comp" in readme and "Demo Comp" in readme
    assert "demo-comp" in (tab / "config.yaml").read_text()

    sim = scaffold(
        "Demo_Sim",
        group="Kaggles",
        template="simulation",
        slug="demo-sim",
        env="connectx",
        root=root,
    )
    assert 'ENV_NAME = "connectx"' in (sim / "sim" / "run.py").read_text()
