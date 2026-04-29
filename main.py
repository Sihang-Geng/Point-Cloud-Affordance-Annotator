from pathlib import Path


# =========================
# User Configuration
# =========================
# Readers only need to edit this block, then run:
#   python main.py
#
# RUN_MODE:
#   "single" -> annotate one point-cloud file, best for quick tests
#   "batch"  -> scan a dataset folder and annotate files one by one
RUN_MODE = "single"

# Single-file mode. Relative paths are resolved from this project folder.
SINGLE_POINT_CLOUD_FILE = r"data\point_clouds\object_95.ply"
AUTO_LOAD_SINGLE_FILE = True

# All selected-point, highlighted-cloud, and affordance outputs go here.
OUTPUT_DIR = "outputs"

# Batch mode. The scanner keeps the original rule:
# find files named "ply-10000.ply" inside folders containing "point_sample".
BATCH_DATA_DIR = r"d:\Latex工作区\666\knife"
BATCH_START_FOLDER = 117


def import_launchers():
    try:
        from pc_affordance_annotator.launcher import run_batch, run_single_file
        return run_batch, run_single_file
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
    if RUN_MODE not in ("single", "batch"):
        raise ValueError('RUN_MODE must be "single" or "batch".')

    if RUN_MODE == "single":
        point_cloud = project_path(SINGLE_POINT_CLOUD_FILE)
        if not point_cloud.exists():
            raise FileNotFoundError(f"Single point-cloud file not found: {point_cloud}")


def main():
    validate_config()
    run_batch, run_single_file = import_launchers()

    if RUN_MODE == "single":
        run_single_file(
            project_path(SINGLE_POINT_CLOUD_FILE),
            auto_load=AUTO_LOAD_SINGLE_FILE,
            output_dir=project_path(OUTPUT_DIR),
        )
        return

    if RUN_MODE == "batch":
        run_batch(
            project_path(BATCH_DATA_DIR),
            start_folder=BATCH_START_FOLDER,
            output_dir=project_path(OUTPUT_DIR),
        )
        return


if __name__ == "__main__":
    main()
