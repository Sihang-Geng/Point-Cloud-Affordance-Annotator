import open3d as o3d
import matplotlib.pyplot as plt
import numpy as np


def visualize_affordance(sampled_points, scores, colormap):
    """可视化扩散结果"""
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(sampled_points)
    norm = plt.Normalize(vmin=scores.min(), vmax=scores.max())
    cmap = plt.get_cmap(colormap)
    colors = cmap(norm(scores))[:, :3]
    pcd.colors = o3d.utility.Vector3dVector(colors)

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="3D Affordance 扩散结果", width=1200, height=800)
    vis.add_geometry(pcd)

    render_option = vis.get_render_option()
    render_option.background_color = np.asarray([0.035, 0.045, 0.055])
    render_option.point_size = 4.0

    vis.run()
    vis.destroy_window()
    return pcd
