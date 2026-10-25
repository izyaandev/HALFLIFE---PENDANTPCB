"""
Half Life pendant: parametric enclosure (CadQuery)

Run:  python pendant_case.py
Makes STEP + STL files for every printable part, a full assembly STEP, and
prints an interference check (any two parts that overlap = a design bug).

Coordinates match the PCB: origin is the centre of the carrier board,
x to the right, y toward the USB-C end, z up from the bottom of the case.
All sizes in mm. Sizes marked (ASSUMED) are typical values for parts I have
not measured, check them against your real parts before printing.
"""
import itertools, os
import cadquery as cq

# ---------------- board + case parameters ----------------
W, L, T = 28.0, 50.0, 1.6            # carrier pcb outline + thickness
R_PCB = 3.0                          # pcb corner radius
CLR = 0.3                            # clearance around the pcb
WALL = 2.4
PW, PL = W + 2 * CLR, L + 2 * CLR    # pocket for the pcb
OW, OL = PW + 2 * WALL, PL + 2 * WALL
R_POCK = R_PCB + CLR
R_OUT = R_POCK + WALL

FLOOR = 1.6                          # base floor thickness
BAT = (25.0, 40.0, 5.0)              # LiPo w, l, thickness (ASSUMED, ~502540 cell)
BAY_H = 6.5                          # battery bay height under the pcb
Z_BOARD = FLOOR + BAY_H              # pcb bottom sits on the ledge here
Z_PCB_TOP = Z_BOARD + T
LEDGE = 1.5                          # how far the ledge sticks in under the pcb edge

HDR_H = 8.5                          # 2.54 mm female header height (ASSUMED)
Z_HDR_TOP = Z_PCB_TOP + HDR_H
XIAO = (17.8, 21.0)                  # XIAO footprint
XIAO_STACK_H = 6.2                   # XIAO + Sense expansion board (ASSUMED)
XIAO_Y = 14.0                        # centre of the XIAO on the carrier
USB_Z = Z_HDR_TOP + 1.2 + 1.6       # centre height of the USB-C port

Z_SPLIT = 14.0                       # where base and lid meet
TONGUE_H, TONGUE_T = 2.0, 1.2
Z_CEIL_IN = 25.4                     # inside ceiling of the lid
Z_TOP = 27.0                         # outside top of the lid

# positions of things on the pcb (from the PCB design)
SW1 = (-8.0, -6.0)                   # privacy slide switch
SW2 = (0.0, -14.0)                   # bookmark button
LED = (-9.0, -17.0)                  # REC led
MIC = (0.0, -1.0)                    # mic header (module stands up on it)
JST = (9.0, -19.0)                   # battery connector

# ---------------- helpers ----------------
def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))

def rrect(w, l, r, z0, h, cx=0.0, cy=0.0):
    return (cq.Workplane("XY").workplane(offset=z0).center(cx, cy)
            .rect(w, l).extrude(h).edges("|Z").fillet(r))

def cyl(d, z0, z1, x=0.0, y=0.0):
    return (cq.Workplane("XY").workplane(offset=z0).center(x, y)
            .circle(d / 2).extrude(z1 - z0))

# ---------------- printable part 1: base ----------------
def make_base():
    b = rrect(OW, OL, R_OUT, 0, Z_SPLIT)
    b = b.cut(rrect(PW - 2 * LEDGE, PL - 2 * LEDGE, 1.5, FLOOR, Z_BOARD - FLOOR + 0.01))  # battery bay
    b = b.cut(rrect(PW, PL, R_POCK, Z_BOARD, Z_SPLIT - Z_BOARD + 0.1))                    # pcb pocket
    tongue = rrect(PW + 2 * TONGUE_T, PL + 2 * TONGUE_T, R_POCK + TONGUE_T, Z_SPLIT, TONGUE_H)
    tongue = tongue.cut(rrect(PW, PL, R_POCK, Z_SPLIT - 0.1, TONGUE_H + 0.2))
    b = b.union(tongue)
    # lanyard ear at the bottom end
    ey = -(OL / 2 + 4.0)
    ear = cyl(11.0, 0, 3.6, 0, ey).union(box(-5.5, 5.5, ey, -(OL / 2) + 1.0, 0, 3.6))
    b = b.union(ear).cut(cyl(3.4, -1, 5, 0, ey))
    # battery wire channel: bay -> under the ledge -> groove up the right wall
    b = b.cut(box(PW / 2 - 2.0, PW / 2 + 1.2, -22, -17, FLOOR + 1.5, Z_BOARD + 0.01))
    b = b.cut(box(PW / 2 - 0.01, PW / 2 + 1.2, -22, -17, Z_BOARD, 11.5))
    return b

