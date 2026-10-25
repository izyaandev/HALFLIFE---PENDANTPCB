"""Makes the README renders from the CadQuery model (software renderer, no GPU needed)."""
import os, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import pendant_case as pc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "images")
os.makedirs(OUT, exist_ok=True)

def to_mesh(wp):
    v, t = wp.val().tessellate(0.02, 0.1)
    return trimesh.Trimesh(vertices=[(p.x, p.y, p.z) for p in v], faces=t, process=False)

printed = {"base": pc.make_base(), "lid": pc.make_lid(), "plunger": pc.make_plunger(),
           "pipe": pc.make_lightpipe(), "slider": pc.make_slider()}
refs = pc.ref_parts()
M = {k: to_mesh(v) for k, v in {**printed, **refs}.items()}

COL = {"base": "#4b5563", "lid": "#14a39a", "plunger": "#f59e0b", "slider": "#f59e0b", "pipe": "#ef4444",
       "pcb": "#15803d", "header_L": "#111827", "header_R": "#111827", "mic_header": "#111827",
       "xiao": "#1d4ed8", "usbc": "#cbd5e1", "battery": "#9ca3af", "mic_module": "#7c3aed",
       "switch": "#374151", "button": "#374151", "led": "#ef4444", "jst": "#e5e7eb"}

def trim(path, pad=60):
    """crop the empty background around the model (background is a vertical gradient)"""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB")).astype(int)
    bg = im[:, 2:3, :]                              # background colour of each row, from the left edge
    mask = (np.abs(im - bg).sum(axis=2) > 24)
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad, im.shape[0]), max(xs.min() - pad, 0), min(xs.max() + pad, im.shape[1])
    Image.fromarray(im[y0:y1, x0:x1].astype("uint8")).save(path)

def render(items, fn, azim=-35, elev=28, title="", size=(1800, 1800), parallel=True, zoom=1.0):
    """items: list of (trimesh, hex colour). Real z-buffer render via pyvista."""
    import pyvista as pv
    pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("#f4f4f1", top="#dfe3e8")
    allb = np.array([m.bounds for m, _ in items])
    lo, hi = allb[:, 0].min(axis=0), allb[:, 1].max(axis=0)
    for m, color in items:
        pdm = pv.wrap(m)
        pl.add_mesh(pdm, color=color, smooth_shading=False, show_edges=False,
                    ambient=0.28, diffuse=0.75, specular=0.25, specular_power=18)
    c = (lo + hi) / 2
    r = np.linalg.norm(hi - lo) * 1.6
    a, e = np.radians(azim), np.radians(elev)
    pos = c + r * np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    pl.camera_position = [tuple(pos), tuple(c), (0, 0, 1)]
    if parallel:
        pl.camera.enable_parallel_projection()
    pl.reset_camera()
    pl.camera.zoom(zoom)
    pl.camera.zoom(zoom)
    try:
        pl.enable_anti_aliasing("ssaa")
    except Exception:
        pass
    path = os.path.join(OUT, fn)
    pl.screenshot(path)
    pl.close()
    trim(path)
    print("wrote", fn)

def shift(mesh, dz):
    m = mesh.copy(); m.apply_translation((0, 0, dz)); return m

# 1) assembled case (closed)
render([(M[k], COL[k]) for k in ("base", "lid", "plunger", "slider", "pipe")],
       "case-assembled.png", azim=58, elev=24, zoom=1.0, title="Pendant case, assembled (33.4 x 64.9 x 30.8 mm)", size=(1800, 1500))

# 2) exploded view
off = {"battery": 10, "base": 0, "pcb": 22, "header_L": 22, "header_R": 22, "mic_header": 22, "switch": 22,
       "button": 22, "led": 22, "jst": 22, "xiao": 42, "usbc": 42, "mic_module": 42,
       "plunger": 66, "slider": 66, "pipe": 66, "lid": 78}
render([(shift(M[k], d), COL[k]) for k, d in off.items()], "case-exploded.png", azim=52, elev=20, zoom=1.0,
       title="Exploded view: base, battery, carrier PCB, XIAO, lid and small parts", size=(1500, 2100))

# 3) cutaway through x = 0 (we look at the cut face from +x)
HALF = pc.box(-80, 0, -80, 80, -5, 60)   # keep everything with x <= 0
ALL = {**printed, **refs}
def cut(k):
    return to_mesh(ALL[k].intersect(HALF))
keys = ("base", "lid", "pcb", "header_L", "header_R", "xiao", "usbc", "battery",
        "mic_module", "mic_header", "button", "plunger", "pipe")
items = []
for k in keys:
    try:
        m = cut(k)
        if len(m.faces): items.append((m, COL[k]))
    except Exception:
        pass
render(items, "case-cutaway.png", azim=14, elev=14, zoom=1.0, title="Cutaway at the centre line: battery under the PCB, XIAO on top", size=(1800, 1500))

# 4) printable parts laid out for slicing
parts = {"base": (0, 0), "lid": (50, 0), "plunger": (95, 0), "slider": (95, 12), "pipe": (95, -12)}
flat = []
for k, (x, y) in parts.items():
    m = M[k].copy()
    if k == "lid": m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
    m.apply_translation(-m.bounds.mean(axis=0) * np.array([1, 1, 0])); m.apply_translation((x, y, -m.bounds[0][2]))
    flat.append((m, COL[k]))
render(flat, "printable-parts.png", azim=-30, elev=38, zoom=1.0, title="Printable parts (lid is flipped for printing)", size=(2000, 1300))
