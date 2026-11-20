"""A wall plate that holds an M5Stack PaperS3 over a USB outlet.

The plate covers a row of gangs, one of them the outlet, and a frame on it
holds the PaperS3, USB edge up, over that outlet. The PaperS3 slides up a
channel in the frame into a USB plug, whose ribbon goes back through a slot to
the outlet, then a cap goes on under it, held by two M3 socket head screws
through its face into heat-set inserts in the shelf behind it. Lips on the
frame's sides and top, and one on the cap, cover the PaperS3's bezel.

The plate prints back down, as it is on the wall; the cap face down.

x is right, y is up, z is out from the wall, the wall at z = 0. Gang 0 is the
leftmost, centered on the origin. The frame, the cap and the PaperS3 are drawn
with the PaperS3 centered on the origin, and put on the plate by `on_frame`.

The view "assembly" is the plate on the wall, the PaperS3 in it.
"""

from math import radians, tan

from build123d import (
    Align,
    Axis,
    Box,
    Circle,
    Cone,
    Cylinder,
    Face,
    Kind,
    Part,
    Pos,
    RectangleRounded,
    Rot,
    Sketch,
    chamfer,
    extrude,
    offset,
)

from build.cad import Object, Piece, project

# Layout

# USB port x from the outlet's center. The frame moves to match.
usb_offset = 0
# Gangs, left to right: P = PaperS3 (first or last), R = rocker, T = toggle,
# B = blank.
gangs = "PR"

# Height of the outlet's face above the wall.
outlet_face_z = 5

# Wall devices

gang_pitch = 46.04
# Plate edge to the center of the outermost gang.
end_margin = 34.93
std_plate_h = 114.3
rocker_opening = (33.6, 67.0)
rocker_screw_spacing = 83.34
toggle_opening = (10.3, 23.8)
toggle_screw_spacing = 60.33
# #6-32 oval head screws, countersunk flush.
screw_d = 3.6
screw_head_d = 7.2
screw_head_angle = 82
# The openings' corners.
opening_r = 1

# Plate

plate_t = 3
# Plate left between the frame and a neighboring opening.
min_web = 3
edge_chamfer = 0.8
# Off the edges on the bed, against elephant's foot, and the mouths of openings
# and holes.
small_chamfer = 0.4

# Frame

wall = 1.6
lip_t = 1.0
# How far the lips cover the PaperS3's bezel.
lip_overlap = 2
# Width of the ledges the PaperS3's back rests on.
pad_w = 2
# Space between the outlet's face and the PaperS3's back: the outlet plug's
# height.
cable_gap = 2
# Material above the plug's pocket.
floor_t = 1.2

# Cap

# Its height below the PaperS3. The frame's top rim matches it.
cap_h = 9
# Screw x from the frame's center.
cap_screw_x = 25
insert_d = 4.0
insert_l = 5.7
m3_clear_d = 3.4
# Counterbore for the screw's head.
m3_head_d = 6.0
m3_head_h = 3.2

# USB plug at the PaperS3

# Width along the PaperS3's edge.
plug_w = 12.8
# How far it sticks out above the PaperS3.
plug_h = 2
plug_clear = 0.2

# Fit

clear_side = 0.2
clear_end = 0.2
clear_depth = 0.3
cap_clear = 0.2
btn_groove = 1.0

# PaperS3, USB edge up, seen from the front

dev_w = 67
dev_h = 121.5
dev_t = 7.7
dev_r = 3
# USB port x from the PaperS3's center.
usb_x = 22
# The power button is on the left edge. Its z range is from the back.
btn_from_top = 21.2
btn_len = 10.8
btn_z = (1.3, 6.1)
btn_proud = 0.7

# With the PaperS3 centered on the origin: the heights of its back, its front,
# the lips' undersides and the frame's front.
z_back = outlet_face_z + cable_gap
z_dev_front = z_back + dev_t
z_chan = z_dev_front + clear_depth
z_top = z_chan + lip_t
chan_x = dev_w / 2 + clear_side
lip_x = dev_w / 2 - lip_overlap
frame_r = dev_r + clear_side + wall
dev_top = dev_h / 2
dev_bot = -dev_h / 2
# The plug's pocket is above the PaperS3, in the frame.
pocket_y1 = dev_top + clear_end + plug_h + plug_clear
frame_y1 = max(pocket_y1 + floor_t, dev_top + cap_h)
frame_y0 = dev_bot - cap_h
frame_h = frame_y1 - frame_y0
frame_cy = (frame_y0 + frame_y1) / 2
cap_cy = dev_bot - cap_h / 2
btn_y = dev_top - btn_from_top

assert gangs.count("P") == 1, "gangs needs exactly one P"
paper = gangs.index("P")
assert paper in (0, len(gangs) - 1), "P must be the first or last gang"

openings = {"R": rocker_opening, "T": toggle_opening}
screw_spacings = {"R": rocker_screw_spacing, "T": toggle_screw_spacing}


def gang_x(i: int) -> float:
    return i * gang_pitch


