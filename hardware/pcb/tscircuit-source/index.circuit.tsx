import React from "react"

// HALF LIFE PENDANT: carrier board v0.1
// XIAO ESP32-S3 Sense plugs into two 1x7 female headers (15.24mm row spacing, VERIFY vs your XIAO).
// Carrier adds: hardware privacy switch, INMP441 mic socket, REC LED, bookmark button,
// LiPo connector, battery-level divider, mic-rail sense with pulldown.

export default () => (
  <board width="28mm" height="50mm" layers={2} borderRadius="3mm" thickness="1.6mm" minViaHoleDiameter="0.3mm" minViaPadDiameter="0.6mm" minTraceWidth="0.2mm" nominalTraceWidth="0.2mm">
    <schematicsection name="MCU" displayName="XIAO ESP32-S3 Sense sockets" />
    <schematicsection name="Mic" displayName="Mic + hardware privacy switch" />
    <schematicsection name="IO" displayName="REC LED + bookmark button" />
    <schematicsection name="Pwr" displayName="Battery + level sense" />

    {/* ---------- XIAO sockets ---------- */}
    <pinheader
      name="HL" pinCount={7} pitch="2.54mm" gender="female"
      pinLabels={["D0", "D1", "D2", "D3", "D4", "D5", "D6"]}
      pcbX={-7.62} pcbY={14} pcbRotation={-90} schX={0} schY={0} schWidth={0.39} schSectionName="MCU"
    />
    <pinheader
      name="HR" pinCount={7} pitch="2.54mm" gender="female"
      pinLabels={["V5", "GND", "V3V3", "D10", "D9", "D8", "D7"]}
      pcbX={7.62} pcbY={14} pcbRotation={-90} schX={6} schY={0} schWidth={0.58} schSectionName="MCU"
    />

    {/* ---------- Mic + privacy switch ---------- */}
    <switch name="SW1" type="spst" footprint="pinrow2_p2.54mm" pcbX={-8} pcbY={-6}
      schX={16} schY={4} schRotation={-90} schSectionName="Mic" />
    <pinheader
      name="MIC1" pinCount={6} pitch="2.54mm" gender="female"
      pinLabels={["SCK", "WS", "SD", "L_R", "GND", "VDD"]}
      pcbX={0} pcbY={-1} pcbRotation={0} schX={22} schY={0} schWidth={0.485} schSectionName="Mic"
    />
    <capacitor name="C1" capacitance="100nF" footprint="0603" pcbX={9} pcbY={-6}
      schX={26} schY={-4} schRotation={-90} schSectionName="Mic" />
    <capacitor name="C2" capacitance="10uF" footprint="0805" pcbX={9} pcbY={-9}
      schX={27.2} schY={-4} schRotation={-90} schSectionName="Mic" />
    <resistor name="R2" resistance="100k" footprint="0603" pcbX={4} pcbY={-6}
      schX={30} schY={-4} schRotation={-90} schSectionName="Mic" />

    <trace from="SW1.pin1" to="HR.V3V3" />
    <trace from="SW1.pin2" to="net.MIC_VDD" />
    <trace from="MIC1.VDD" to="net.MIC_VDD" />
    <trace from="C1.pin1" to="net.MIC_VDD" />
    <trace from="C2.pin1" to="net.MIC_VDD" />
    <trace from="R2.pin1" to="net.MIC_VDD" />
    <trace from="C1.pin2" to="net.GND" />
    <trace from="C2.pin2" to="net.GND" />
    <trace from="R2.pin2" to="net.GND" />
    <trace from="MIC1.GND" to="net.GND" />
    <trace from="MIC1.L_R" to="net.GND" />
    <trace from="MIC1.SCK" to="HL.D0" />
    <trace from="MIC1.WS" to="HL.D1" />
    <trace from="MIC1.SD" to="HL.D2" />
    <trace from="HL.D5" to="net.MIC_VDD" />
    <trace from="HR.GND" to="net.GND" />

    {/* ---------- IO ---------- */}
    <resistor name="R1" resistance="220" footprint="0603" pcbX={-9} pcbY={-14} pcbRotation={180}
      schX={-12} schY={-6} schRotation={-90} schSectionName="IO" />
    <led name="LED1" color="red" footprint="0603" pcbX={-9} pcbY={-17}
      schX={-12} schY={-9} schRotation={-90} schSectionName="IO" />
    <pushbutton name="SW2" footprint="smdpushbutton" pcbX={0} pcbY={-14}
      schX={-6} schY={-6} schSectionName="IO" />
    <trace from="HL.D6" to="R1.pin1" />
    <trace from="R1.pin2" to="LED1.pos" />
    <trace from="LED1.neg" to="net.GND" />
    <trace from="HL.D4" to="SW2.pin1" />
    <trace from="SW2.pin2" to="net.GND" />

    {/* ---------- Battery + level sense ---------- */}
    <battery name="BAT1" capacity="500mAh" footprint="jst2_p2mm_ph"
      pcbX={9} pcbY={-19} pcbRotation={-90} schX={-12} schY={4} schOrientation="vertical" schSectionName="Pwr" />
    <resistor name="R3" resistance="200k" footprint="0603" pcbX={3} pcbY={-18} pcbRotation={180}
      schX={-6} schY={6} schRotation={-90} schSectionName="Pwr" />
    <resistor name="R4" resistance="200k" footprint="0603" pcbX={3} pcbY={-21}
      schX={-6} schY={2} schRotation={-90} schSectionName="Pwr" />
    <trace from="BAT1.pos" to="net.VBAT" />
    <trace from="BAT1.neg" to="net.GND" />
    <trace from="R3.pin1" to="net.VBAT" />
    <trace from="R3.pin2" to="net.VBAT_SENSE" />
    <trace from="R4.pin1" to="net.VBAT_SENSE" />
    <trace from="R4.pin2" to="net.GND" />
    <trace from="HL.D3" to="net.VBAT_SENSE" />

    <silkscreentext text="HALF LIFE PENDANT v0.1" fontSize="1.2mm" pcbX={0} pcbY={-23} />
  </board>
)
