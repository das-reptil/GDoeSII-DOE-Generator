import math
import os
from tkinter import *
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

from gdoesii_doe import (
    TWO_PI,
    apply_phase_offset,
    fresnel_zone_plate_phase,
    gerchberg_saxton_phase,
    grating_phase,
    lens_phase,
    load_target_intensity,
    phase_to_uint16,
    save_phase_png,
    simulate_phase,
    vortex_phase,
    wrap_phase,
)
from gdoesii_grayscribe import export_grayscribex_normalized, phase_span_to_height_nm
from gdoesii_tilt import gerchberg_saxton_tilted_phase, simulate_phase_tilted, target_plane_geometry

APP_TITLE = "GDoeSII DOE Generator"


def preview_image(values, max_size=340):
    values = np.asarray(values, dtype=np.uint16)
    img = Image.fromarray((values >> 8).astype(np.uint8), mode="L")
    w, h = img.size
    scale = min(max_size / w, max_size / h, 1.0)
    img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self._configure_window()
        self.phase = None
        self.simulation = None
        self.metadata = None
        self.target_path = None
        self.phase_photo = None
        self.sim_photo = None
        self._build()

    def _configure_window(self):
        """Choose a useful initial size without exceeding the current screen."""
        screen_w = max(1, self.root.winfo_screenwidth())
        screen_h = max(1, self.root.winfo_screenheight())
        width = min(1180, max(640, screen_w - 80), screen_w)
        height = min(900, max(520, screen_h - 120), screen_h)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(700, width), min(500, height))
        self.root.resizable(True, True)

    def _build(self):
        shell = Frame(self.root)
        shell.pack(fill=BOTH, expand=True)
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)

        self.canvas = Canvas(shell, highlightthickness=0)
        v_scroll = ttk.Scrollbar(shell, orient=VERTICAL, command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(shell, orient=HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.canvas.grid(row=0, column=0, sticky=NSEW)
        v_scroll.grid(row=0, column=1, sticky=NS)
        h_scroll.grid(row=1, column=0, sticky=EW)

        outer = Frame(self.canvas, padx=10, pady=10)
        self.scroll_content = outer
        self.canvas_window = self.canvas.create_window((0, 0), window=outer, anchor=NW)
        outer.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

        left = Frame(outer, padx=10, pady=10, relief=RIDGE, bd=1)
        left.grid(row=0, column=0, sticky=N + S + W, padx=(0, 10))
        right = Frame(outer, padx=10, pady=10)
        right.grid(row=0, column=1, sticky=NSEW)
        self.left = left

        self.kind = StringVar(value="Lens")
        self.width = IntVar(value=512)
        self.height = IntVar(value=512)
        self.pixel_nm = DoubleVar(value=500.0)
        self.wavelength_nm = DoubleVar(value=633.0)
        self.distance_mm = DoubleVar(value=10.0)
        self.period_um = DoubleVar(value=20.0)
        self.angle_deg = DoubleVar(value=0.0)
        self.charge = IntVar(value=1)
        self.iterations = IntVar(value=50)
        self.target_width_um = DoubleVar(value=0.0)
        self.target_pan_deg = DoubleVar(value=0.0)
        self.target_tilt_deg = DoubleVar(value=0.0)
        self.n_doe = DoubleVar(value=1.52)
        self.n_env = DoubleVar(value=1.0)
        self.offset_mode = StringVar(value="None")
        self.theta_x = DoubleVar(value=0.0)
        self.theta_y = DoubleVar(value=0.0)
        self.offset_x = DoubleVar(value=0.0)
        self.offset_y = DoubleVar(value=0.0)
        self.status = StringVar(value="Ready.")
        self.offset_info = StringVar(value="On-axis")
        self.target_plane_info = StringVar(value="Target plane parallel to DOE")
        self.relief_info = StringVar(value="")
        self.progress = DoubleVar(value=0.0)

        row = 0
        ttk.Label(left, text="DOE Generator", font=("calibri", 14, "bold")).grid(row=row, column=0, columnspan=2, sticky=W, pady=(0, 8)); row += 1
        ttk.Label(left, text="Type").grid(row=row, column=0, sticky=W)
        ttk.OptionMenu(left, self.kind, "Lens", "Lens", "Grating", "Fresnel Zone Plate", "Vortex", "Vortex + Lens", "Arbitrary Image (GS)").grid(row=row, column=1, sticky=EW); row += 1
        for label, var in (
            ("Width (px)", self.width), ("Height (px)", self.height),
            ("Pixel size (nm)", self.pixel_nm), ("Wavelength (nm)", self.wavelength_nm),
            ("Focal / target z (mm)", self.distance_mm), ("Grating period (um)", self.period_um),
            ("Grating angle (deg)", self.angle_deg), ("Vortex charge", self.charge),
            ("GS iterations", self.iterations), ("GS target width (um; 0=fit)", self.target_width_um),
        ):
            row = self._entry(row, label, var)

        ttk.Button(left, text="Select target image", command=self._select_target).grid(row=row, column=0, columnspan=2, sticky=EW, pady=4); row += 1
        self.target_label = ttk.Label(left, text="No target image selected", wraplength=260)
        self.target_label.grid(row=row, column=0, columnspan=2, sticky=W); row += 1
        ttk.Separator(left).grid(row=row, column=0, columnspan=2, sticky=EW, pady=7); row += 1

        ttk.Label(left, text="Off-axis steering", font=("calibri", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky=W); row += 1
        ttk.Label(left, text="Mode").grid(row=row, column=0, sticky=W)
        ttk.OptionMenu(left, self.offset_mode, "None", "None", "Angle", "Target-plane distance", command=lambda *_: (self._update_offset(), self._update_target_plane())).grid(row=row, column=1, sticky=EW); row += 1
        row = self._entry(row, "Theta X (deg)", self.theta_x)
        row = self._entry(row, "Theta Y (deg)", self.theta_y)
        row = self._entry(row, "Target X offset (mm)", self.offset_x)
        row = self._entry(row, "Target Y offset (mm)", self.offset_y)
        ttk.Label(left, textvariable=self.offset_info, wraplength=280, justify=LEFT).grid(row=row, column=0, columnspan=2, sticky=W, pady=4); row += 1
        ttk.Separator(left).grid(row=row, column=0, columnspan=2, sticky=EW, pady=7); row += 1

        ttk.Label(left, text="Target plane orientation", font=("calibri", 12, "bold")).grid(row=row, column=0, columnspan=2, sticky=W); row += 1
        row = self._entry(row, "Target pan (deg)", self.target_pan_deg)
        row = self._entry(row, "Target tilt (deg)", self.target_tilt_deg)
        ttk.Label(left, textvariable=self.target_plane_info, wraplength=280, justify=LEFT).grid(row=row, column=0, columnspan=2, sticky=W, pady=4); row += 1
        ttk.Separator(left).grid(row=row, column=0, columnspan=2, sticky=EW, pady=7); row += 1

        row = self._entry(row, "DOE index", self.n_doe)
        row = self._entry(row, "Environment index", self.n_env)
        ttk.Label(left, textvariable=self.relief_info, wraplength=280, justify=LEFT).grid(row=row, column=0, columnspan=2, sticky=W); row += 1
        ttk.Progressbar(left, variable=self.progress, maximum=100, length=270).grid(row=row, column=0, columnspan=2, sticky=EW, pady=5); row += 1
        ttk.Button(left, text="Generate DOE", command=self._generate).grid(row=row, column=0, columnspan=2, sticky=EW, pady=3); row += 1
        ttk.Button(left, text="Save 16-bit Phase PNG", command=self._save_phase).grid(row=row, column=0, columnspan=2, sticky=EW, pady=3); row += 1
        ttk.Button(left, text="Export GrayScribeX", command=self._export).grid(row=row, column=0, columnspan=2, sticky=EW, pady=3); row += 1
        ttk.Label(left, textvariable=self.status, wraplength=280, justify=LEFT).grid(row=row, column=0, columnspan=2, sticky=W, pady=(7, 0))
        left.columnconfigure(1, weight=1)

        title = Frame(right); title.pack(fill=X)
        title.columnconfigure(0, weight=1); title.columnconfigure(1, weight=1)
        ttk.Label(title, text="16-bit phase map", font=("calibri", 14, "bold")).grid(row=0, column=0, padx=(0, 15), sticky=W)
        ttk.Label(title, text="Target-plane simulation", font=("calibri", 14, "bold")).grid(row=0, column=1, sticky=W)
        images = Frame(right); images.pack(fill=X, pady=10)
        images.columnconfigure(0, weight=1); images.columnconfigure(1, weight=1)
        self.phase_label = Label(images, text="Generate a DOE", width=45, height=20, relief=SUNKEN, bd=1)
        self.phase_label.grid(row=0, column=0, padx=(0, 8), sticky=NSEW)
        self.sim_label = Label(images, text="Simulation preview", width=45, height=20, relief=SUNKEN, bd=1)
        self.sim_label.grid(row=0, column=1, padx=(8, 0), sticky=NSEW)
        self.info = Text(right, width=88, height=18); self.info.pack(fill=BOTH, expand=True)
        self._set_info("Generate a phase-only DOE. Off-axis steering and target-plane pan/tilt are stored in metadata; tilted GS uses rotated angular-spectrum propagation.")

        for var in (self.theta_x, self.theta_y, self.offset_x, self.offset_y, self.pixel_nm, self.wavelength_nm, self.distance_mm):
            var.trace_add("write", lambda *_: (self._update_offset(), self._update_target_plane()))
        for var in (self.target_pan_deg, self.target_tilt_deg):
            var.trace_add("write", lambda *_: self._update_target_plane())
        for var in (self.wavelength_nm, self.n_doe, self.n_env):
            var.trace_add("write", lambda *_: self._update_relief())
        self._update_offset(); self._update_target_plane(); self._update_relief()

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        req_w = self.scroll_content.winfo_reqwidth()
        req_h = self.scroll_content.winfo_reqheight()
        self.canvas.itemconfigure(self.canvas_window, width=max(event.width, req_w), height=max(event.height, req_h))

    def _entry(self, row, text, var):
        ttk.Label(self.left, text=text).grid(row=row, column=0, sticky=W, pady=1)
        ttk.Entry(self.left, textvariable=var, width=14).grid(row=row, column=1, sticky=EW, pady=1)
        return row + 1

    def _set_info(self, text):
        self.info.config(state=NORMAL); self.info.delete("1.0", END); self.info.insert(END, text); self.info.config(state=DISABLED)

    def _select_target(self):
        path = filedialog.askopenfilename(title="Select target intensity image", filetypes=(("Images", "*.png *.tif *.tiff *.jpg *.jpeg *.bmp"), ("All files", "*.*")))
        if path:
            self.target_path = path; self.target_label.config(text=os.path.basename(path)); self.status.set("Target: " + os.path.basename(path))

    def _mode(self):
        return {"Angle": "angle", "Target-plane distance": "distance"}.get(self.offset_mode.get(), "none")

    def _offset(self, shape=(2, 2)):
        return apply_phase_offset(np.zeros(shape), self.pixel_nm.get(), self.wavelength_nm.get(), offset_mode=self._mode(), theta_x_deg=self.theta_x.get(), theta_y_deg=self.theta_y.get(), offset_x_mm=self.offset_x.get(), offset_y_mm=self.offset_y.get(), distance_mm=self.distance_mm.get())[2]

    def _target_center(self, distance_mm=None):
        z_mm = float(self.distance_mm.get() if distance_mm is None else distance_mm)
        mode = self._mode()
        if mode == "distance":
            return float(self.offset_x.get()), float(self.offset_y.get()), z_mm
        if mode == "angle":
            return z_mm * math.tan(math.radians(float(self.theta_x.get()))), z_mm * math.tan(math.radians(float(self.theta_y.get()))), z_mm
        return 0.0, 0.0, z_mm

    def _plane_is_tilted(self):
        return abs(float(self.target_pan_deg.get())) > 1e-12 or abs(float(self.target_tilt_deg.get())) > 1e-12

    def _plane_geometry(self, p, target_info=None):
        center_x, center_y, center_z = self._target_center(p["distance_mm"])
        kwargs = {}
        if target_info is not None and target_info.get("actual_width_um") is not None:
            kwargs["width_mm"] = float(target_info["actual_width_um"]) / 1000.0
            kwargs["height_mm"] = float(target_info["actual_height_um"]) / 1000.0
        return target_plane_geometry(center_z, pan_deg=self.target_pan_deg.get(), tilt_deg=self.target_tilt_deg.get(), center_x_mm=center_x, center_y_mm=center_y, pixel_size_nm=p["pixel_size_nm"], wavelength_nm=p["wavelength_nm"], **kwargs)

    def _update_offset(self):
        try:
            i = self._offset()
            if i["mode"] == "none":
                self.offset_info.set("On-axis: no steering ramp"); return
            text = "Theta X: {:.3f} deg\nTheta Y: {:.3f} deg\nTotal angle: {:.3f} deg".format(i["theta_x_deg"], i["theta_y_deg"], i["total_angle_deg"])
            if i["period_diag_um"] is not None:
                text += "\nRamp period diag: {:.3f} um\nPixels / period diag: {:.2f}".format(i["period_diag_um"], i["pixels_per_period_diag"])
            if i["sampling_warning"]: text += "\nWARNING: " + i["sampling_warning"]
            self.offset_info.set(text)
        except Exception as exc:
            self.offset_info.set("Offset invalid: " + str(exc))

    def _update_target_plane(self):
        try:
            center_x, center_y, center_z = self._target_center()
            info = target_plane_geometry(center_z, pan_deg=self.target_pan_deg.get(), tilt_deg=self.target_tilt_deg.get(), center_x_mm=center_x, center_y_mm=center_y, pixel_size_nm=self.pixel_nm.get(), wavelength_nm=self.wavelength_nm.get())
            normal = info["normal"]
            text = "Center X/Y/Z: {:.3f} / {:.3f} / {:.3f} mm\nNormal: [{:.4f}, {:.4f}, {:.4f}]".format(center_x, center_y, center_z, normal[0], normal[1], normal[2])
            sampling = info.get("sampling", {})
            minimum = sampling.get("minimum_pixels_per_carrier")
            if minimum is not None: text += "\nTilt carrier: {:.2f} px/period minimum".format(minimum)
            if sampling.get("sampling_warning"): text += "\nWARNING: " + sampling["sampling_warning"]
            self.target_plane_info.set(text)
        except Exception as exc:
            self.target_plane_info.set("Target plane invalid: " + str(exc))

    def _update_relief(self):
        try:
            relief = phase_span_to_height_nm(self.wavelength_nm.get(), self.n_doe.get(), 0.0, TWO_PI, environment_refractive_index=self.n_env.get())
            self.relief_info.set("Delta n: {:.4f}\nMax 2pi relief: {:.3f} um".format(self.n_doe.get() - self.n_env.get(), relief / 1000.0))
        except Exception:
            self.relief_info.set("Delta n / relief: invalid")

    def _params(self):
        p = dict(width_px=int(self.width.get()), height_px=int(self.height.get()), pixel_size_nm=float(self.pixel_nm.get()), wavelength_nm=float(self.wavelength_nm.get()), distance_mm=float(self.distance_mm.get()))
        if p["width_px"] < 2 or p["height_px"] < 2 or p["pixel_size_nm"] <= 0 or p["wavelength_nm"] <= 0 or p["distance_mm"] <= 0:
            raise ValueError("Width/height must be >=2 and pixel size, wavelength and target z must be positive.")
        if float(self.target_width_um.get()) < 0:
            raise ValueError("GS target width must be 0 (auto fit) or greater than 0 um.")
        return p

    def _base_phase(self, p):
        kind = self.kind.get(); sim = None; target_info = None; offset_embedded = False
        if kind == "Lens":
            phase = lens_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
        elif kind == "Grating":
            phase = grating_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.period_um.get(), self.angle_deg.get())
        elif kind == "Fresnel Zone Plate":
            phase = fresnel_zone_plate_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
        elif kind == "Vortex":
            phase = vortex_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.charge.get())
        elif kind == "Vortex + Lens":
            phase = wrap_phase(lens_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"]) + vortex_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.charge.get()))
        else:
            if not self.target_path: raise ValueError("Select a target image first.")
            target, target_info = load_target_intensity(self.target_path, p["width_px"], p["height_px"], pixel_size_nm=p["pixel_size_nm"], target_width_um=self.target_width_um.get(), return_info=True)
            if self._plane_is_tilted():
                center_x, center_y, _ = self._target_center(p["distance_mm"])
                phase, sim = gerchberg_saxton_tilted_phase(target, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"], pan_deg=self.target_pan_deg.get(), tilt_deg=self.target_tilt_deg.get(), center_x_mm=center_x, center_y_mm=center_y, iterations=self.iterations.get(), seed=0, progress_callback=self._progress)
                offset_embedded = True
            else:
                phase, sim = gerchberg_saxton_phase(target, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"], iterations=self.iterations.get(), seed=0, progress_callback=self._progress)
        return wrap_phase(phase), sim, target_info, offset_embedded

    def _progress(self, current, total):
        self.progress.set(100.0 * current / total); self.status.set("Gerchberg-Saxton iteration {} / {}".format(current, total)); self.root.update_idletasks()

    def _generate(self):
        try:
            p = self._params(); self.progress.set(0); base, sim, target_info, offset_embedded = self._base_phase(p)
            if offset_embedded:
                phase = base; offset = self._offset(); offset["embedded_in_tilted_gs"] = True
            else:
                phase, _, offset = apply_phase_offset(base, p["pixel_size_nm"], p["wavelength_nm"], offset_mode=self._mode(), theta_x_deg=self.theta_x.get(), theta_y_deg=self.theta_y.get(), offset_x_mm=self.offset_x.get(), offset_y_mm=self.offset_y.get(), distance_mm=p["distance_mm"])
            plane = self._plane_geometry(p, target_info)
            if sim is None:
                if self._plane_is_tilted():
                    center_x, center_y, _ = self._target_center(p["distance_mm"])
                    sim = simulate_phase_tilted(phase, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"], pan_deg=self.target_pan_deg.get(), tilt_deg=self.target_tilt_deg.get(), center_x_mm=center_x, center_y_mm=center_y)
                else:
                    sim = simulate_phase(base, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
            self.phase, self.simulation = phase, sim
            self.metadata = {"type": self.kind.get(), **p, "offset": offset, "target_plane": plane}
            if self.kind.get() == "Grating": self.metadata.update(grating_period_um=float(self.period_um.get()), grating_angle_deg=float(self.angle_deg.get()))
            if self.kind.get() in ("Vortex", "Vortex + Lens"): self.metadata["vortex_charge"] = int(self.charge.get())
            if self.kind.get() == "Vortex + Lens": self.metadata.update(focal_length_mm=float(p["distance_mm"]), phase_combination="lens + vortex")
            if self.kind.get() == "Arbitrary Image (GS)":
                self.metadata.update(gs_iterations=int(self.iterations.get()), target_file=os.path.basename(self.target_path), target_geometry=target_info, target_propagation="tilted angular spectrum" if self._plane_is_tilted() else "same-sampling Fresnel")
            self.phase_photo = preview_image(phase_to_uint16(phase)); self.sim_photo = preview_image(sim)
            self.phase_label.config(image=self.phase_photo, text="", width=self.phase_photo.width(), height=self.phase_photo.height())
            self.sim_label.config(image=self.sim_photo, text="", width=self.sim_photo.width(), height=self.sim_photo.height())
            relief = phase_span_to_height_nm(p["wavelength_nm"], self.n_doe.get(), 0.0, TWO_PI, environment_refractive_index=self.n_env.get())
            lines = [
                "Generator: {}".format(self.kind.get()),
                "Size: {} x {} px; pixel: {:.3f} nm".format(p["width_px"], p["height_px"], p["pixel_size_nm"]),
                "Physical size: {:.3f} x {:.3f} um".format(p["width_px"] * p["pixel_size_nm"] / 1000, p["height_px"] * p["pixel_size_nm"] / 1000),
                "Wavelength: {:.3f} nm; focal / target z: {:.4f} mm".format(p["wavelength_nm"], p["distance_mm"]),
                "Max 2pi relief: {:.3f} um".format(relief / 1000),
                "Offset mode: {}".format(offset["mode"]),
                "Theta X/Y: {:.4f} / {:.4f} deg; total: {:.4f} deg".format(offset["theta_x_deg"], offset["theta_y_deg"], offset["total_angle_deg"]),
                "Target pan/tilt: {:.4f} / {:.4f} deg".format(plane["pan_deg"], plane["tilt_deg"]),
                "Target center X/Y/Z: {:.4f} / {:.4f} / {:.4f} mm".format(*plane["center_mm"]),
                "Target normal: [{:.6f}, {:.6f}, {:.6f}]".format(*plane["normal"]),
            ]
            if self.kind.get() in ("Vortex", "Vortex + Lens"): lines.append("Vortex charge: {}".format(int(self.charge.get())))
            if self.kind.get() == "Vortex + Lens": lines.append("Focused vortex: lens + azimuthal vortex phase; simulation plane = focal plane.")
            if target_info is not None:
                requested = target_info["requested_width_um"]; mode_text = "auto fit" if requested is None else "requested {:.3f} um width".format(requested)
                lines.append("GS target: {:.3f} x {:.3f} um ({} x {} px; {})".format(target_info["actual_width_um"], target_info["actual_height_um"], target_info["target_width_px"], target_info["target_height_px"], mode_text))
            if plane.get("corners_mm"):
                for name in ("top_left", "top_right", "bottom_left", "bottom_right"):
                    lines.append("Target {}: [{:.4f}, {:.4f}, {:.4f}] mm".format(name, *plane["corners_mm"][name]))
            if offset["mode"] == "target-plane distance": lines.append("Target X/Y: {:.4f} / {:.4f} mm; ray: {:.4f} mm".format(offset["offset_x_mm"], offset["offset_y_mm"], offset["ray_length_mm"]))
            if offset["period_diag_um"] is not None: lines.append("Ramp diag: {:.4f} um; {:.3f} px/period".format(offset["period_diag_um"], offset["pixels_per_period_diag"]))
            if offset["sampling_warning"]: lines.append("WARNING: " + offset["sampling_warning"])
            plane_warning = plane.get("sampling", {}).get("sampling_warning")
            if plane_warning: lines.append("WARNING: " + plane_warning)
            if self.kind.get() == "Arbitrary Image (GS)" and self._plane_is_tilted(): lines.append("GS propagation: rotated angular spectrum with target-plane interpolation.")
            elif self._plane_is_tilted(): lines.append("Analytic phase is unchanged; preview is evaluated on the tilted target plane.")
            else: lines.append("Simulation is centered in local target coordinates.")
            self._set_info("\n".join(lines)); self.progress.set(100); self.status.set("DOE generated successfully.")
        except Exception as exc:
            self.progress.set(0); self.status.set("Error: " + str(exc)); messagebox.showerror(APP_TITLE, str(exc))

    def _require(self):
        if self.phase is None:
            messagebox.showinfo(APP_TITLE, "Generate a DOE first."); return False
        return True

    def _save_phase(self):
        if not self._require(): return
        path = filedialog.asksaveasfilename(title="Save 16-bit phase DOE", defaultextension=".png", filetypes=(("16-bit PNG", "*.png"),))
        if path:
            try:
                png, meta = save_phase_png(self.phase, path, self.metadata); self.status.set("Saved {} and {}".format(os.path.basename(png), os.path.basename(meta)))
            except Exception as exc: messagebox.showerror(APP_TITLE, str(exc))

    def _export(self):
        if not self._require(): return
        path = filedialog.asksaveasfilename(title="Export Quantum X / GrayScribeX height map", defaultextension=".png", filetypes=(("16-bit PNG", "*.png"),))
        if path:
            try:
                result = export_grayscribex_normalized(wrap_phase(self.phase) / TWO_PI, path, self.wavelength_nm.get(), self.n_doe.get(), 0.0, TWO_PI, pixel_size_nm=self.pixel_nm.get(), environment_refractive_index=self.n_env.get(), source_info={"type": "GDoeSII DOE Generator"}, extra_metadata=self.metadata)
                self.status.set("GrayScribeX export saved. Max relief {:.3f} um.".format(result["max_height_nm"] / 1000))
            except Exception as exc: messagebox.showerror(APP_TITLE, str(exc))


def main():
    root = Tk(); App(root); root.mainloop()


if __name__ == "__main__":
    main()