# The frame's center, on the plate, and its edges about the PaperS3: each
# reaches out to cover the outlet's opening under the PaperS3, should it need
# to.
frame_cx = gang_x(paper) + usb_offset - usb_x
outlet_x = gang_x(paper) - frame_cx
outlet_reach = rocker_opening[0] / 2 + min_web
frame_x0 = min(-chan_x - wall, outlet_x - outlet_reach)
frame_x1 = max(chan_x + wall, outlet_x + outlet_reach)
frame_w = frame_x1 - frame_x0
on_frame = Pos(frame_cx, -frame_cy)

plate_x0 = min(gang_x(0) - end_margin, frame_cx + frame_x0)
plate_x1 = max(gang_x(len(gangs) - 1) + end_margin, frame_cx + frame_x1)
plate_h = max(std_plate_h, frame_h)


def check_neighbor() -> None:
    """Warn if the frame covers the next gang's opening."""
    if len(gangs) == 1:
        return
    side = 1 if paper == 0 else -1
    neighbor = gangs[paper + side]
    if neighbor not in openings:
        return
    edge = frame_cx + (frame_x1 if side > 0 else frame_x0)
    reach = side * (edge - gang_x(paper))
    most = gang_pitch - openings[neighbor][0] / 2 - min_web
    if reach > most:
        print(f"  WARNING: the frame covers the next opening by {reach - most:g} mm")


# Shapes

# Centered on the origin, standing on it.
UPRIGHT = (Align.CENTER, Align.CENTER, Align.MIN)


def up(face: Face | Sketch, z0: float, height: float) -> Part:
    """A face, drawn up from z0."""
    return Pos(0, 0, z0) * extrude(face, height, (0, 0, 1))


def box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]):
    return Pos(x[0], y[0], z[0]) * Box(
        x[1] - x[0], y[1] - y[0], z[1] - z[0], align=Align.MIN
    )


def rod(d: float, z0: float, height: float) -> Part:
    """Upright, d across, from z0."""
    return Pos(0, 0, z0) * Cylinder(d / 2, height, align=UPRIGHT)


def rrect(w: float, h: float, r: float = opening_r) -> Face:
    """A rounded rectangle about the origin."""
    return RectangleRounded(w, h, r)


def slab(w: float, h: float, t: float) -> Part:
    """Rounded corners, about the origin, from z = 0 to t: its front edges
    chamfered, and lightly those on the bed."""
    s = up(rrect(w, h, frame_r), 0, t)
    faces = s.faces().sort_by(Axis.Z)
    s = chamfer(faces.last.edges(), edge_chamfer)
    return chamfer(s.faces().sort_by(Axis.Z).first.edges(), small_chamfer)


def opening(face: Face | Sketch, z0: float, z1: float) -> Part:
    """A hole of that shape from z0 up to z1, its mouth there chamfered."""
    k = small_chamfer
    wide = Sketch() + offset(face, k, kind=Kind.ARC)
    mouth = Pos(0, 0, z1) * extrude(wide, k, (0, 0, -1), taper=45)
    return up(face, z0, z1 - z0) + mouth


def countersink(top: float) -> Part:
    """For an oval head screw, its head flush with `top`."""
    t = tan(radians(screw_head_angle / 2))
    sink = (screw_head_d - screw_d) / 2 / t
    shank = rod(screw_d, -1, top + 2)
    head = Pos(0, 0, top - sink) * Cone(
        screw_d / 2, screw_head_d / 2, sink, align=UPRIGHT
    )
    return shank + head


def screw_holes(kind: str) -> Part:
    return Part() + [
        Pos(0, s * screw_spacings[kind] / 2) * countersink(plate_t) for s in (-1, 1)
    ]


def gang_cuts(kind: str) -> Part:
    w, h = openings[kind]
    return opening(rrect(w, h), -1, plate_t) + screw_holes(kind)


# The plate


def frame_body() -> Part:
    """The frame, uncut, about the PaperS3."""
    return Pos((frame_x0 + frame_x1) / 2, frame_cy) * slab(frame_w, frame_h, z_top)


def cap_zone(dy: float = 0) -> Part:
    """The cap's room: all of the frame below the PaperS3 and in front of the
    shelf at z_back."""
    return box(
        (frame_x0 - 1, frame_x1 + 1), (frame_y0 - 1, dev_bot + dy), (z_back, z_top + 1)
    )


