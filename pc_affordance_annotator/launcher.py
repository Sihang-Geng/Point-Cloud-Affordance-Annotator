import os
import tkinter as tk

import numpy as np

from .app import AnnotationApp


def run_batch(data_dir, start_folder=0, output_dir=None):
    np.set_printoptions(suppress=True, precision=6)
    root = tk.Tk()
    app = AnnotationApp(
        root,
        data_dir,
        start_folder_number=start_folder,
        output_directory=output_dir,
    )
    root.mainloop()
    return app


def run_single_file(point_cloud_file, auto_load=True, output_dir=None):
    np.set_printoptions(suppress=True, precision=6)
    point_cloud_file = os.path.abspath(point_cloud_file)
    root = tk.Tk()
    app = AnnotationApp(
        root,
        os.path.dirname(point_cloud_file),
        point_cloud_files=[point_cloud_file],
        output_directory=output_dir,
    )
    if auto_load:
        root.after(100, app.load_next_file)
    root.mainloop()
    return app
