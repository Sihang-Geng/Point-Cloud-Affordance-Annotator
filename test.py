from pathlib import Path

# & "C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe" test.py
# =========================
# Quick Test Configuration
# =========================
# Readers only need to edit TEST_POINT_CLOUD_FILE, then run:
#   python test.py
#
# Relative paths are resolved from this project folder.
TEST_POINT_CLOUD_FILE = r"data\point_clouds\object_95.ply"
AUTO_LOAD_POINT_CLOUD = True

# Selected-point, highlighted-cloud, and affordance outputs go here.
OUTPUT_DIR = "outputs"


def import_launcher():
    try:
        from pc_affordance_annotator.launcher import run_single_file
        return run_single_file
    except ModuleNotFoundError as exc:
        missing = exc.name
        raise SystemExit(
            f"Missing dependency: {missing}\n"
            "Please install dependencies first:\n"
            "  pip install -r requirements.txt"
        ) from exc


def project_path(path_text):
    path = Path(path_text)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parent / path


def validate_config():
    point_cloud = project_path(TEST_POINT_CLOUD_FILE)
    if not point_cloud.exists():
        raise FileNotFoundError(f"Test point-cloud file not found: {point_cloud}")


def main():
    validate_config()
    run_single_file = import_launcher()

    run_single_file(
        project_path(TEST_POINT_CLOUD_FILE),
        auto_load=AUTO_LOAD_POINT_CLOUD,
        output_dir=project_path(OUTPUT_DIR),
    )


if __name__ == "__main__":
    main()
