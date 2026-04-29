import open3d as o3d
import numpy as np
from plyfile import PlyData, PlyElement
from copy import deepcopy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import time
from scipy.sparse import lil_matrix, diags, identity
from scipy.sparse.linalg import spsolve

# --- Helper Functions (from original script) ---
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

def visualize_and_select_points(pcd):
    """可视化点云并允许用户选择点，支持多次选择并自动去重"""
    selected_indices = set()
    pcd_for_picking = deepcopy(pcd)
    pcd_for_picking.paint_uniform_color([0.5, 0.5, 0.5])

    while True:
        if selected_indices:
            colors = np.asarray(pcd_for_picking.colors).copy()
            for idx in selected_indices:
                colors[idx] = np.array([1.0, 0.0, 0.0])
            pcd_for_picking.colors = o3d.utility.Vector3dVector(colors)

        vis = o3d.visualization.VisualizerWithEditing()
        vis.create_window(window_name='点云选择 (按 Q 退出选择)', width=1200, height=800)
        vis.add_geometry(pcd_for_picking)
        vis.run()
        new_indices = vis.get_picked_points()
        vis.destroy_window()

        if not new_indices:
            break
        selected_indices.update(new_indices)
        
        # Removed the confirmation dialog to streamline the process
    return list(selected_indices)

def ground_truth_construction(sampled_points, key_points, k, alpha):
    """基于3D AffordanceNet真值构建方法生成可供性概率分数"""
    tree = cKDTree(sampled_points)
    distances, indices = tree.query(sampled_points, k=k + 1)
    indices = indices[:, 1:]
    distances = distances[:, 1:]

    N = sampled_points.shape[0]
    A = lil_matrix((N, N))
    for i in range(N):
        A[i, indices[i]] = distances[i]
    
    W = 0.5 * (A + A.T)
    d_inv_sqrt_arr = 1.0 / np.sqrt(np.array(W.sum(axis=1)).flatten() + 1e-8)
    D_inv_sqrt = diags(d_inv_sqrt_arr)
    W_tilde = D_inv_sqrt @ W @ D_inv_sqrt

    Y = np.zeros(N)
    for key in key_points:
        _, idx = tree.query(key, k=1)
        Y[idx] = 1.0

    I = identity(N)
    S = spsolve(I - alpha * W_tilde, Y)
    S = (S - S.min()) / (S.max() - S.min() + 1e-8)
    return S

def visualize_affordance(sampled_points, scores, colormap):
    """可视化扩散结果"""
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(sampled_points)
    norm = plt.Normalize(vmin=scores.min(), vmax=scores.max())
    cmap = plt.get_cmap(colormap)
    colors = cmap(norm(scores))[:, :3]
    pcd.colors = o3d.utility.Vector3dVector(colors)
    
    o3d.visualization.draw_geometries([pcd], window_name="3D Affordance 扩散结果", width=1200, height=800)
    return pcd

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

# --- Main Application Class ---

