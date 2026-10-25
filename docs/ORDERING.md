# Ordering the carrier PCB

Files: `hardware/pcb/gerbers/half-life-pendant-gerbers.zip` (upload this). Editable design: `hardware/pcb/half-life-pendant.kicad_pro`.

## order settings (JLCPCB, PCBWay or similar)
- upload the Gerber zip
- 28 x 50 mm, 2 layers, 1.6 mm, qty 5, HASL lead-free (or ENIG)
- no assembly: the board is mostly through-hole sockets, so hand-solder it (passives are 0603 or bigger on purpose)
- design rules used: traces 0.2 mm, vias 0.3 mm hole / 0.6 mm pad

## check before you pay
1. **XIAO fit.** The sockets assume 15.24 mm between the two pin rows. Measure your XIAO ESP32-S3 Sense.
2. **Footprints.** The slide switch, tactile button and JST connector footprints are generic. Compare them with your real parts.
3. **Battery pads.** The XIAO battery pads are on its underside and the board's JST connector does not touch them. A short wire links them.
4. **LiPo polarity.** Many LiPo cables are wired opposite to the JST PH pinout. Check before connecting.
5. **Preview.** Open the Gerbers in the fab's online viewer and check every layer.
6. **Open it in KiCad** and run its DRC. I generated the KiCad files from the tscircuit design but haven't opened them in KiCad myself.

## 3D printing
See `hardware/3d/README.md` for orientation and settings. Check the parts against your real battery and switch first.