def frame_cuts() -> Part:
    """The frame's insides, about the PaperS3."""
    win_y1 = dev_top - lip_overlap
    win_h = win_y1 - frame_y0 + 2
    cuts = [
        cap_zone(cap_clear),
        # The PaperS3 slides up this channel from the bottom.
        box((-chan_x, chan_x), (frame_y0 - 1, dev_top + clear_end), (z_back, z_chan)),
        # The window between the lips, open at the bottom, where the cap's
        # face is.
        Pos(0, win_y1 - win_h / 2)
        * opening(rrect(2 * lip_x, win_h), z_chan - 1, z_top),
        # Cable space behind the PaperS3, inside the ledges it rests on.
        box(
            (-chan_x + pad_w, chan_x - pad_w),
            (dev_bot + pad_w, dev_top - pad_w),
            (plate_t, z_back),
        ),
        # The plug's pocket, and a slot from it through the top ledge into
        # the cable space.
        box(
            (usb_x - plug_w / 2 - plug_clear, usb_x + plug_w / 2 + plug_clear),
            (dev_top - pad_w, pocket_y1),
            (plate_t, z_chan),
        ),
        # The groove the power button slides up.
        box(
            (-chan_x - btn_groove, -chan_x),
            (frame_y0 - 1, btn_y + btn_len / 2 + 1),
            (z_back + btn_z[0] - 0.5, z_back + btn_z[1] + 0.5),
        ),
    ]
    # Heat-set inserts in the shelf behind the cap.
    insert_hole = opening(Circle(insert_d / 2), z_back - insert_l - 0.5, z_back)
    cuts += [Pos(s * cap_screw_x, cap_cy) * insert_hole for s in (-1, 1)]
    return Part() + cuts


def plate() -> Part:
    body = Pos((plate_x0 + plate_x1) / 2, 0) * slab(
        plate_x1 - plate_x0, plate_h, plate_t
    )
    body += on_frame * frame_body()
    cuts = [Pos(gang_x(i)) * gang_cuts(g) for i, g in enumerate(gangs) if g != "P"]
    # The outlet under the PaperS3 is a rocker-style device, and the frame's
    # walls and ledges stand clear of its face.
    clear = up(rrect(*rocker_opening), -1, outlet_face_z + clear_depth + 1)
    cuts.append(Pos(gang_x(paper)) * (screw_holes("R") + clear))
    cuts.append(on_frame * frame_cuts())
    return body - cuts


# The cap


def cap() -> Part:
    """About the PaperS3, as it's put on: holding up the PaperS3's bottom
    edge, over the ends of the frame's side walls, on the shelf at z_back."""
    cx = lip_x - cap_clear
    body = frame_body() & cap_zone()
    # A lip over the bottom bezel, between the frame's.
    body += box(
        (-cx, cx),
        (dev_bot - 1, dev_bot + lip_overlap),
        (z_dev_front + cap_clear, z_top),
    )
    for s in (-1, 1):
        at = Pos(s * cap_screw_x, cap_cy)
        body -= at * rod(m3_clear_d, z_back - 1, z_top - z_back + 2)
        body -= at * rod(m3_head_d, z_top - m3_head_h, m3_head_h + 1)
    return body


# For reference


def cap_screws() -> Part:
    """M3 x 10 socket head screws."""
    one = rod(3, -10, 10) + rod(5.5, 0, 3)
    return Part() + [
        Pos(s * cap_screw_x, cap_cy, z_top - m3_head_h) * one for s in (-1, 1)
    ]


def papers3() -> Part:
    body = up(rrect(dev_w, dev_h, dev_r), z_back, dev_t)
    button = box(
        (-dev_w / 2 - btn_proud, -dev_w / 2 + 1),
        (btn_y - btn_len / 2, btn_y + btn_len / 2),
        (z_back + btn_z[0], z_back + btn_z[1]),
    )
    return body + button


def plug() -> Part:
    """The plug end of the ribbon, in the middle of the PaperS3's thickness."""
    z = z_back + dev_t / 2
    return box(
        (usb_x - plug_w / 2, usb_x + plug_w / 2),
        (dev_top, dev_top + plug_h),
        (z - 3.5, z + 3.5),
    )


def outlet_face() -> Part:
    w, h = rocker_opening
    return Pos(gang_x(paper)) * up(rrect(w - 0.6, h - 0.6), 0, outlet_face_z)


# Put together


def assembly() -> list[Piece]:
    return [
        Piece(plate(), "plate", "white"),
        Piece(on_frame * cap(), "cap", "lightgray"),
        Piece(on_frame * papers3(), "PaperS3", "dimgray"),
        Piece(on_frame * plug(), "plug", "orange"),
        Piece(on_frame * cap_screws(), "screws", "silver"),
        Piece(outlet_face(), "outlet", "ivory"),
    ]


def plate_print() -> Part:
    """Back down, as it is on the wall."""
    check_neighbor()
    print(
        f"  Plate is {plate_x1 - plate_x0:g} x {plate_h:g} mm, "
        f"the frame {z_top:g} mm out from the wall"
    )
    return plate()


def cap_print() -> Part:
    """Face down."""
    face_down = Pos(0, 0, z_top) * Rot(180, 0, 0)
    return face_down * Pos(-(frame_x0 + frame_x1) / 2, -cap_cy) * cap()


project(
    __file__,
    objects={
        "plate": Object(plate_print, "The wall plate and the frame the PaperS3 is in"),
        "cap": Object(cap_print, "Goes on under the PaperS3, held by two M3 screws"),
    },
    views={"assembly": Object(assembly, "On the wall, holding the PaperS3")},
    plates=["plate cap"],
)
