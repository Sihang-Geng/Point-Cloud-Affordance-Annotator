<p align="center">
  <img src="examples/readme/gui.jpg" alt="Point Cloud Affordance Annotator GUI" width="760">
</p>

<h1 align="center">Point Cloud Affordance Annotator</h1>

<p align="center">
  A lightweight Open3D + Tkinter tool for turning a few manually selected 3D points into dense point-cloud affordance heatmaps.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#visual-results">Visual Results</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#project-layout">Project Layout</a>
</p>

---

## Why This Project

Dense 3D affordance labeling is usually slow: users need to mark many points or manually paint object regions. This tool keeps the human interaction small:

1. Load a `.ply` point cloud.
2. Select only a few key points in the Open3D picking window.
3. Run graph-based diffusion to generate a dense affordance score for every point.
4. Save the result as a colored `.ply` with an `affordance` field.

The original diffusion behavior is intentionally preserved from the prototype script, while the codebase is split into small modules for easier reading, testing, and reuse.

## Visual Results

### Example 1: Local Interaction Region

| Sparse point annotation | Diffused affordance heatmap |
| --- | --- |
| <img src="examples/readme/annotation-local-region.jpg" alt="Sparse annotation for local interaction region" width="420"> | <img src="examples/readme/diffusion-local-region.jpg" alt="Diffused affordance result for local interaction region" width="420"> |

### Example 2: Ring / Handle Region

| Sparse point annotation | Diffused affordance heatmap |
| --- | --- |
| <img src="examples/readme/annotation-ring-region.jpg" alt="Sparse annotation for ring region" width="420"> | <img src="examples/readme/diffusion-ring-region.jpg" alt="Diffused affordance result for ring region" width="420"> |

### GUI

<p align="center">
  <img src="examples/readme/gui.jpg" alt="GUI overview" width="760">
</p>

The GUI is intentionally simple:

- `加载并标注下一个点云`: load a point cloud and open the Open3D picking window.
- `重新标注当前点云`: repeat annotation for the current point cloud.
- `执行扩散计算`: run affordance diffusion from the selected seed points.
- `保存扩散结果`: save the colored affordance point cloud.

Open3D picking controls:

- `Shift + left click`: select a point.
- `Shift + right click`: remove a selected point.
- `Q`: finish picking and return to the main GUI.

## Quick Start

### 1. Install Dependencies

Python 3.9+ is recommended.

```bash
pip install -r requirements.txt
```

### 2. Run One-File Test

The easiest entry is `test.py`. It already points to the included sample point cloud:

```python
TEST_POINT_CLOUD_FILE = r"data\point_clouds\object_95.ply"
OUTPUT_DIR = "outputs"
```

Run:

```bash
python test.py
```

Workflow:

1. The Open3D window opens automatically.
2. Select several seed points with `Shift + left click`.
3. Press `Q` to finish annotation.
4. Click `执行扩散计算`.
5. Change `k近邻数`, `衰减系数`, or `色彩映射` if needed, then run diffusion again.
6. Click `保存扩散结果`.

### 3. Run Your Own Point Cloud

Put your `.ply` file under:

```text
data/point_clouds/
```

Then edit `test.py`:

```python
TEST_POINT_CLOUD_FILE = r"data\point_clouds\your_file.ply"
OUTPUT_DIR = "outputs"
```

Run:

```bash
python test.py
```

No command-line path arguments are required; readers only edit the configuration block at the top of the file.

## Batch Annotation

For dataset-style annotation, use `main.py`.

Edit the configuration block:

```python
RUN_MODE = "batch"
BATCH_DATA_DIR = r"d:\Latex工作区\666\knife"
BATCH_START_FOLDER = 117
OUTPUT_DIR = "outputs"
```

Then run:

```bash
python main.py
```

Batch mode keeps the original prototype scanning rule:

- recursively scan `BATCH_DATA_DIR`;
- only look inside paths containing `point_sample`;
- only load files named `ply-10000.ply`;
- use the numeric parent folder as the ordering key;
- start from `BATCH_START_FOLDER`.

## Outputs

By default, generated files are written to `outputs/` so the repository root stays clean.

For a point cloud named `object_95.ply`, the tool can produce:

```text
outputs/object_95_selected_points.txt   # selected seed point index and XYZ coordinates
outputs/object_95_highlighted.ply       # original point cloud with selected points highlighted
outputs/object_95_affordance.ply        # colored point cloud with affordance scores
```

The affordance `.ply` contains:

- `x`, `y`, `z`
- `red`, `green`, `blue`
- `affordance`

## How It Works

The diffusion logic follows the original script:

1. Build a `cKDTree` on all sampled points.
2. Query `k` nearest neighbors for every point.
3. Construct a sparse graph from neighbor distances.
4. Symmetrize and normalize the graph.
5. Set selected key points as seed labels.
6. Solve:

```text
(I - alpha * W_tilde) S = Y
```

7. Normalize `S` to `[0, 1]`.
8. Render the result with a Matplotlib colormap in Open3D.

The implementation is in:

```text
pc_affordance_annotator/diffusion.py
```

## Project Layout

```text
.
├── data/
│   └── point_clouds/                 # sample or user-provided input point clouds
├── examples/
│   ├── readme/                       # README-safe image names
│   ├── 标注.jpg
│   ├── 标注2.jpg
│   ├── 结果.jpg
│   ├── 结果2.jpg
│   └── 交互界面.jpg
├── legacy/
│   └── annoteation(1).py             # original single-file prototype
├── outputs/                          # generated annotation and diffusion files
├── pc_affordance_annotator/
│   ├── app.py                        # Tkinter GUI workflow
│   ├── diffusion.py                  # original graph diffusion logic
│   ├── io_utils.py                   # PLY/TXT read-write helpers
│   ├── launcher.py                   # single-file and batch launch helpers
│   ├── selection.py                  # Open3D point picking
│   └── visualization.py              # affordance heatmap visualization
├── main.py                           # configurable main entry
├── test.py                           # easiest one-file test entry
├── requirements.txt
└── README.md
```

## Notes

- The point-cloud input format is expected to be PLY with `x`, `y`, `z` vertex fields.
- If the point cloud has no colors, the tool paints it gray before point picking.
- The diffusion visualization uses a dark Open3D background to make heatmaps easier to inspect.
- `outputs/` is ignored by Git by default except for `.gitkeep`, so your local generated files do not clutter commits.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
