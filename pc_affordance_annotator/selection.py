import numpy as np
from copy import deepcopy
import open3d as o3d


def visualize_and_select_points(pcd):
    """可视化点云并允许用户选择点，支持多次选择并自动去重"""
    print("\n" + "="*50)
    print(">>> 进入点云选择模式 <<<")
    print("操作指南:")
    print("1. [Shift + 鼠标左键]: 选择点 (选中后点会变红)")
    print("2. [Shift + 鼠标右键]: 取消选择")
    print("3. [Q] 或 [Esc]: 退出选择并保存结果")
    print("4. [鼠标左键]: 旋转视角")
    print("5. [鼠标右键]: 平移视角")
    print("6. [鼠标滚轮]: 缩放")
    print("="*50 + "\n")

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
        vis.create_window(window_name='点云选择 (Shift+左键选择, Q退出)', width=1600, height=1000, left=50, top=50)
        vis.add_geometry(pcd_for_picking)
        
        opt = vis.get_render_option()
        if opt is not None:
            opt.point_size = 5.0
            opt.background_color = np.asarray([0.95, 0.95, 0.95])
        
        print("等待用户操作... (请在弹出窗口中进行选择)")
        vis.run()
        new_indices = vis.get_picked_points()
        vis.destroy_window()

        if not new_indices:
            print("未获取到新选择的点。")
            break
        
        print(f"本次选择了 {len(new_indices)} 个点。")
        selected_indices.update(new_indices)
        print(f"当前累计已选择 {len(selected_indices)} 个点。")
        
    print(f">>> 退出选择模式，总共选择了 {len(selected_indices)} 个点 <<<")
    return list(selected_indices)
