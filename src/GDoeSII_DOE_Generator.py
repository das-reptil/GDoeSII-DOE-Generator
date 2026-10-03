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
        self.root.geometry("1180x900")
        self.root.resizable(False, False)
        self.phase = None
        self.simulation = None
        self.metadata = None
        self.target_path = None
        self.phase_photo = None
        self.sim_photo = None
        self._build()

    def _build(self):
        outer = Frame(self.root, padx=10, pady=10)
        outer.pack(fill=BOTH, expand=True)
        left = Frame(outer, padx=10, pady=10, relief=RIDGE, bd=1)
        left.pack(side=LEFT, fill=Y)
        right = Frame(outer, padx=10, pady=10)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
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
        self.n_doe = DoubleVar(value=1.52)
        self.n_env = DoubleVar(value=1.0)
        self.offset_mode = StringVar(value="None")
        self.theta_x = DoubleVar(value=0.0)
        self.theta_y = DoubleVar(value=0.0)
        self.offset_x = DoubleVar(value=0.0)
        self.offset_y = DoubleVar(value=0.0)
        self.status = StringVar(value="Ready.")
        self.offset_info = StringVar(value="On-axis")
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
        ttk.OptionMenu(left, self.offset_mode, "None", "None", "Angle", "Target-plane distance", command=lambda *_: self._update_offset()).grid(row=row, column=1, sticky=EW); row += 1
        row = self._entry(row, "Theta X (deg)", self.theta_x)
        row = self._entry(row, "Theta Y (deg)", self.theta_y)
        row = self._entry(row, "Target X offset (mm)", self.offset_x)
        row = self._entry(row, "Target Y offset (mm)", self.offset_y)
        ttk.Label(left, textvariable=self.offset_info, wraplength=280, justify=LEFT).grid(row=row, column=0, columnspan=2, sticky=W, pady=4); row += 1
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
        ttk.Label(title, text="16-bit phase map", font=("calibri", 14, "bold")).grid(row=0, column=0, padx=(0, 230), sticky=W)
        ttk.Label(title, text="Local target-plane simulation", font=("calibri", 14, "bold")).grid(row=0, column=1, sticky=W)
        images = Frame(right); images.pack(fill=X, pady=10)
        self.phase_label = Label(images, text="Generate a DOE", width=45, height=20, relief=SUNKEN, bd=1)
        self.phase_label.grid(row=0, column=0, padx=(0, 15))
        self.sim_label = Label(images, text="Simulation preview", width=45, height=20, relief=SUNKEN, bd=1)
        self.sim_label.grid(row=0, column=1)
        self.info = Text(right, width=88, height=18); self.info.pack(fill=BOTH, expand=True)
        self._set_info("Generate a phase-only DOE. The exported phase map contains any off-axis steering ramp; the simulation stays centered in local target coordinates.")

        for var in (self.theta_x, self.theta_y, self.offset_x, self.offset_y, self.pixel_nm, self.wavelength_nm, self.distance_mm):
            var.trace_add("write", lambda *_: self._update_offset())
        for var in (self.wavelength_nm, self.n_doe, self.n_env):
            var.trace_add("write", lambda *_: self._update_relief())
        self._update_offset(); self._update_relief()

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
        return apply_phase_offset(
            np.zeros(shape), self.pixel_nm.get(), self.wavelength_nm.get(),
            offset_mode=self._mode(), theta_x_deg=self.theta_x.get(), theta_y_deg=self.theta_y.get(),
            offset_x_mm=self.offset_x.get(), offset_y_mm=self.offset_y.get(), distance_mm=self.distance_mm.get(),
        )[2]

    def _update_offset(self):
        try:
            i = self._offset()
            if i["mode"] == "none":
                self.offset_info.set("On-axis: no steering ramp"); return
            text = "Theta X: {:.3f} deg\nTheta Y: {:.3f} deg\nTotal angle: {:.3f} deg".format(i["theta_x_deg"], i["theta_y_deg"], i["total_angle_deg"])
            if i["period_diag_um"] is not None:
                text += "\nRamp period diag: {:.3f} um\nPixels / period diag: {:.2f}".format(i["period_diag_um"], i["pixels_per_period_diag"])
            if i["sampling_warning"]:
                text += "\nWARNING: " + i["sampling_warning"]
            self.offset_info.set(text)
        except Exception as exc:
            self.offset_info.set("Offset invalid: " + str(exc))

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
        kind = self.kind.get(); sim = None; target_info = None
        if kind == "Lens":
            phase = lens_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
        elif kind == "Grating":
            phase = grating_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.period_um.get(), self.angle_deg.get())
        elif kind == "Fresnel Zone Plate":
            phase = fresnel_zone_plate_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
        elif kind == "Vortex":
            phase = vortex_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.charge.get())
        elif kind == "Vortex + Lens":
            phase = wrap_phase(
                lens_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
                + vortex_phase(p["width_px"], p["height_px"], p["pixel_size_nm"], self.charge.get())
            )
        else:
            if not self.target_path:
                raise ValueError("Select a target image first.")
            target, target_info = load_target_intensity(
                self.target_path,
                p["width_px"],
                p["height_px"],
                pixel_size_nm=p["pixel_size_nm"],
                target_width_um=self.target_width_um.get(),
                return_info=True,
            )
            phase, sim = gerchberg_saxton_phase(target, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"], iterations=self.iterations.get(), seed=0, progress_callback=self._progress)
        return wrap_phase(phase), sim, target_info

    def _progress(self, current, total):
        self.progress.set(100.0 * current / total); self.status.set("Gerchberg-Saxton iteration {} / {}".format(current, total)); self.root.update_idletasks()

    def _generate(self):
        try:
            p = self._params(); self.progress.set(0); base, sim, target_info = self._base_phase(p)
            phase, _, offset = apply_phase_offset(base, p["pixel_size_nm"], p["wavelength_nm"], offset_mode=self._mode(), theta_x_deg=self.theta_x.get(), theta_y_deg=self.theta_y.get(), offset_x_mm=self.offset_x.get(), offset_y_mm=self.offset_y.get(), distance_mm=p["distance_mm"])
            if sim is None:
                sim = simulate_phase(base, p["pixel_size_nm"], p["wavelength_nm"], p["distance_mm"])
            self.phase, self.simulation = phase, sim
            self.metadata = {"type": self.kind.get(), **p, "offset": offset}
            if self.kind.get() == "Grating": self.metadata.update(grating_period_um=float(self.period_um.get()), grating_angle_deg=float(self.angle_deg.get()))
            if self.kind.get() in ("Vortex", "Vortex + Lens"):
                self.metadata["vortex_charge"] = int(self.charge.get())
            if self.kind.get() == "Vortex + Lens":
                self.metadata.update(focal_length_mm=float(p["distance_mm"]), phase_combination="lens + vortex")
            if self.kind.get() == "Arbitrary Image (GS)":
                self.metadata.update(
                    gs_iterations=int(self.iterations.get()),
                    target_file=os.path.basename(self.target_path),
                    target_geometry=target_info,
                )
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
            ]
            if self.kind.get() in ("Vortex", "Vortex + Lens"):
                lines.append("Vortex charge: {}".format(int(self.charge.get())))
            if self.kind.get() == "Vortex + Lens":
                lines.append("Focused vortex: lens + azimuthal vortex phase; simulation plane = focal plane.")
            if target_info is not None:
                requested = target_info["requested_width_um"]
                mode_text = "auto fit" if requested is None else "requested {:.3f} um width".format(requested)
                lines.append(
                    "GS target: {:.3f} x {:.3f} um ({} x {} px; {})".format(
                        target_info["actual_width_um"],
                        target_info["actual_height_um"],
                        target_info["target_width_px"],
                        target_info["target_height_px"],
                        mode_text,
                    )
                )
            if offset["mode"] == "target-plane distance": lines.append("Target X/Y: {:.4f} / {:.4f} mm; ray: {:.4f} mm".format(offset["offset_x_mm"], offset["offset_y_mm"], offset["ray_length_mm"]))
            if offset["period_diag_um"] is not None: lines.append("Ramp diag: {:.4f} um; {:.3f} px/period".format(offset["period_diag_um"], offset["pixels_per_period_diag"]))
            if offset["sampling_warning"]: lines.append("WARNING: " + offset["sampling_warning"])
            lines.append("Simulation is centered in local target coordinates.")
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