class AnnotationApp:
    def __init__(self, root, directory, start_folder_number=0):
        self.root = root
        self.root.title("优化版点云标注与扩散工具")
        self.root.geometry("600x550")

        # File management
        self.base_directory = directory
        self.start_folder_number = start_folder_number
        self.point_cloud_files = self._scan_for_files()
        self.current_file_index = -1

        # State variables
        self.pcd = None
        self.selected_indices = []
        self.selected_points_info = []
        self.highlighted_pcd = None
        self.current_file_path = None
        self.affordance_pcd = None
        self.affordance_scores = None
        self.sampled_points = None

        # Build GUI
        self._create_widgets()

        self.log(f"找到 {len(self.point_cloud_files)} 个待处理的点云文件。")
        self.log("请点击 '下一个文件' 开始标注。")

    def _scan_for_files(self):
        """Scans the directory for ply-10000.ply files, starting from a specific folder number."""
        ply_paths = {}
        for dirpath, _, filenames in os.walk(self.base_directory):
            if 'point_sample' in dirpath:
                try:
                    folder_name = os.path.basename(os.path.dirname(dirpath))
                    folder_num = int(folder_name)
                    if folder_num >= self.start_folder_number:
                        for filename in filenames:
                            if filename == 'ply-10000.ply':
                                ply_paths[folder_num] = os.path.join(dirpath, filename)
                except (ValueError, IndexError):
                    continue
        
        sorted_keys = sorted(ply_paths.keys())
        paths = [ply_paths[key] for key in sorted_keys]
        return paths

    def _create_widgets(self):
        """Creates and arranges all the GUI widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="点云标注与扩散工具", font=("微软雅黑", 20, "bold"))
        title_label.pack(pady=10)

        file_frame = ttk.Frame(main_frame)
        file_frame.pack(pady=5)
        
        self.next_button = ttk.Button(file_frame, text="下一个文件", width=20, command=self.load_next_file)
        self.reannotate_button = ttk.Button(file_frame, text="重新标注当前点", width=20, command=self.reannotate)
        self.next_button.pack(side=tk.LEFT, padx=5)
        self.reannotate_button.pack(side=tk.LEFT, padx=5)

        params_frame = ttk.LabelFrame(main_frame, text="扩散参数设置", padding="10")
        params_frame.pack(pady=10, fill=tk.X)

        self.k_slider = self._create_slider(params_frame, "k近邻数:", 0, 1, 50, 10)
        self.alpha_slider = self._create_slider(params_frame, "衰减系数:", 0, 0.9, 0.999, 0.998, is_float=True)
        
        colormap_label = ttk.Label(params_frame, text="色彩映射:")
        colormap_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.colormap_combo = ttk.Combobox(params_frame, values=['jet', 'viridis', 'plasma', 'inferno', 'magma', 'cividis'], width=15)
        self.colormap_combo.set('jet')
        self.colormap_combo.grid(row=1, column=1, padx=5, pady=5)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(pady=5)
        self.calculate_button = ttk.Button(action_frame, text="执行扩散计算", width=20, command=self.calculate_diffusion)
        self.save_button = ttk.Button(action_frame, text="保存扩散结果", width=20, command=self.save_results)
        self.calculate_button.pack(side=tk.LEFT, padx=5)
        self.save_button.pack(side=tk.LEFT, padx=5)

        output_log = tk.Text(main_frame, height=10, background='white', font=("微软雅黑", 10))
        output_log.pack(pady=10, fill=tk.BOTH, expand=True)
        self.output_log = output_log

        exit_button = ttk.Button(main_frame, text="退出", command=self.root.destroy, width=10)
        exit_button.pack(pady=10)

    def _create_slider(self, parent, text, row, from_, to, default, is_float=False):
        """Helper to create a label and a slider."""
        label = ttk.Label(parent, text=text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        
        slider_val = tk.DoubleVar() if is_float else tk.IntVar()
        slider_val.set(default)
        
        slider = ttk.Scale(parent, from_=from_, to=to, orient=tk.HORIZONTAL, length=150, variable=slider_val)
        slider.grid(row=row, column=1, padx=5, pady=5)
        
        val_label = ttk.Label(parent, textvariable=slider_val)
        val_label.grid(row=row, column=2, padx=5, pady=5)
        
        return slider_val

    def log(self, message):
        self.output_log.insert(tk.END, message + "\n")
        self.output_log.see(tk.END)

    def load_next_file(self):
        """Loads the next point cloud file from the list and initiates annotation."""
        self.current_file_index += 1
        if self.current_file_index >= len(self.point_cloud_files):
            self.log("所有文件处理完毕！")
            messagebox.showinfo("完成", "已处理完所有点云文件。")
            self.next_button.config(state=tk.DISABLED)
            return

        self.current_file_path = self.point_cloud_files[self.current_file_index]
        self.log(f"--- 开始处理文件 ({self.current_file_index + 1}/{len(self.point_cloud_files)}) ---")
        self.log(f"加载: {self.current_file_path}")

        try:
            self.pcd = o3d.io.read_point_cloud(self.current_file_path)
            if not self.pcd.has_points():
                self.log("错误: 点云文件为空或加载失败。")
                return
            if not self.pcd.has_colors():
                self.pcd.paint_uniform_color([0.5, 0.5, 0.5])
        except Exception as e:
            self.log(f"读取文件失败: {e}")
            messagebox.showerror("错误", f"读取文件失败: {e}")
            return

        self.log(f"点云加载成功，点数: {len(self.pcd.points)}")
        self.log("请在弹出的窗口中选择点 (Shift+左键)，完成后按 Q 键或关闭窗口。")
        
        self.annotate_current_file()

    def annotate_current_file(self):
        """Handles the annotation process for the currently loaded PCD."""
        self.selected_indices = visualize_and_select_points(self.pcd)

        if not self.selected_indices:
            self.log("未选择任何点。跳过此文件。")
            return

        self.log(f"已选择 {len(self.selected_indices)} 个点。")

        # Process and save the selected points
        points = np.asarray(self.pcd.points)
        self.selected_points_info = []
        for idx in self.selected_indices:
            self.selected_points_info.append({
                'index': idx,
                'coordinates': tuple(points[idx]),
            })

        path, filename = os.path.split(self.current_file_path)
        info_filename = os.path.splitext(filename)[0] + "_selected_points.txt"
        self.info_path = os.path.join(path, info_filename)

        with open(self.info_path, 'w', encoding='utf-8') as f:
            f.write("选中点坐标信息:\n")
            f.write("索引\tX坐标\tY坐标\tZ坐标\n")
            for info in self.selected_points_info:
                idx = info['index']
                x, y, z = info['coordinates']
                f.write(f"{idx}\t{x:.6f}\t{y:.6f}\t{z:.6f}\n")
        
        self.log(f"选中点坐标已保存至: {self.info_path}")

        # Save highlighted point cloud
        self.highlighted_pcd = deepcopy(self.pcd)
        colors = np.asarray(self.highlighted_pcd.colors)
        colors[self.selected_indices] = [1, 0, 0] # Red
        self.highlighted_pcd.colors = o3d.utility.Vector3dVector(colors)
        
        output_filename = os.path.splitext(filename)[0] + "_highlighted.ply"
        output_path = os.path.join(path, output_filename)
        o3d.io.write_point_cloud(output_path, self.highlighted_pcd)
        self.log(f"高亮点云已保存至: {output_path}")
        self.log("标注完成。您可以执行扩散计算或加载下一个文件。")

    def reannotate(self):
        """Allows re-annotation of the currently loaded point cloud."""
        if self.pcd is None:
            messagebox.showerror("错误", "请先使用 '下一个文件' 加载一个点云。")
            return
        self.log("--- 重新标注当前文件 ---")
        self.log("请在弹出的窗口中选择点，完成后按 Q 键或关闭窗口。")
        self.annotate_current_file()

    def calculate_diffusion(self):
        """Calculates and visualizes the affordance diffusion."""
        if not self.selected_indices:
            messagebox.showerror("错误", "请先标注点云文件。")
            return

        self.sampled_points = read_ply_points(self.current_file_path, self.log)
        key_points = read_key_points_from_txt(self.info_path, self.log)

        if self.sampled_points is None or key_points is None:
            return

        k_neighbors = int(self.k_slider.get())
        alpha = self.alpha_slider.get()
        colormap = self.colormap_combo.get()

        self.log("开始扩散计算...")
        self.log(f"参数: k={k_neighbors}, alpha={alpha:.4f}, colormap={colormap}")
        start_time = time.time()

        try:
            self.affordance_scores = ground_truth_construction(
                self.sampled_points, key_points, k=k_neighbors, alpha=alpha
            )
            elapsed_time = time.time() - start_time
            self.log(f"扩散计算完成! 耗时: {elapsed_time:.2f}秒")

            self.affordance_pcd = visualize_affordance(self.sampled_points, self.affordance_scores, colormap)
            self.log("扩散结果可视化完成。")
        except Exception as e:
            self.log(f"扩散计算失败: {e}")
            messagebox.showerror("错误", f"扩散计算失败: {e}")

    def save_results(self):
        """Saves the result of the diffusion calculation."""
        if self.affordance_pcd is None or self.affordance_scores is None:
            messagebox.showerror("错误", "请先执行扩散计算。")
            return

        path, filename = os.path.split(self.current_file_path)
        default_filename = os.path.splitext(filename)[0] + "_affordance.ply"
        
        save_path = filedialog.asksaveasfilename(
            initialdir=path,
            initialfile=default_filename,
            title="保存扩散结果",
            filetypes=(("PLY files", "*.ply"), ("All files", "*.*"))
        )

        if not save_path:
            self.log("保存操作已取消。")
            return

        result_path = save_affordance_cloud(
            self.affordance_pcd, self.affordance_scores, save_path, self.log
        )
        if result_path:
            messagebox.showinfo("保存成功", f"扩散结果已保存至:\n{result_path}")
            self.log(f"扩散结果已保存至: {result_path}")

def main():
    # 1. 指定包含点云数据的根目录
    directory = "d:\\Latex工作区\\666\\knife"
    # 2. 指定起始文件夹编号
    start_folder = 117 

    root = tk.Tk()
    app = AnnotationApp(root, directory, start_folder_number=start_folder)
    root.mainloop()

if __name__ == "__main__":
    np.set_printoptions(suppress=True, precision=6)
    main()