# ---------------- printable part 2: lid ----------------
def make_lid():
    lid = rrect(OW, OL, R_OUT, Z_SPLIT, Z_TOP - Z_SPLIT)
    lid = lid.faces(">Z").edges().chamfer(1.0)
    ridge = box(-9.0, 9.0, MIC[1] - 2.8, MIC[1] + 2.8, Z_TOP - 1.0, 30.8)   # tall ridge for the mic module
    lid = lid.union(ridge)
    lid = lid.cut(rrect(PW + 2.6, PL + 2.6, R_POCK + 1.3, Z_SPLIT - 0.1, 16.0 - Z_SPLIT + 0.1))  # groove for the base tongue
    lid = lid.cut(rrect(PW, PL, R_POCK, 16.0 - 0.1, Z_CEIL_IN - 16.0 + 0.1))                     # main cavity
    lid = lid.cut(box(-7.8, 7.8, MIC[1] - 1.6, MIC[1] + 1.6, Z_CEIL_IN - 1.0, 29.6))              # ridge cavity
    lid = lid.cut(cyl(5.6, Z_CEIL_IN - 0.5, Z_TOP + 1, *SW2))                                      # button plunger hole
    lid = lid.cut(cyl(3.2, Z_CEIL_IN - 0.5, Z_TOP + 1, *LED))                                      # led light pipe hole
    lid = lid.cut(cq.Workplane("XY").workplane(offset=Z_CEIL_IN - 0.5).center(*SW1)
                  .slot2D(11.0, 3.4).extrude(3.0))                                                 # privacy slider slot
    usb = box(-6.5, 6.5, PL / 2 - 1.0, OL / 2 + 1, USB_Z - 3.5, USB_Z + 3.5).edges("|Y").fillet(1.5)
    lid = lid.cut(usb)                                                                             # usb-c opening
    for gx in (-3.0, 0.0, 3.0):
        lid = lid.cut(cyl(1.6, 29.0, 31.5, gx, MIC[1]))                                            # mic grille
    return lid

# ---------------- printable part 3-5: small moving parts ----------------
def make_plunger():                  # bookmark button plunger, drops in from inside
    z_btn_top = Z_PCB_TOP + 3.5
    p = cyl(5.2, z_btn_top + 0.4, Z_CEIL_IN - 1.2)
    p = p.union(cyl(7.4, Z_CEIL_IN - 1.2, Z_CEIL_IN))
    p = p.union(cyl(5.2, Z_CEIL_IN, Z_TOP + 0.6))
    return p.translate((SW2[0], SW2[1], 0))

def make_lightpipe():                # carries the REC led light up to the lid
    z_bot = Z_PCB_TOP + 0.8 + 0.4
    p = cyl(3.0, z_bot, Z_CEIL_IN - 1.2)
    p = p.union(cyl(4.6, Z_CEIL_IN - 1.2, Z_CEIL_IN))
    p = p.union(cyl(3.0, Z_CEIL_IN, Z_TOP))
    return p.translate((LED[0], LED[1], 0))

def make_slider():                   # thumb slider that grabs the switch lever
    z_lever_top = Z_PCB_TOP + 3.6 + 2.4
    z0 = z_lever_top - 1.2
    s = box(-2.0, 2.0, -1.4, 1.4, z0, Z_CEIL_IN - 1.2)
    s = s.cut(box(-1.0, 1.0, -2.0, 2.0, z0 - 0.1, z0 + 4.0))          # fork
    s = s.union(box(-4.0, 4.0, -2.3, 2.3, Z_CEIL_IN - 1.2, Z_CEIL_IN))  # retaining flange
    s = s.union(box(-2.5, 2.5, -1.4, 1.4, Z_CEIL_IN, Z_TOP + 0.8))     # thumb pad
    return s.translate((SW1[0], SW1[1], 0))

