import os
from pathlib import Path
from tkinter import BOTH, END, HORIZONTAL, LEFT, RIGHT, VERTICAL, Canvas, Tk, Toplevel, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .film_batch import discover_frames, run_batch
from .film_config import FilmConfig
from .frame_analysis import analyze_frame, write_csv
from .frame_generation import MAPPING_MODES, generate_yaw_frames
from .physical_projection import physical_projection_sampling


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
        width = min(980, max(720, screen_w - 100), screen_w)
        height = min(920, max(600, screen_h - 120), screen_h)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(640, width), min(480, height))
        self.root.resizable(True, True)

    def _build(self):
        # The complete film GUI lives in a scrollable canvas. This keeps every
        # control reachable on small/high-DPI displays while still stretching
        # the content to use wider windows when space is available.
        container = ttk.Frame(self.root)
        container.pack(fill=BOTH, expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.scroll_canvas = Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient=VERTICAL, command=self.scroll_canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient=HORIZONTAL, command=self.scroll_canvas.xview)
        self.scroll_canvas.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
        )

        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        outer = ttk.Frame(self.scroll_canvas, padding=10)
        self.scroll_content = outer
        self.scroll_window = self.scroll_canvas.create_window(
            (0, 0), window=outer, anchor="nw"
        )
        self.scroll_min_width = 900
        outer.bind("<Configure>", self._on_scroll_content_configure)
        self.scroll_canvas.bind("<Configure>", self._on_scroll_canvas_configure)
        self.root.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.root.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")
        self.root.bind("<Button-4>", self._on_linux_scroll_up, add="+")
        self.root.bind("<Button-5>", self._on_linux_scroll_down, add="+")

        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text="Input mode").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=2)
        self.input_mode = ttk.Combobox(
            outer,
            state="readonly",
            values=("Use existing frame directory", "Generate 360-degree yaw frames from source image"),
        )
        self.input_mode.set("Use existing frame directory")
        self.input_mode.grid(row=0, column=1, columnspan=2, sticky="ew", pady=2)

        self.frame_dir = ttk.Entry(outer)
        self.source_image = ttk.Entry(outer)
        self.output_dir = ttk.Entry(outer)
        self._path_row(outer, 1, "Target frame directory", self.frame_dir, self._choose_frames)
        self._path_row(outer, 2, "Source image", self.source_image, self._choose_source)
        self._path_row(outer, 3, "Output directory", self.output_dir, self._choose_output)

        generation = ttk.LabelFrame(outer, text="Optional target-frame generation", padding=8)
        generation.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        generation.columnconfigure(1, weight=1)
        generation.columnconfigure(3, weight=1)
        self.frame_count = self._var_entry(generation, 0, 0, "Frame count", "48")
        self.frame_canvas = self._var_entry(generation, 0, 2, "Frame canvas (px)", "1024")
        self.frame_front = self._var_entry(generation, 1, 0, "Front image width (px)", "600")
        self.camera_distance = self._var_entry(generation, 1, 2, "Perspective distance", "4.0")
        ttk.Label(generation, text="Intensity mapping").grid(row=2, column=0, sticky="w", padx=(0, 4), pady=2)
        self.mapping = ttk.Combobox(generation, state="readonly", values=MAPPING_MODES)
        self.mapping.set("invert grayscale")
        self.mapping.grid(row=2, column=1, columnspan=3, sticky="ew", pady=2)

        note = (
            "Film mode is intentionally Gerchberg-Saxton only. Target frames can be supplied directly "
            "or generated as an evenly sampled vertical-axis rotation. The normal DOE Generator remains "
            "available for Lens, Grating, FZP and Vortex designs."
        )
        ttk.Label(outer, text=note, wraplength=900, justify=LEFT).grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=(6, 10)
        )

        optics = ttk.LabelFrame(outer, text="GS optics", padding=8)
        optics.grid(row=6, column=0, columnspan=3, sticky="nsew")
        optics.columnconfigure(1, weight=1)
        optics.columnconfigure(3, weight=1)
        self.width = self._var_entry(optics, 0, 0, "DOE width (px)", "512")
        self.height = self._var_entry(optics, 0, 2, "DOE height (px)", "512")
        self.pixel_nm = self._var_entry(optics, 1, 0, "DOE pixel size (nm)", "500")
        self.wavelength_nm = self._var_entry(optics, 1, 2, "Wavelength (nm)", "532")
        self.distance_mm = self._var_entry(optics, 2, 0, "Target z (mm)", "300")
        self.target_width_mm = self._var_entry(optics, 2, 2, "Target width (mm; 0=fit)", "50")
        ttk.Label(optics, text="Propagation mode").grid(row=3, column=0, sticky="w", padx=(0, 4), pady=2)
        self.propagation_mode = ttk.Combobox(
            optics,
            state="readonly",
            values=("Physical projection", "Same sampling"),
        )
        self.propagation_mode.set("Physical projection")
        self.propagation_mode.grid(row=3, column=1, sticky="ew", padx=(0, 10), pady=2)
        self.iterations = self._var_entry(optics, 3, 2, "GS iterations", "50")
        self.seed = self._var_entry(optics, 4, 0, "GS seed", "0")
        self.projection_info = ttk.Label(optics, text="", wraplength=840, justify=LEFT)
        self.projection_info.grid(row=4, column=2, columnspan=2, sticky="ew", pady=2)

        target = ttk.LabelFrame(outer, text="Target plane", padding=8)
        target.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        target.columnconfigure(1, weight=1)
        target.columnconfigure(3, weight=1)
        self.target_x = self._var_entry(target, 0, 0, "Target X (mm)", "0")
        self.target_y = self._var_entry(target, 0, 2, "Target Y (mm)", "0")
        self.pan = self._var_entry(target, 1, 0, "Target pan (deg)", "0")
        self.tilt = self._var_entry(target, 1, 2, "Target tilt (deg)", "0")
        ttk.Label(
            target,
            text="Physical projection currently supports a parallel target plane (pan = tilt = 0). Tilted targets remain available in Same sampling mode.",
            wraplength=840,
            justify=LEFT,
        ).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(4, 0))

        brightness = ttk.LabelFrame(outer, text="Brightness analysis", padding=8)
        brightness.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
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
            wraplength=870,
            justify=LEFT,
        ).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(5, 0))

        layout = ttk.LabelFrame(outer, text="Disc layout", padding=8)
        layout.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        layout.columnconfigure(1, weight=1)
        layout.columnconfigure(3, weight=1)
        self.ring_pitch = self._var_entry(layout, 0, 0, "Ring pitch (mm)", "2.5")
        self.ring_radius = self._var_entry(layout, 0, 2, "Ring radius (mm; 0=auto)", "0")
        ttk.Label(layout, text="DOE orientation").grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
        self.orientation = ttk.Combobox(layout, state="readonly", values=("tangential", "radial", "fixed"))
        self.orientation.set("tangential")
        self.orientation.grid(row=1, column=1, sticky="ew", pady=2)

        buttons = ttk.Frame(outer)
        buttons.grid(row=10, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(buttons, text="Analyze frames", command=self._analyze).pack(side=LEFT)
        ttk.Button(buttons, text="Run GS batch", command=self._run).pack(side=RIGHT)

        self.progress = ttk.Progressbar(outer, orient=HORIZONTAL, mode="determinate", maximum=100)
        self.progress.grid(row=11, column=0, columnspan=3, sticky="ew")
        self.status = ttk.Label(outer, text="Ready.")
        self.status.grid(row=12, column=0, columnspan=3, sticky="w", pady=(4, 4))
        self.log = ScrolledText(outer, height=8, wrap="word")
        self.log.grid(row=13, column=0, columnspan=3, sticky="nsew")

        for entry in (self.width, self.height, self.pixel_nm, self.wavelength_nm, self.distance_mm, self.target_width_mm):
            entry.bind("<KeyRelease>", lambda _event: self._update_projection_info())
        self.propagation_mode.bind("<<ComboboxSelected>>", lambda _event: self._update_projection_info())
        self._update_projection_info()

        # Capture the natural requested width once the controls exist. Narrower
        # windows then expose the horizontal scrollbar instead of clipping.
        self.root.update_idletasks()
        self.scroll_min_width = max(self.scroll_min_width, outer.winfo_reqwidth())
        self._sync_scroll_content_width()

    def _on_scroll_content_configure(self, _event=None):
        self._sync_scroll_content_width()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_scroll_canvas_configure(self, _event=None):
        self._sync_scroll_content_width()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _sync_scroll_content_width(self):
        if not hasattr(self, "scroll_canvas"):
            return
        viewport_width = max(1, self.scroll_canvas.winfo_width())
        requested_width = max(self.scroll_min_width, self.scroll_content.winfo_reqwidth())
        target_width = max(viewport_width, requested_width)
        current_width = float(self.scroll_canvas.itemcget(self.scroll_window, "width") or 0)
        if abs(current_width - target_width) > 1.0:
            self.scroll_canvas.itemconfigure(self.scroll_window, width=target_width)

    def _on_mousewheel(self, event):
        if hasattr(self, "log") and event.widget is self.log:
            return
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            self.scroll_canvas.yview_scroll(direction * 3, "units")

    def _on_shift_mousewheel(self, event):
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            self.scroll_canvas.xview_scroll(direction * 3, "units")

    def _on_linux_scroll_up(self, event):
        if hasattr(self, "log") and event.widget is self.log:
            return
        self.scroll_canvas.yview_scroll(-3, "units")

    def _on_linux_scroll_down(self, event):
        if hasattr(self, "log") and event.widget is self.log:
            return
        self.scroll_canvas.yview_scroll(3, "units")

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

    def _update_projection_info(self):
        try:
            width = int(self.width.get())
            height = int(self.height.get())
            pixel_nm = float(self.pixel_nm.get())
            wavelength_nm = float(self.wavelength_nm.get())
            distance_mm = float(self.distance_mm.get())
            target_width_mm = float(self.target_width_mm.get())
            if self.propagation_mode.get() == "Physical projection":
                info = physical_projection_sampling(width, height, pixel_nm, wavelength_nm, distance_mm)
                samples = (
                    target_width_mm * 1000.0 / info["target_pixel_size_x_um"]
                    if target_width_mm > 0 else None
                )
                text = (
                    "Target sampling: {:.3f} x {:.3f} um/px; field: {:.3f} x {:.3f} mm".format(
                        info["target_pixel_size_x_um"],
                        info["target_pixel_size_y_um"],
                        info["target_field_width_mm"],
                        info["target_field_height_mm"],
                    )
                )
                if samples is not None:
                    text += "; {:.1f} samples across requested width".format(samples)
                if info["sampling_warning"]:
                    text += "; WARNING: " + info["sampling_warning"]
            else:
                pixel_um = pixel_nm / 1000.0
                field_width_mm = width * pixel_um / 1000.0
                field_height_mm = height * pixel_um / 1000.0
                text = "Same sampling: {:.3f} um/px; field: {:.6f} x {:.6f} mm".format(
                    pixel_um, field_width_mm, field_height_mm
                )
            self.projection_info.config(text=text)
        except Exception:
            self.projection_info.config(text="Projection sampling: enter valid optical parameters.")

    def _choose_frames(self):
        path = filedialog.askdirectory(title="Select directory with target frames")
        if path:
            self.frame_dir.delete(0, END)
            self.frame_dir.insert(0, path)
            if not self.output_dir.get().strip():
                self.output_dir.insert(0, str(Path(path).parent / "film_batch_output"))

    def _choose_source(self):
        path = filedialog.askopenfilename(
            title="Select source image",
            filetypes=(("Images", "*.png *.tif *.tiff *.jpg *.jpeg *.bmp"), ("All files", "*.*")),
        )
        if path:
            self.source_image.delete(0, END)
            self.source_image.insert(0, path)
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
            target_width_um=float(self.target_width_mm.get()) * 1000.0,
            propagation_mode=self.propagation_mode.get().strip().lower(),
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

    def _prepare_frame_directory(self):
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            raise ValueError("Select an output directory.")

        if self.input_mode.get() == "Generate 360-degree yaw frames from source image":
            source = self.source_image.get().strip()
            if not source:
                raise ValueError("Select a source image.")
            frames_dir = Path(output_dir) / "frames_raw"
            metadata = generate_yaw_frames(
                source,
                frames_dir,
                frame_count=int(self.frame_count.get()),
                canvas_px=int(self.frame_canvas.get()),
                front_size_px=float(self.frame_front.get()),
                camera_distance=float(self.camera_distance.get()),
                mapping=self.mapping.get(),
            )
            self._append(
                f"Generated {metadata['frame_count']} target frames in {frames_dir}."
            )
            return str(frames_dir)

        frame_dir = self.frame_dir.get().strip()
        if not frame_dir:
            raise ValueError("Select a target frame directory.")
        return frame_dir

    def _analyze(self):
        try:
            config = self._config()
            frame_dir = self._prepare_frame_directory()
            output_dir = self.output_dir.get().strip()
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
            output_dir = self.output_dir.get().strip()
            if not output_dir:
                raise ValueError("Select an output directory.")

            self.progress["value"] = 0
            self.log.delete("1.0", END)
            self._append("Starting GS-only film batch...")
            if config.propagation_mode == "physical projection":
                self._append("Propagation: physical projection (scaled Fresnel).")
            else:
                self._append("Propagation: legacy same sampling.")
            frame_dir = self._prepare_frame_directory()
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
            if summary.get("physical_projection_sampling"):
                sampling = summary["physical_projection_sampling"]
                self._append(
                    "Physical target sampling: {:.3f} um/px; field {:.3f} mm wide.".format(
                        sampling["target_pixel_size_x_um"],
                        sampling["target_field_width_mm"],
                    )
                )
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
