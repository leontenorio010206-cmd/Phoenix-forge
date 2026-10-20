import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.examples import adder_project, clock_project


def main():
    root = Path(__file__).resolve().parents[1] / "examples"
    for slug, project in (("full_adder", adder_project()), ("semaforo", clock_project())):
        folder = root / slug
        folder.mkdir(parents=True, exist_ok=True)
        project.write_sources(folder)
        project.save(folder / (slug + ".pforge"), overwrite=True)


if __name__ == "__main__":
    main()
