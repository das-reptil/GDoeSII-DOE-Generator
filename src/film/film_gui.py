import os
from pathlib import Path
from tkinter import BOTH, END, HORIZONTAL, LEFT, RIGHT, Tk, Toplevel, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .film_batch import discover_frames, run_batch
from .film_config import FilmConfig
from .frame_analysis import analyze_frame, write_csv


APP_TITLE = "GDoeSII Film / GS Batch"


class FilmBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self._configure_window()
        self._build()

    def _configure_window(self):
        screen_w = max(1, self.root.winfo_screenwidth())
        screen_h = max(1, self.root.winfo_screenheight())
        width = min(920, max(700, screen_w - 100), screen_w)
        height = min(860, max(560, screen_h - 120), screen_h)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(700, width), min(560, height))
        self.root.resizable(True, True)

    def _build(self):
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=BOTH, expand=True)
        outer.columnconfigure(1, weight=1)

        self.frame_dir = ttk.Entry(outer)
        self.output_dir = ttk.Entry(outer)

        self._path_row(outer, 0, "Target frame directory", self.frame_dir, self._choose_frames)
        self._path_row(outer, 1, "Output directory", self.output_dir, self._choose_output)

        note = (
            "Film mode is intentionally Gerchberg-Saxton only. Input is a directory of target frames. "
            "The normal DOE Generator remains available for Lens, Grating, FZP and Vortex designs."
        )
        ttk.Label(outer, text=note, wraplength=830, justify=LEFT).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(6, 10)
        )

        optics = ttk.LabelFrame(outer, text="GS optics", padding=8)
        optics.grid(row=3, column=0, columnspan=3, sticky="nsew")
        optics.columnconfigure(1, weight=1)
        optics.columnconfigure(3, weight=1)

        self.width = self._var_entry(optics, 0, 0, "DOE width (px)", "512")
        self.height = self._var_entry(optics, 0, 2, "DOE height (px)", "512")
        self.pixel_nm = self._var_entry(optics, 1, 0, "DOE pixel size (nm)", "500")
        self.wavelength_nm = self._var_entry(optics, 1, 2, "Wavelength (nm)", "532")
        self.distance_mm = self._var_entry(optics, 2, 0, "Target z (mm)", "300")
        self.target_width_um = self._var_entry(optics, 2, 2, "GS target width (um; 0=fit)", "0")
        self.iterations = self._var_entry(optics, 3, 0, "GS iterations", "50")
        self.seed = self._var_entry(optics, 3, 2, "GS seed", "0")

        target = ttk.LabelFrame(outer, text="Target plane", padding=8)
        target.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        target.columnconfigure(1, weight=1)
        target.columnconfigure(3, weight=1)
        self.target_x = self._var_entry(target, 0, 0, "Target X (mm)", "0")
        self.target_y = self._var_entry(target, 0, 2, "Target Y (mm)", "0")
        self.pan = self._var_entry(target, 1, 0, "Target pan (deg)", "0")
        self.tilt = self._var_entry(target, 1, 2, "Target tilt (deg)", "0")

        brightness = ttk.LabelFrame(outer, text="Brightness analysis", padding=8)
        brightness.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        brightness.columnconfigure(1, weight=1)
        self.active_threshold = self._var_entry(brightness, 0, 0, "Active threshold", "0.05")
        ttk.Label(brightness, text="Mode").grid(row=0, column=2, sticky="w", padx=(12, 4))
        self.brightness_mode = ttk.Combobox(
            brightness,
            state="readonly",
            values=(
                "constant reconstructed brightness",
                "preserve geometric brightness",
                "analysis only",
            ),
        )
        self.brightness_mode.set("constant reconstructed brightness")
        self.brightness_mode.grid(row=0, column=3, sticky="ew")
        self.geometric_gamma = self._var_entry(brightness, 1, 0, "Geometric gamma", "0.5")
        ttk.Label(
            brightness,
            text=(
                "The batch reports a recommended external laser/duty factor. A simple scalar "
                "brightness multiplier on the target image would be cancelled by GS normalization."
            ),
            wraplength=810,
            justify=LEFT,
        ).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(5, 0))

        layout = ttk.LabelFrame(outer, text="Disc layout", padding=8)
        layout.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        layout.columnconfigure(1, weight=1)
        layout.columnconfigure(3, weight=1)
        self.ring_pitch = self._var_entry(layout, 0, 0, "Ring pitch (mm)", "2.5")
        self.ring_radius = self._var_entry(layout, 0, 2, "Ring radius (mm; 0=auto)", "0")
        ttk.Label(layout, text="DOE orientation").grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
        self.orientation = ttk.Combobox(layout, state="readonly", values=("tangential", "radial", "fixed"))
        self.orientation.set("tangential")
        self.orientation.grid(row=1, column=1, sticky="ew", pady=2)

        buttons = ttk.Frame(outer)
        buttons.grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(buttons, text="Analyze frames", command=self._analyze).pack(side=LEFT)
        ttk.Button(buttons, text="Run GS batch", command=self._run).pack(side=RIGHT)

        self.progress = ttk.Progressbar(outer, orient=HORIZONTAL, mode="determinate", maximum=100)
        self.progress.grid(row=8, column=0, columnspan=3, sticky="ew")
        self.status = ttk.Label(outer, text="Ready.")
        self.status.grid(row=9, column=0, columnspan=3, sticky="w", pady=(4, 4))
        self.log = ScrolledText(outer, height=10, wrap="word")
        self.log.grid(row=10, column=0, columnspan=3, sticky="nsew")
        outer.rowconfigure(10, weight=1)

        ttk.Label(
            outer,
            text=(
                "Current GS target-width calculation uses the existing same-sampling model. "
                "A separate physical-projection scaling mode is required before a 50 mm target can be "
                "represented directly with the 500 nm DOE sampling used in the film concept."
            ),
            wraplength=830,
            justify=LEFT,
        ).grid(row=11, column=0, columnspan=3, sticky="ew", pady=(8, 0))

    def _path_row(self, parent, row, text, entry, command):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=2)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        ttk.Button(parent, text="Browse...", command=command).grid(row=row, column=2, padx=(6, 0), pady=2)

    def _var_entry(self, parent, row, column, text, default):
        ttk.Label(parent, text=text).grid(row=row, column=column, sticky="w", padx=(0, 4), pady=2)
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.grid(row=row, column=column + 1, sticky="ew", padx=(0, 10), pady=2)
        return entry

    def _choose_frames(self):
        path = filedialog.askdirectory(title="Select directory with target frames")
        if path:
            self.frame_dir.delete(0, END)
            self.frame_dir.insert(0, path)
            if not self.output_dir.get().strip():
                self.output_dir.insert(0, str(Path(path).parent / "film_batch_output"))

    def _choose_output(self):
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_dir.delete(0, END)
            self.output_dir.insert(0, path)

    def _config(self):
        return FilmConfig(
            doe_width_px=int(self.width.get()),
            doe_height_px=int(self.height.get()),
            pixel_size_nm=float(self.pixel_nm.get()),
            wavelength_nm=float(self.wavelength_nm.get()),
            target_distance_mm=float(self.distance_mm.get()),
            target_width_um=float(self.target_width_um.get()),
            gs_iterations=int(self.iterations.get()),
            seed=int(self.seed.get()),
            target_x_mm=float(self.target_x.get()),
            target_y_mm=float(self.target_y.get()),
            target_pan_deg=float(self.pan.get()),
            target_tilt_deg=float(self.tilt.get()),
            active_threshold=float(self.active_threshold.get()),
            ring_pitch_mm=float(self.ring_pitch.get()),
            ring_radius_mm=float(self.ring_radius.get()),
            ring_orientation=self.orientation.get(),
            brightness_mode=self.brightness_mode.get(),
            geometric_gamma=float(self.geometric_gamma.get()),
        ).validate()

    def _append(self, text):
        self.log.insert(END, text + os.linesep)
        self.log.see(END)
        self.root.update_idletasks()

    def _analyze(self):
        try:
            config = self._config()
            frame_dir = self.frame_dir.get().strip()
            output_dir = self.output_dir.get().strip()
            if not frame_dir:
                raise ValueError("Select a target frame directory.")
            if not output_dir:
                raise ValueError("Select an output directory.")
            frames = discover_frames(frame_dir)
            output = Path(output_dir)
            rows = []
            for index, frame in enumerate(frames):
                row = analyze_frame(frame, config.active_threshold)
                row["frame_index"] = index
                row["frame_angle_deg"] = index * 360.0 / len(frames)
                rows.append(row)
            path = write_csv(rows, output / "statistics" / "frame_source_statistics.csv")
            self.status.config(text=f"Analyzed {len(frames)} frames.")
            self._append(f"Source-frame statistics: {path}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            self.status.config(text="Analysis failed.")

    def _progress_callback(self, frame_value, frame_total, iteration, iteration_total, message):
        if frame_total:
            frame_fraction = max(0.0, min(1.0, frame_value / frame_total))
            if iteration_total and frame_value < frame_total:
                frame_fraction = max(
                    frame_fraction,
                    min(1.0, (frame_value + iteration / iteration_total) / frame_total),
                )
            self.progress["value"] = 100.0 * frame_fraction
        self.status.config(text=message)
        self.root.update_idletasks()

    def _run(self):
        try:
            config = self._config()
            frame_dir = self.frame_dir.get().strip()
            output_dir = self.output_dir.get().strip()
            if not frame_dir:
                raise ValueError("Select a target frame directory.")
            if not output_dir:
                raise ValueError("Select an output directory.")

            self.progress["value"] = 0
            self.log.delete("1.0", END)
            self._append("Starting GS-only film batch...")
            summary = run_batch(
                frame_dir,
                output_dir,
                config=config,
                progress_callback=self._progress_callback,
            )
            self.progress["value"] = 100
            self.status.config(text=f"Completed {summary['frame_count']} frames.")
            self._append(f"Completed {summary['frame_count']} independent GS DOEs.")
            self._append(f"Output: {summary['output_directory']}")
            self._append("Brightness analysis: statistics/brightness_statistics.csv")
            self._append("Ring layout: layout/DOE_ring_layout.csv")
        except Exception as exc:
            self.status.config(text="Batch failed.")
            self._append("ERROR: " + str(exc))
            messagebox.showerror(APP_TITLE, str(exc))


def run_film_gui(parent=None):
    if parent is None:
        root = Tk()
    else:
        root = Toplevel(parent)
    FilmBatchApp(root)
    if parent is None:
        root.mainloop()
    return root
