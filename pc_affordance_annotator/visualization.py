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
    vis.create_window(window_name="3D Affordance 扩散结果", width=1600, height=1000, left=50, top=50)
    vis.add_geometry(pcd)
    
    opt = vis.get_render_option()
    if opt is not None:
        opt.point_size = 5.0
        opt.background_color = np.asarray([0.15, 0.15, 0.15]) # 深色背景更能凸显热力图
        
    vis.run()
    vis.destroy_window()
    
    return pcd