# ---------------- reference models of the real components ----------------
def ref_parts():
    r = {}
    r["pcb"] = rrect(W, L, R_PCB, Z_BOARD, T)
    r["header_L"] = box(-7.62 - 1.27, -7.62 + 1.27, XIAO_Y - 8.89, XIAO_Y + 8.89, Z_PCB_TOP, Z_HDR_TOP)
    r["header_R"] = box(7.62 - 1.27, 7.62 + 1.27, XIAO_Y - 8.89, XIAO_Y + 8.89, Z_PCB_TOP, Z_HDR_TOP)
    r["xiao"] = box(-XIAO[0] / 2, XIAO[0] / 2, XIAO_Y - XIAO[1] / 2, XIAO_Y + XIAO[1] / 2,
                    Z_HDR_TOP, Z_HDR_TOP + XIAO_STACK_H)
    r["usbc"] = box(-4.5, 4.5, XIAO_Y + XIAO[1] / 2 - 6.5, XIAO_Y + XIAO[1] / 2 + 0.3,
                    USB_Z - 1.6, USB_Z + 1.6)
    r["battery"] = box(-BAT[0] / 2, BAT[0] / 2, -BAT[1] / 2, BAT[1] / 2, FLOOR + 0.2, FLOOR + 0.2 + BAT[2])
    r["mic_module"] = box(-7.0, 7.0, MIC[1] - 0.8, MIC[1] + 0.8, Z_PCB_TOP + HDR_H - 3.0, Z_PCB_TOP + HDR_H - 3.0 + 14.0)
    r["mic_header"] = box(-7.62, 7.62, MIC[1] - 1.27, MIC[1] + 1.27, Z_PCB_TOP, Z_PCB_TOP + HDR_H)
    r["switch"] = (box(SW1[0] - 3.5, SW1[0] + 3.5, SW1[1] - 1.8, SW1[1] + 1.8, Z_PCB_TOP, Z_PCB_TOP + 3.6)
                   .union(box(SW1[0] - 0.8, SW1[0] + 0.8, SW1[1] - 1.3, SW1[1] + 1.3, Z_PCB_TOP + 3.6, Z_PCB_TOP + 6.0)))
    r["button"] = box(SW2[0] - 3, SW2[0] + 3, SW2[1] - 3, SW2[1] + 3, Z_PCB_TOP, Z_PCB_TOP + 3.5)
    r["led"] = box(LED[0] - 0.8, LED[0] + 0.8, LED[1] - 0.4, LED[1] + 0.4, Z_PCB_TOP, Z_PCB_TOP + 0.8)
    r["jst"] = box(JST[0] - 2.5, JST[0] + 2.5, JST[1] - 3.2, JST[1] + 3.2, Z_PCB_TOP, Z_PCB_TOP + 6.0)
    return r

def vol(shape):
    return shape.val().Volume()

if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(f"{out}/step", exist_ok=True); os.makedirs(f"{out}/stl", exist_ok=True)
    printable = {"case_base": make_base(), "case_lid": make_lid(), "button_plunger": make_plunger(),
                 "led_lightpipe": make_lightpipe(), "slider_cap": make_slider()}
    refs = ref_parts()
    for name, shp in printable.items():
        cq.exporters.export(shp, f"{out}/step/{name}.step")
        cq.exporters.export(shp, f"{out}/stl/{name}.stl", tolerance=0.02, angularTolerance=0.1)
        print(f"{name:16s} volume {vol(shp)/1000:7.2f} cm3")
    asm = cq.Assembly(name="half_life_pendant")
    colors = {"case_base": (0.25, 0.27, 0.3), "case_lid": (0.15, 0.55, 0.5), "button_plunger": (0.9, 0.6, 0.1),
              "led_lightpipe": (0.9, 0.2, 0.2), "slider_cap": (0.9, 0.6, 0.1)}
    for n, s in printable.items():
        asm.add(s, name=n, color=cq.Color(*colors[n]))
    refcol = (0.1, 0.45, 0.2)
    for n, s in refs.items():
        asm.add(s, name="ref_" + n, color=cq.Color(*refcol))
    asm.save(f"{out}/half_life_pendant_assembly.step")
    # interference check: any overlap between two different parts is a design bug
    allp = {**printable, **{"ref_" + k: v for k, v in refs.items()}}
    # these overlaps are intentional: the usb-c sits in the xiao block, the mic module plugs into its header
    ignore = {frozenset(("ref_xiao", "ref_usbc")), frozenset(("ref_mic_module", "ref_mic_header"))}
    bad = 0
    for (a, sa), (b, sb) in itertools.combinations(allp.items(), 2):
        if frozenset((a, b)) in ignore:
            continue
        try:
            v = vol(sa.intersect(sb))
        except Exception:
            v = 0.0
        if v > 0.01:
            bad += 1
            print(f"OVERLAP  {a} x {b}: {v:.3f} mm3")
    print("interference check:", "clean" if bad == 0 else f"{bad} overlaps")
    bb = cq.Workplane().add(printable["case_base"]).union(printable["case_lid"]).val().BoundingBox()
    print(f"assembled size: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
