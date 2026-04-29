import numpy as np
from plyfile import PlyData, PlyElement
from tkinter import messagebox


def read_ply_points(file_path, logger):
    """读取PLY文件并返回点云坐标（仅坐标）"""
    try:
        ply_data = PlyData.read(file_path)
        vertices = ply_data['vertex']
        points = np.vstack([vertices['x'], vertices['y'], vertices['z']]).T
        return points
    except Exception as e:
        logger(f"读取点云坐标失败: {e}")
        messagebox.showerror("错误", f"读取点云坐标失败: {e}")
        return None


def read_key_points_from_txt(file_path, logger):
    """从TXT文件读取关键点坐标"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            key_points = np.loadtxt(f, skiprows=2, usecols=(1, 2, 3))
        return key_points
    except Exception as e:
        logger(f"读取关键点失败: {e}")
        messagebox.showerror("错误", f"读取关键点失败: {e}")
        return None


def save_affordance_cloud(pcd, scores, output_path, logger):
    """保存带有affordance分数的点云"""
    try:
        points = np.asarray(pcd.points)
        colors = np.asarray(pcd.colors)
        vertices = np.zeros(points.shape[0], dtype=[
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1'),
            ('affordance', 'f4')
        ])
        vertices['x'] = points[:, 0]
        vertices['y'] = points[:, 1]
        vertices['z'] = points[:, 2]
        vertices['red'] = (colors[:, 0] * 255).astype(np.uint8)
        vertices['green'] = (colors[:, 1] * 255).astype(np.uint8)
        vertices['blue'] = (colors[:, 2] * 255).astype(np.uint8)
        vertices['affordance'] = scores
        vertex_element = PlyElement.describe(vertices, 'vertex')
        PlyData([vertex_element], text=True).write(output_path)
        return output_path
    except Exception as e:
        logger(f"保存扩散结果失败: {e}")
        messagebox.showerror("错误", f"保存扩散结果失败: {e}")
        return None
