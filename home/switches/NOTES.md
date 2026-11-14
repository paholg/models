# Physical sliders for Home Assistant

Notes from a feasibility discussion on 2026-11-13. Nothing has been built or
measured yet: every force, field and coil figure below is an estimate.

## Idea

The magnet-detent sliders in `game/fox-in-the-forest/score.scad` feel great.
Use the same mechanism as wall-switch-sized sliders for Home Assistant, read by
an ESP32 (ESPHome). Ideally the slider also moves itself to follow state
changed elsewhere.

The score tracker's mechanism: a 5×1 mm disc magnet in the slider's plate, over
one captured in the back at each position, 9 mm pitch, about 0.6 mm between
magnets.

## Status

- Everything on the "to buy" part of the bench test list below was ordered
  2026-11-13: solenoids, DRV8833 boards, 5 V supply, capacitor, Hall sensors
  and the larger magnets.
- Next step when they arrive: measure one coil's resistance (expect about
  5.5 Ω for the 6 V version), then design the test rig below.

## Sensing position

Feasible, low risk. Must be non-contact: a slide pot's friction would stop the
magnet snapping into its detent.

- A Hall sensor directly under a detent magnet doesn't work: about 165 mT all
  the time, about 230 mT with the slider there, which saturates common parts.
- Preferred: a second "sense" magnet in the slider, about 7 mm to the side of
  the detent magnet, over a row of Hall switches, one per position. Roughly
  +80 mT from the sense magnet against −5 mT static from the detent row, so
  digital switches need no calibration. One GPIO per position, or an MCP23017.
- Alternative: one 3-axis magnetometer per track (MLX90393 class). Continuous
  position and no extra magnet, but needs calibration and sees neighbouring
  sliders.

## Moving the slider

The detent takes an estimated 0.5–1 N sideways to break. Measure it with a
luggage scale; everything is sized against this number.

| Option | Assessment |
|---|---|
| Motor-driven pusher | Known to work. Gearmotor and belt (N20, about 200 rpm, GT2 16-tooth pulley) move a fork whose gap spans the whole travel, so it parks clear and the manual feel is unchanged. Brief whir. Not an N20 with an M4 leadscrew: far too slow. A micro servo (MG90S) with a printed arm is the quickest first test. |
| Electromagnets | The interesting one, being tested first. See below. |
| Motorized fader | Works, but its drag and weak motor fight magnetic detents. |
| LED per position | Fallback with no motion: LED shows real state, slider only commands. |

### Electromagnet version

An iron-core coil under each position. Unpowered, the slider magnet clicks
onto each core, so the cores are the detents and the back needs no magnets.
Powered, one core repels while its neighbour attracts.

Open risks, which the bench test is meant to answer:

- Repelling a magnet sitting dead centre over a core doesn't pick a direction;
  the neighbour's pull has to steer, and it is weak at this spacing.
- Magnet-on-iron is a softer click than magnet-on-magnet.
- Each coil needs driving in both directions. Wiring every third coil together
  as three phases would cut this to three H-bridge channels per slider, if it
  still moves cleanly.

Strength, for scale: a 5×1 mm magnet is equivalent to roughly 950 amp-turns.

## JF-0530B solenoid

No manufacturer datasheet exists; these are from seller listings, which
disagree with each other. A generic part from many factories, so measure what
arrives.

- 6 V version: about 5.5 Ω, about 1.1 A. 12 V version: about 12 Ω, about 1 A.
  Many listings say "300 mA", which reads as a long-term limit, not the draw.
- Plunger 6 mm diameter. Clamp it in place and it is the fixed core.
- Body about 30 × 13–16 × 15 mm, so minimum pitch about 13–16 mm.
- On for a few seconds at most.
- Estimated 600–800 amp-turns at rated voltage (from resistance and a guessed
  winding space).
- About $4–6 each at retail, so too dear for dozens.

## Bench test parts

- 3 solenoids in use (6 V version), plus spares
- 2× DRV8833 breakout: three H-bridge channels needed
- 5 V supply, 3 A or more. A USB charger is fine through a USB-C breakout with
  5.1 kΩ CC resistors, wired straight to the drivers, not through the ESP32
  board. Not a power bank. Share ground with the ESP32.
- 1000 µF, 16 V or higher capacitor across the supply at the drivers
- 5× SS49E analog Hall sensors, to measure coil field and slider position
- ESP32 dev board, breadboard, jumpers, multimeter, luggage scale
- 5×1 mm magnets, and optionally 6×2 or 8×2 mm to suit the 6 mm cores

To print: a holder for three solenoids in a row at about 16 mm pitch with the
plunger ends up, a short track over them with a thin floor, a slider carrying
the magnet, and a pocket for a Hall sensor beside the track.

Firmware: pulse the coils in sequence and see whether the slider steps.

## If it works: winding coils

About $0.50–1 per coil in materials against $4–6 bought.

- 0.25 mm (30 AWG) enamelled wire, 15–25 m per coil. About 500 turns on an M5
  bolt with a 15 mm long, 12 mm wide bobbin comes to about 5 Ω: 1 A and 500
  amp-turns at 5 V, pulses only. A one-pound spool makes 40–65 coils.
- Buy solderable (polyurethane) enamel, and put two header pins in the bobbin
  for the wire ends. Finishing leads takes longer than winding.
- Winder: a NEMA17 spinning a printed mandrel, counting turns by steps, wire
  guided by hand through a felt tensioner. A minute or two per coil.
- Drivers cost about as much as the coils: about $0.75 per H-bridge channel.
