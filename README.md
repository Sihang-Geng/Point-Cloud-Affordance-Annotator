<h1 align="center">Point Cloud Affordance Annotator</h1>

<p align="center">
  <b>Click a few 3D points. Diffuse them into a dense affordance heatmap.</b>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Open3D" src="https://img.shields.io/badge/Open3D-Point%20Clouds-2E8B57?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-111827?style=flat-square">
</p>

<p align="center">
  <a href="#-installation">Installation</a> ·
  <a href="#-run-the-demo">Run Demo</a> ·
  <a href="#-visual-gallery">Visual Gallery</a> ·
  <a href="#-gui-guide">GUI Guide</a> ·
  <a href="#-project-map">Project Map</a>
</p>

---

## ✨ What It Does

| Need | What this tool gives you |
| --- | --- |
| Sparse 3D annotation | Select only a few seed points in an Open3D window |
| Dense affordance labels | Diffuse seed points to every point in the cloud |
| Fast visual feedback | Re-run diffusion after changing `k`, `alpha`, or colormap |
| Clean files | Inputs stay in `data/point_clouds/`, outputs go to `outputs/` |
| Easy reading | Core logic split into small Python modules |

> Built for quick dataset labeling, robotics affordance experiments, and visual sanity-checking of point-cloud interaction regions.

## 🚀 Installation

> New to Python? Follow the **Conda path** below. It keeps this project isolated from your other Python projects.

### 1. Clone the repository

```bash
git clone https://github.com/Sihang-Geng/Point-Cloud-Affordance-Annotator.git
cd Point-Cloud-Affordance-Annotator
```

### 2. Create a clean environment

| Option | Best for | Commands |
| --- | --- | --- |
| 🟢 Conda, recommended | Beginners / Windows users | See block below |
| 🔵 venv | Lightweight Python users | See block below |

#### 🟢 Conda environment

```bash
conda create -n pc-affordance python=3.9 -y
conda activate pc-affordance
```

#### 🔵 Python venv environment

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If the download is slow in your region, try a mirror:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. Check the installation

```bash
python -c "import open3d, numpy, scipy, matplotlib, plyfile; print('Environment ready!')"
```

If you see `Environment ready!`, you are good to go.

<table>
  <tr>
    <td><b>Small tip</b></td>
    <td>If Open3D opens a blank window or fails to display, update your graphics driver and make sure you are running on a desktop environment, not a headless terminal.</td>
  </tr>
</table>

## ⚡ Run the Demo

The fastest test is already configured in `test.py`:

```python
TEST_POINT_CLOUD_FILE = r"data\point_clouds\object_95.ply"
OUTPUT_DIR = "outputs"
```

Run:

```bash
python test.py
```

Then follow this tiny loop:

| Step | What to do | What happens |
| --- | --- | --- |
| 1 | `Shift + left click` several points | seed points are selected |
| 2 | Press `Q` | the seeds are saved to `outputs/` |
| 3 | Click `执行扩散计算` | affordance heatmap appears |
| 4 | Tune `k`, `alpha`, or colormap | quickly compare diffusion behavior |
| 5 | Click `保存扩散结果` | save the colored `.ply` |

### Use your own point cloud

1. Put your `.ply` file here:

```text
data/point_clouds/
```

2. Edit the top of `test.py`:

```python
TEST_POINT_CLOUD_FILE = r"data\point_clouds\your_file.ply"
OUTPUT_DIR = "outputs"
```

3. Run:

```bash
python test.py
```

No command-line path arguments are required. Edit the small config block, then run the script.

### Quick troubleshooting

| Symptom | Try this |
| --- | --- |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the active environment |
| Open3D window does not appear | Use a local desktop session and update graphics drivers |
| PowerShell refuses activation | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again |
| Point cloud is empty | Check that your PLY has `x`, `y`, `z` vertex fields |

## 🖼 Visual Gallery

### Local Interaction Region

| 🎯 Sparse seeds | 🌈 Diffused heatmap |
| --- | --- |
| <img src="examples/readme/annotation-local-region.jpg" alt="Sparse annotation for local interaction region" width="360"> | <img src="examples/readme/diffusion-local-region.jpg" alt="Diffused affordance result for local interaction region" width="360"> |

### Ring / Handle Region

| 🎯 Sparse seeds | 🌈 Diffused heatmap |
| --- | --- |
| <img src="examples/readme/annotation-ring-region.jpg" alt="Sparse annotation for ring region" width="360"> | <img src="examples/readme/diffusion-ring-region.jpg" alt="Diffused affordance result for ring region" width="360"> |

## 🧭 GUI Guide

<p align="center">
  <img src="examples/readme/gui.jpg" alt="Point Cloud Affordance Annotator GUI" width="540">
</p>

| Button / control | Meaning |
| --- | --- |
| `加载并标注下一个点云` | Load a point cloud and open the picking window |
| `重新标注当前点云` | Re-pick seed points for the current cloud |
| `k近邻数` | Control the local graph neighborhood |
| `衰减系数` | Control diffusion strength |
| `色彩映射` | Switch visual colormap |
| `执行扩散计算` | Generate the affordance heatmap |
| `保存扩散结果` | Save the colored `.ply` result |

Open3D picking:

| Gesture | Action |
| --- | --- |
| `Shift + left click` | Select a seed point |
| `Shift + right click` | Remove a selected point |
| `Q` | Finish picking |

## 📦 Outputs

Generated files are written to `outputs/` by default.

| File | Description |
| --- | --- |
| `*_selected_points.txt` | Selected seed point indices and XYZ coordinates |
| `*_highlighted.ply` | Point cloud with selected seeds highlighted |
| `*_affordance.ply` | Colored point cloud with an extra `affordance` score field |

The affordance PLY stores:

```text
x, y, z, red, green, blue, affordance
```

## 🧪 Batch Annotation

For dataset-style labeling, edit `main.py`:

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

Batch mode keeps the original prototype rule:

| Rule | Detail |
| --- | --- |
| Search root | `BATCH_DATA_DIR` |
| Valid folder | path contains `point_sample` |
| Valid file | file name is `ply-10000.ply` |
| Ordering | numeric parent folder |
| Resume point | `BATCH_START_FOLDER` |

## 🧠 How Diffusion Works

The implementation keeps the original behavior:

```text
selected seed points -> kNN graph -> normalized graph -> linear solve -> [0, 1] score
```

The core equation is:

```text
(I - alpha * W_tilde) S = Y
```

Code location:

```text
pc_affordance_annotator/diffusion.py
```

## 🗂 Project Map

```text
.
├── data/point_clouds/          # sample or user-provided input point clouds
├── examples/readme/            # README images with GitHub-safe names
├── legacy/                     # original single-file prototype
├── outputs/                    # generated annotation and diffusion files
├── pc_affordance_annotator/
│   ├── app.py                  # Tkinter GUI
│   ├── diffusion.py            # graph diffusion logic
│   ├── io_utils.py             # PLY/TXT helpers
│   ├── launcher.py             # launch helpers
│   ├── selection.py            # Open3D point picking
│   └── visualization.py        # heatmap rendering
├── main.py                     # configurable batch/single entry
├── test.py                     # easiest demo entry
└── requirements.txt
```

## ✅ Notes

| Topic | Note |
| --- | --- |
| Input format | PLY with `x`, `y`, `z` vertex fields |
| No colors? | The tool paints the cloud gray for picking |
| Visualization | Diffusion uses a dark Open3D background for stronger contrast |
| Git hygiene | Generated output files are ignored by default |

## 📄 License

MIT License. See [LICENSE](LICENSE).
