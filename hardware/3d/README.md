# 3D enclosure

Parametric CadQuery model of the pendant case, with real STEP files and print-ready STLs.

```
pip install cadquery trimesh pyvista
python pendant_case.py          # rebuilds step/, stl/, the assembly STEP and runs the interference check
python render_views.py          # rebuilds the renders in docs/images (needs xvfb on a headless machine)
```

## parts

| part | print notes |
|---|---|
| `case_base` | print upright. The lanyard ear is at the bottom end |
| `case_lid` | print upside down (ceiling on the bed). The USB-C opening bridges, so use a few layers of bridging or a little support |
| `button_plunger` | print upright. Drops in from inside, the flange keeps it from falling out |
| `slider_cap` | print upright. The fork at the bottom grabs the switch lever |
| `led_lightpipe` | print in clear/translucent filament, or cut a 3 mm clear rod to length |

Material: PETG or PLA, 0.2 mm layers, 3 walls. Lid and base join with a tongue-and-groove lip (0.1 mm clearance per side),
friction fit. A dab of glue or a bit of tape makes it permanent.

## interference check

`pendant_case.py` builds the carrier PCB, headers, XIAO stack, battery, mic module, switch, button, LED and battery connector
as reference solids and checks every pair for overlap. Result: no printed part collides with any component
(the two intentional overlaps, USB-C inside the XIAO and the mic module plugged into its header, are excluded).

## assumptions to verify against your real parts

Sizes marked ASSUMED in `pendant_case.py`: battery 25 x 40 x 5 mm, 8.5 mm female headers, XIAO + Sense stack height 6.2 mm,
switch lever geometry. Measure yours and change the numbers at the top of the script, everything else follows.

## things I learned from modelling it

- the INMP441 breakout stands upright on its header and is about 14 mm tall, which is why the lid has a raised ridge over the mic
- the whole stack makes the case chunky (33.4 x 64.9 x 30.8 mm including the ear). Low-profile sockets, or soldering the XIAO straight to the board, would cut roughly 8 mm
