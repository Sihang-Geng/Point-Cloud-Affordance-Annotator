from copy import deepcopy
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import open3d as o3d

from .diffusion import ground_truth_construction
from .io_utils import read_key_points_from_txt, read_ply_points, save_affordance_cloud
from .selection import visualize_and_select_points
from .visualization import visualize_affordance


class AnnotationApp:
    def __init__(self, root, directory, start_folder_number=0, point_cloud_files=None, output_directory=None):
        self.root = root
        self.root.title("Point Cloud Affordance Annotator")
        self.root.geometry("760x640")
        self.root.minsize(720, 600)

        # File management
        self.base_directory = directory
        self.start_folder_number = start_folder_number
        self.output_directory = os.path.abspath(output_directory) if output_directory else None
        self.point_cloud_files = list(point_cloud_files) if point_cloud_files is not None else self._scan_for_files()
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
        if self.output_directory:
            self.log(f"输出目录: {self.output_directory}")
        self.log("请点击 '下一个文件' 开始标注。")

    def _get_output_path(self, filename):
        if self.output_directory:
            os.makedirs(self.output_directory, exist_ok=True)
            return os.path.join(self.output_directory, filename)

        path, _ = os.path.split(self.current_file_path)
        return os.path.join(path, filename)

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
        self._configure_style()

        main_frame = ttk.Frame(self.root, padding="24", style="App.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame, style="App.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 18))

        title_label = ttk.Label(
            header_frame,
            text="Point Cloud Affordance Annotator",
            style="Title.TLabel",
        )
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(
            header_frame,
            text="少量关键点标注，快速扩散生成点云 affordance 热力标签",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack(anchor=tk.W, pady=(6, 0))

        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 14))
        
        self.next_button = ttk.Button(file_frame, text="加载并标注下一个点云", style="Primary.TButton", command=self.load_next_file)
        self.reannotate_button = ttk.Button(file_frame, text="重新标注当前点云", command=self.reannotate)
        self.next_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.reannotate_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        params_frame = ttk.LabelFrame(main_frame, text="Diffusion Settings / 扩散参数", padding="16", style="Card.TLabelframe")
        params_frame.pack(pady=(0, 14), fill=tk.X)
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(2, minsize=70)

        self.k_slider = self._create_slider(params_frame, "k近邻数:", 0, 1, 50, 10)
        self.alpha_slider = self._create_slider(params_frame, "衰减系数:", 0, 0.9, 0.999, 0.998, is_float=True)
        
        colormap_label = ttk.Label(params_frame, text="色彩映射:")
        colormap_label.grid(row=2, column=0, padx=(0, 10), pady=(12, 0), sticky=tk.W)
        self.colormap_combo = ttk.Combobox(
            params_frame,
            values=['jet', 'viridis', 'plasma', 'inferno', 'magma', 'cividis'],
            width=18,
            state="readonly",
        )
        self.colormap_combo.set('jet')
        self.colormap_combo.grid(row=2, column=1, padx=0, pady=(12, 0), sticky=tk.W)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 14))
        self.calculate_button = ttk.Button(action_frame, text="执行扩散计算", style="Primary.TButton", command=self.calculate_diffusion)
        self.save_button = ttk.Button(action_frame, text="保存扩散结果", command=self.save_results)
        self.calculate_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        log_frame = ttk.LabelFrame(main_frame, text="Run Log / 运行日志", padding="10", style="Card.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 14))

        output_log = tk.Text(
            log_frame,
            height=12,
            background='#fbfbf8',
            foreground='#1f2a2e',
            insertbackground='#1f2a2e',
            relief=tk.FLAT,
            borderwidth=0,
            font=("Consolas", 10),
            wrap=tk.WORD,
        )
        output_log.pack(fill=tk.BOTH, expand=True)
        self.output_log = output_log

        footer_frame = ttk.Frame(main_frame, style="App.TFrame")
        footer_frame.pack(fill=tk.X)

        hint_label = ttk.Label(
            footer_frame,
            text="Open3D 选点：Shift + 左键选择，Shift + 右键取消，Q 保存退出",
            style="Hint.TLabel",
        )
        hint_label.pack(side=tk.LEFT)

        exit_button = ttk.Button(footer_frame, text="退出", command=self.root.destroy, width=12)
        exit_button.pack(side=tk.RIGHT)

    def _configure_style(self):
        self.root.configure(bg="#f3f0e8")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#f3f0e8")
        style.configure("TFrame", background="#f3f0e8")
        style.configure("Title.TLabel", background="#f3f0e8", foreground="#182226", font=("微软雅黑", 22, "bold"))
        style.configure("Subtitle.TLabel", background="#f3f0e8", foreground="#61706f", font=("微软雅黑", 10))
        style.configure("Hint.TLabel", background="#f3f0e8", foreground="#6f7775", font=("微软雅黑", 9))
        style.configure("TLabel", background="#f3f0e8", foreground="#223034", font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10), padding=(14, 8))
        style.configure("Primary.TButton", font=("微软雅黑", 10, "bold"), padding=(14, 8))
        style.configure("Card.TLabelframe", background="#f3f0e8", bordercolor="#d8d2c6", relief=tk.SOLID)
        style.configure("Card.TLabelframe.Label", background="#f3f0e8", foreground="#2a3437", font=("微软雅黑", 10, "bold"))
        style.configure("Horizontal.TScale", background="#f3f0e8", troughcolor="#ded8cc")
        style.configure("TCombobox", padding=4)

    def _create_slider(self, parent, text, row, from_, to, default, is_float=False):
        """Helper to create a label and a slider."""
        label = ttk.Label(parent, text=text)
        label.grid(row=row, column=0, padx=(0, 10), pady=8, sticky=tk.W)
        
        slider_val = tk.DoubleVar() if is_float else tk.IntVar()
        slider_val.set(default)
        
        slider = ttk.Scale(parent, from_=from_, to=to, orient=tk.HORIZONTAL, length=150, variable=slider_val)
        slider.grid(row=row, column=1, padx=0, pady=8, sticky=tk.EW)
        
        val_label = ttk.Label(parent, textvariable=slider_val)
        val_label.grid(row=row, column=2, padx=(14, 0), pady=8, sticky=tk.W)
        
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
        self.log("="*30)
        self.log("【操作指南】")
        self.log("1. 按住 [Shift] + [鼠标左键] 选择点")
        self.log("2. 按住 [Shift] + [鼠标右键] 取消选择")
        self.log("3. 按 [Q] 键保存并退出当前选择窗口")
        self.log("="*30)
        
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

        _, filename = os.path.split(self.current_file_path)
        info_filename = os.path.splitext(filename)[0] + "_selected_points.txt"
        self.info_path = self._get_output_path(info_filename)

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
        output_path = self._get_output_path(output_filename)
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
        initial_dir = self.output_directory if self.output_directory else path
        
        save_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
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
