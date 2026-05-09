#!/usr/bin/env python3
"""
generate_meshes.py
==================
Programmatic STL mesh generator for the RLAI AMR robot body.

All geometry is modelled in millimetres (mm).  The URDF applies
  scale="0.001 0.001 0.001"
when loading these meshes, so Gazebo / RViz sees everything in SI (metres).

Robot reference geometry  (from urdf/base/):
  ┌────────────────────────────────────────────────────────────────────────┐
  │  Part              │  Dimension (mm)            │  URDF ref            │
  ├────────────────────────────────────────────────────────────────────────┤
  │  Chassis bbox      │  500 L × 400 W × 150 H     │  base.urdf.xacro     │
  │  Wheel             │  r = 62.5,  width = 25      │  wheels.urdf.xacro   │
  │  Wheel sep (Y)     │  350 centre-to-centre       │  robot.urdf.xacro    │
  │  Caster sphere     │  r = 25                     │  wheels.urdf.xacro   │
  │  LiDAR 2D position │  (180, 0, 180)              │  robot.urdf.xacro    │
  │  Camera position   │  (250, 0, 130)              │  robot.urdf.xacro    │
  └────────────────────────────────────────────────────────────────────────┘

Outputs  (src/robot/rlai_meshes/meshes/):
  chassis.stl    —  full chassis body with integrated sensor mounts
  wheel.stl      —  single wheel body (tyre, hub, spokes)
  wheel_cap.stl  —  cap discs only (separate mesh for per-colour URDF visual)

Usage:
  python scripts/generate_meshes.py
"""

import math
import os
import logging
from pathlib import Path

import cadquery as cq
from cadquery import exporters

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent          # .../scripts/
REPO_ROOT  = SCRIPT_DIR.parent                        # workspace root
MESH_DIR   = REPO_ROOT / "src/robot/rlai_meshes/meshes"

# ── Export quality ─────────────────────────────────────────────────────────────
LINEAR_TOL  = 5e-5   # 0.05 mm  → fine surface quality
ANGULAR_TOL = 0.05   # rad      → ~3° max deviation on arcs / cylinders

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CHASSIS PARAMETERS  (all mm – scaled × 0.001 in URDF → metres in Gazebo)  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

CX_L = 500.0   # chassis length  (X, +forward)
CX_W = 400.0   # chassis width   (Y, ±lateral)
CX_H = 150.0   # chassis height  (Z, +up)

# ── Two-tier body: structural tray + flat top deck ────────────────────────────
LOWER_H      = 100.0   # structural tray height  (z: 0  → 100)
UPPER_H      =  50.0   # top deck height         (z: 100→ 150)
LOWER_FILLET =  20.0   # vertical-edge fillet on lower tray
UPPER_FILLET =  12.0   # vertical-edge fillet on upper deck
DECK_INSET   =  10.0   # deck set in from tray edges (each side → 480 × 380)

# ── LiDAR mounting ring (annular cylinder, sits on deck top) ────────────────
# URDF places LiDAR at (0.20, 0, 0.18) m  →  (200, 0, 180) mm.
# Ring sits directly on deck (z=150 mm), ring top at z=170 mm.
LIDAR_X       = 200.0
LIDAR_RING_Z  = CX_H         # 150 mm (deck top, no tower)
LIDAR_RING_H  =  20.0        # ring top at 170 mm
LIDAR_RING_OR =  52.0        # outer radius
LIDAR_RING_IR =  39.0        # inner radius (LiDAR body Ø ≈ 76 mm fits inside)

# ── Camera housing (flush-mounted in front face, replaces external L-bracket) ────
#
# Design:  A housing block fills the area at the front of the upper deck
#   (x=224..250 mm, z=100..150 mm, y=±55 mm).  The upper deck front face is at
#   x=240 mm (inset 10 mm), so the block provides a clean 10 mm extension plus
#   back wall.  A camera-pocket bay is then cut from the front face, leaving the
#   D435i body sitting flush with the chassis front face.
#
# Camera joint (robot.urdf.xacro):  xyz="0.237 0.0 0.125"
#   → camera body center 12.5 mm behind front face  (front face flush at x=250 mm)
#
CAM_HOUSING_W    = 110.0   # housing Y width (±55 mm, centered)
CAM_HOUSING_D    =  26.0   # housing X depth (x=224..250 mm)
CAM_HOUSING_FILLET = 4.0   # vertical-edge fillet radius
CAM_MOUNT_Z      = 125.0   # camera joint Z in mm  (midpoint of housing z=100..150)

# Camera bay (pocket cut into front face):
CAM_BAY_W  =  92.0   # Y width  (2 mm margin around 90 mm camera body)
CAM_BAY_H  =  27.0   # Z height (2 mm margin around 25 mm camera body)
CAM_BAY_D  =  27.0   # X depth  (1 mm clearance at pocket back)

# ── D435i camera mesh parameters (local link frame, all mm, box centred at origin) ─
#
# Camera body:  90 mm × 25 mm × 25 mm  (Y-width × X-depth × Z-height)
#   Front face at local x = +12.5 mm
#   Lens positions on front face (D435i approximate, left→right in +Y direction):
CAM_W = 90.0    # Y
CAM_D = 25.0    # X  (depth / thickness)
CAM_H = 25.0    # Z  (height)
CAM_BODY_FILLET = 1.5

# Lens discs on front face (x = +CAM_D/2), extruding +X outward
# Order: IR emitter | left IR | RGB | right IR
CAM_LENS_SPECS = [
    ( 40.0,  0.0, 3.5),    # IR emitter:  y=+40 mm, z=0, r=3.5
    ( 18.0,  0.0, 5.0),    # left IR:     y=+18 mm, z=0, r=5.0
    ( -3.0,  0.0, 7.0),    # RGB:         y= −3 mm, z=0, r=7.0  ← largest
    (-22.0,  0.0, 5.0),    # right IR:    y=−22 mm, z=0, r=5.0
]
CAM_LENS_T = 2.0   # lens disc protrusion depth (mm)

# Sensor window recess on front face (shows the imaging area)
CAM_WIN_W  = 78.0   # Y
CAM_WIN_H  = 16.0   # Z
CAM_WIN_D  =  1.2   # recess depth into front face (mm)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  WHEEL PARAMETERS  (all mm – scaled × 0.001 in URDF)                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

WH_R       = 62.5   # tyre outer radius
WH_W       = 40.0   # axial width  (= length in STL, Z-axis; URDF rotates π/2)
TYRE_THICK = 12.0   # radial tyre-wall thickness  → inner radius = 50.5 mm
HUB_R      = 18.0   # hub disc radius
SPOKE_N    =  5     # number of spokes
SPOKE_W    =  5.0   # spoke tangential width (Y in STL)
SPOKE_T    = 28.0   # spoke axial thickness  (Z in STL, slightly thinner than tyre)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  WHEEL CAP PARAMETERS  (disc covers flush with both wheel faces)             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

WH_CAP_T = 2.5                 # cap disc thickness (mm)
WH_CAP_R = WH_R - TYRE_THICK  # 50.5 mm – fits exactly inside tyre bore

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  3-D LIDAR MAST PARAMETERS  (supports lidar_3d at xyz="0 0 0.30" m)        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

LIDAR3D_Z       = 300.0   # LiDAR joint Z in base_link frame (mm)
LIDAR3D_L       =  86.0   # LiDAR cylinder length (lidar_3d.urdf.xacro)
LIDAR3D_BOT     = LIDAR3D_Z - LIDAR3D_L / 2.0   # = 257 mm  (cylinder bottom)

MAST_BASE_Z     = CX_H + 10.0      # = 160 mm  (former sensor tower top)
MAST_FLANGE_W   =  50.0   # base-flange plate width & depth (mm)
MAST_FLANGE_H   =   5.0   # base-flange plate height (mm)
MAST_POLE_R     =  13.0   # round pole outer radius (mm)
MAST_COLLAR_H   =  12.0   # top collar height  (mm)
MAST_COLLAR_R   =  26.0   # top collar radius  (grips LiDAR cylinder base)
MAST_COLLAR_Z   = LIDAR3D_BOT - MAST_COLLAR_H   # = 245 mm

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PAYLOAD PLATFORM PARAMETERS  (all mm – scaled × 0.001 in URDF)            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# Layout (base_link frame, Z-up):
#
#   z = 150 mm  — chassis deck top (post feet sit here)
#   z = 156 mm  — post shaft starts (above 6 mm foot flange)
#   z = 220 mm  — platform plate bottom face
#   z = 240 mm  — platform plate top face
#
# 2-D LiDAR scans at z ≈ 180 mm — fully in the 70 mm open gap between
# the chassis deck and the platform underside.  LiDAR housing top ≈ 200 mm,
# leaving 20 mm clearance below the platform.
# Each corner post (Ø 24 mm) is at (±205, ±150) mm; at r ≈ 253 mm from the
# LiDAR at (180,0), each post subtends < 3° of the 360° horizontal scan.

PP_POST_R      = 12.0    # post shaft radius (mm) — Ø 24 mm round tube
PP_POST_FOOT_W = 36.0    # square foot-flange side length (mm)
PP_POST_FOOT_H =  6.0    # foot-flange height (mm)
PP_POST_BOT_Z  = 150.0   # foot base = chassis deck top
PP_PLATE_Z     = 220.0   # platform plate bottom face  ← lowered from 265
PP_POST_H      = PP_PLATE_Z - PP_POST_BOT_Z - PP_POST_FOOT_H + 3.0  # +3 overlap into plate for clean union

# Corner post XY positions (base_link frame, mm)
# Front posts pulled back to x=110 so plate front edge (140 mm) clears
# the LiDAR ring rear edge (200-52=148 mm) by 8 mm.
#   front foot outer edge X: 110+18=128 < 140 ✓   Y: 130+18=148 < 160 ✓
#   rear  foot outer edge X: 190+18=208 < 220 ✓   Y: 130+18=148 < 160 ✓
PP_POSTS = [(110, 130), (110, -130), (-190, 130), (-190, -130)]

# Top plate — asymmetric: rear stays at x=−220 mm, front pulled to x=+140 mm.
PP_PLATE_FRONT  = 140.0   # plate front edge X (mm) — clears LiDAR ring rear (148 mm)
PP_PLATE_REAR   = 220.0   # plate rear  edge X (mm) — unchanged
PP_PLATE_L      = PP_PLATE_FRONT + PP_PLATE_REAR   # 360 mm
PP_PLATE_CX     = (PP_PLATE_FRONT - PP_PLATE_REAR) / 2.0  # −40 mm (plate X centre)
PP_PLATE_W      = 320.0   # Y extent (mm)
PP_PLATE_H      =  20.0   # thickness (mm)
PP_PLATE_FILLET =  10.0   # vertical-edge fillet (mm)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  LOGO ENGRAVING PARAMETERS                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# The rbot.svg logo is engraved 2 mm deep into both ±Y side walls of the
# lower structural tray (z = 0..100 mm, wall at y = ±200 mm).
#
# SVG bounding box of text content (measured by sampling all paths):
#   x ∈ [25.6, 476.2]  width  = 450.6 SVG units
#   y ∈ [209.1, 282.8] height =  73.7 SVG units  (Y-down, includes descenders)

LOGO_SVG       = str(SCRIPT_DIR / "rbot.svg")
LOGO_TARGET_W  = 380.0   # mm — desired text width on wall
LOGO_DEPTH     =   2.0   # mm — engraving depth into wall
LOGO_WALL_CZ   =  45.0   # mm — robot Z of logo centre (lower tray z=0..100)
LOGO_SVG_XC    = (25.6 + 476.2) / 2.0   # SVG x centre ≈ 250.9
LOGO_SVG_YC    = (209.1 + 282.8) / 2.0  # SVG y centre ≈ 245.95
LOGO_SCALE     = LOGO_TARGET_W / (476.2 - 25.6)  # ≈ 0.843 mm per SVG unit

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CASTER ATTACHMENT PODS  (4 corners, z=−37.5 mm)                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

CASTER_X       = 200.0   # |X| of front / rear caster (matches URDF joints)
CASTER_Y       = 140.0   # |Y| of left / right caster (matches URDF joints)
CASTER_Z       = -37.5   # caster sphere centre Z  (below chassis bottom)
CASTER_PLATE_W =  70.0   # mount-plate footprint (mm)
CASTER_PLATE_H =   8.0   # mount-plate height   (mm)
CASTER_STEM_R  =  20.0   # stem cylinder outer radius (mm)


# ══════════════════════════════════════════════════════════════════════════════
#  CHASSIS BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_chassis() -> cq.Workplane:
    """
    Construct the full AMR chassis body.

    Z-layer breakdown (mm):
        0 – 100   Lower structural tray     500 × 400,  vertical edge fillets r=20
      100 – 150   Upper flat deck           480 × 380,  vertical edge fillets r=12
      150 – 160   Sensor tower              200 × 360,  front-biased  (x = −10…190)
      160 – 180   2-D LiDAR mount ring      OD=104, ID=78 annular cylinder @ x=180
      100 – 150   Camera housing (front)    26 × 110 × 50 mm flush block + 92×27 bay

    Additional structural features:
      160 – 257   3-D LiDAR mast            base flange + round pole + top collar
        0 – −38   Caster attachment pods    square plate + cylindrical stem (×2)
    """

    # ── 1. Lower structural tray ──────────────────────────────────────────────
    lower = (
        cq.Workplane("XY")
        .box(CX_L, CX_W, LOWER_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(LOWER_FILLET)
    )

    # ── 2. Upper deck (inset 10 mm each side, stacked on lower tray) ─────────
    deck = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0.0, 0.0, LOWER_H))
        .box(
            CX_L - DECK_INSET * 2,
            CX_W - DECK_INSET * 2,
            UPPER_H,
            centered=(True, True, False),
        )
        .edges("|Z")
        .fillet(UPPER_FILLET)
    )
    body = lower.union(deck)

    # ── 3. LiDAR mounting ring (annular cylinder, on deck top) ───────────────
    lidar_ring = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(LIDAR_X, 0.0, LIDAR_RING_Z))
        .circle(LIDAR_RING_OR)
        .circle(LIDAR_RING_IR)
        .extrude(LIDAR_RING_H)
    )
    body = body.union(lidar_ring)

    # ── 4. Camera housing block (front of upper deck) + bay pocket ────────────
    # A solid housing block extends the upper-deck front face (which is inset
    # 10 mm to x=240 mm) forward to x=250 mm over a 110 mm wide × 50 mm tall
    # region.  A camera-pocket bay is then cut into its front face so the D435i
    # body sits flush: front face of camera == chassis front face (x=250 mm).
    housing_x_cen = CX_L / 2.0 - CAM_HOUSING_D / 2.0   # 237 mm
    cam_housing = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(housing_x_cen, 0.0, LOWER_H))
        .box(CAM_HOUSING_D, CAM_HOUSING_W, UPPER_H,
             centered=(True, True, False))
        .edges("|Z")
        .fillet(CAM_HOUSING_FILLET)
    )
    body = body.union(cam_housing)

    # Pocket bay: cut camera-shaped recess from the front face
    bay = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(housing_x_cen, 0.0, CAM_MOUNT_Z))
        .box(CAM_BAY_D, CAM_BAY_W, CAM_BAY_H, centered=(True, True, True))
    )
    body = body.cut(bay)

    # ── 6. 3-D LiDAR mast (commented out — 3D lidar removed, payload platform occupies space)
    # lidar_mast_flange = (
    #     cq.Workplane("XY")
    #     .transformed(offset=cq.Vector(0.0, 0.0, MAST_BASE_Z))
    #     .box(MAST_FLANGE_W, MAST_FLANGE_W, MAST_FLANGE_H,
    #          centered=(True, True, False))
    # )
    # mast_pole_bot = MAST_BASE_Z + MAST_FLANGE_H
    # mast_pole_h   = MAST_COLLAR_Z - mast_pole_bot
    # lidar_mast_pole = (
    #     cq.Workplane("XY")
    #     .transformed(offset=cq.Vector(0.0, 0.0, mast_pole_bot))
    #     .circle(MAST_POLE_R)
    #     .extrude(mast_pole_h)
    # )
    # lidar_mast_collar = (
    #     cq.Workplane("XY")
    #     .transformed(offset=cq.Vector(0.0, 0.0, MAST_COLLAR_Z))
    #     .circle(MAST_COLLAR_R)
    #     .extrude(MAST_COLLAR_H)
    # )
    # body = body.union(lidar_mast_flange).union(lidar_mast_pole).union(lidar_mast_collar)

    # ── 7. Caster attachment pods (4 corners) ─────────────────────────────────
    # Each pod: a square mount plate flush with the chassis underside (z=0→−8)
    # plus a cylindrical stem that reaches the caster sphere centre (z=−8→−37.5).
    stem_h = abs(CASTER_Z) - CASTER_PLATE_H   # 37.5 − 8 = 29.5 mm
    for cx, cy in [(CASTER_X, CASTER_Y), (CASTER_X, -CASTER_Y),
                   (-CASTER_X, CASTER_Y), (-CASTER_X, -CASTER_Y)]:
        caster_plate = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(cx, cy, -CASTER_PLATE_H))
            .box(CASTER_PLATE_W, CASTER_PLATE_W, CASTER_PLATE_H,
                 centered=(True, True, False))
            .edges("|Z").fillet(8.0)
        )
        caster_stem = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(cx, cy, CASTER_Z))
            .circle(CASTER_STEM_R)
            .extrude(stem_h)
        )
        body = body.union(caster_plate).union(caster_stem)

    # ── 8. Logo engraving on ±Y side walls ───────────────────────────────────
    body = _engrave_logo_walls(body)

    return body


# ══════════════════════════════════════════════════════════════════════════════
#  LOGO ENGRAVING
# ══════════════════════════════════════════════════════════════════════════════

def _engrave_logo_walls(body: cq.Workplane) -> cq.Workplane:
    """
    Engrave the rbot.svg logo 2 mm deep into both ±Y side walls of the
    chassis lower tray.

    Approach:
      1. Parse SVG paths with svgelements (handles group transforms).
      2. Split each path into closed sub-paths (M...Z units).
      3. Sample each sub-path into a dense polyline.
      4. Transform SVG coords → workplane UV → 3D world points on the wall face.
      5. Build Wire → Solid (extrudeLinear inward) → cut from chassis body.

    Wall plane definitions:
      +Y wall: Plane(origin=(0,+200,0), xDir=(-1,0,0), normal=(0,+1,0))
               →  yDir=(0,0,+1), toWorldCoords(u,v) = (-u, +200, v)
               →  text reads L-to-R when viewed from outside (+Y side)
      -Y wall: Plane(origin=(0,-200,0), xDir=(+1,0,0), normal=(0,-1,0))
               →  yDir=(0,0,+1), toWorldCoords(u,v) = (+u, -200, v)
               →  text reads L-to-R when viewed from outside (-Y side)
    Both walls use identical UV coordinates (u = (svg_x-cx)*scale, v = -(svg_y-cy)*scale+cz).
    """
    import svgelements as se
    from svgelements import Move, Close, Line, CubicBezier, QuadraticBezier

    if not os.path.isfile(LOGO_SVG):
        log.warning("Logo SVG not found (%s) — skipping wall engraving", LOGO_SVG)
        return body

    svg   = se.SVG.parse(LOGO_SVG)
    paths = [e for e in svg.elements() if isinstance(e, se.Path)]
    if not paths:
        log.warning("No paths found in logo SVG — skipping engraving")
        return body

    wall_y = CX_W / 2.0  # 200.0 mm

    # ── UV mapping (shared by both walls) ─────────────────────────────────────
    def svg_to_uv(sx: float, sy: float):
        u = (sx - LOGO_SVG_XC) * LOGO_SCALE
        v = -(sy - LOGO_SVG_YC) * LOGO_SCALE + LOGO_WALL_CZ
        return (u, v)

    # ── Sample a list of path segments into SVG (x, y) points ─────────────────
    def sample_segments(segs, n_per_seg: int = 30):
        pts = []
        for seg in segs:
            if isinstance(seg, Move):
                pts.append((seg.end.x, seg.end.y))
            elif isinstance(seg, Close):
                pass
            elif isinstance(seg, Line):
                for k in range(n_per_seg):
                    t = k / n_per_seg
                    pts.append((
                        seg.start.x + t * (seg.end.x - seg.start.x),
                        seg.start.y + t * (seg.end.y - seg.start.y),
                    ))
            elif hasattr(seg, 'point'):
                for k in range(n_per_seg):
                    pt = seg.point(k / n_per_seg)
                    pts.append((pt.x, pt.y))
        return pts

    # ── Build a cutting solid from UV points on a wall plane ──────────────────
    def build_cut_solid(uv_pts, plane, extrude_vec):
        world_pts = [plane.toWorldCoords(cq.Vector(u, v, 0)) for u, v in uv_pts]
        # Deduplicate consecutive near-identical points
        clean = [world_pts[0]]
        for p in world_pts[1:]:
            if p.sub(clean[-1]).Length > 0.08:
                clean.append(p)
        if len(clean) < 4:
            return None
        # Close the polyline
        if clean[-1].sub(clean[0]).Length > 0.08:
            clean.append(clean[0])
        # Build polyline edges
        edges = []
        for i in range(len(clean) - 1):
            try:
                edges.append(cq.Edge.makeLine(clean[i], clean[i + 1]))
            except Exception:
                pass
        if len(edges) < 3:
            return None
        try:
            wire  = cq.Wire.assembleEdges(edges)
            solid = cq.Solid.extrudeLinear(wire, [], extrude_vec)
            return solid
        except Exception:
            return None

    # ── Wall plane + extrusion direction pairs ────────────────────────────────
    wall_configs = [
        (
            cq.Plane(origin=cq.Vector(0,  wall_y, 0),
                     xDir=cq.Vector(-1, 0, 0), normal=cq.Vector(0,  1, 0)),
            cq.Vector(0, -LOGO_DEPTH, 0),
        ),
        (
            cq.Plane(origin=cq.Vector(0, -wall_y, 0),
                     xDir=cq.Vector( 1, 0, 0), normal=cq.Vector(0, -1, 0)),
            cq.Vector(0,  LOGO_DEPTH, 0),
        ),
    ]

    n_cuts = 0
    for plane, extrude_vec in wall_configs:
        for path_elem in paths:
            # Split path into sub-paths with a Close segment
            cur, sub_lists = [], []
            for seg in path_elem._segments:
                if isinstance(seg, Move) and cur:
                    sub_lists.append(cur)
                    cur = [seg]
                else:
                    cur.append(seg)
            if cur:
                sub_lists.append(cur)
            sub_lists = [s for s in sub_lists
                         if any(isinstance(x, Close) for x in s)]

            for sub_segs in sub_lists:
                pts_svg = sample_segments(sub_segs)
                if len(pts_svg) < 4:
                    continue
                uv_pts = [svg_to_uv(x, y) for x, y in pts_svg]
                solid  = build_cut_solid(uv_pts, plane, extrude_vec)
                if solid is not None:
                    try:
                        body = body.cut(solid)
                        n_cuts += 1
                    except Exception as ex:
                        log.debug("Logo sub-path cut failed: %s", ex)

    log.info("Logo engraving: %d sub-path cuts applied to ±Y walls", n_cuts)
    return body


# ══════════════════════════════════════════════════════════════════════════════
#  LOGO INLAY MESHES  (colored fills for engraved cavities)
# ══════════════════════════════════════════════════════════════════════════════

# Inlay is 5 % shallower than the cavity so the visible face sits just inside
# the wall surface (avoids Z-fighting at the outer wall face).
LOGO_INLAY_DEPTH = LOGO_DEPTH * 0.95   # ≈ 1.9 mm


def _build_logo_inlay_mesh(path_indices: list) -> "cq.Workplane | None":
    """
    Build combined STL geometry for a subset of logo letter inlays.

    Each letter is built on both ±Y walls:
      • sub-path 0  → extruded inward (LOGO_INLAY_DEPTH) — letter outline body
      • sub-paths 1+ → cut from the letter body (counters for o, b, a, i, …)

    Returns a cq.Workplane containing the union of all letter solids, or None.
    """
    import svgelements as se
    from svgelements import Move, Close, Line

    if not os.path.isfile(LOGO_SVG):
        log.warning("Logo SVG not found (%s) — skipping inlay", LOGO_SVG)
        return None

    svg   = se.SVG.parse(LOGO_SVG)
    paths = [e for e in svg.elements() if isinstance(e, se.Path)]
    if not paths:
        return None

    wall_y = CX_W / 2.0   # 200.0 mm

    def svg_to_uv(sx: float, sy: float):
        u = (sx - LOGO_SVG_XC) * LOGO_SCALE
        v = -(sy - LOGO_SVG_YC) * LOGO_SCALE + LOGO_WALL_CZ
        return (u, v)

    def signed_area(pts):
        """Shoelace signed area of a polygon. Positive = CCW winding."""
        n = len(pts)
        a = 0.0
        for i in range(n):
            j = (i + 1) % n
            a += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        return a / 2.0

    def sample_segments(segs, n_per_seg: int = 30):
        pts = []
        for seg in segs:
            if isinstance(seg, Move):
                pts.append((seg.end.x, seg.end.y))
            elif isinstance(seg, Close):
                pass
            elif isinstance(seg, Line):
                for k in range(n_per_seg):
                    t = k / n_per_seg
                    pts.append((
                        seg.start.x + t * (seg.end.x - seg.start.x),
                        seg.start.y + t * (seg.end.y - seg.start.y),
                    ))
            elif hasattr(seg, 'point'):
                for k in range(n_per_seg):
                    pt = seg.point(k / n_per_seg)
                    pts.append((pt.x, pt.y))
        return pts

    def make_solid(uv_pts, plane, extrude_vec):
        world_pts = [plane.toWorldCoords(cq.Vector(u, v, 0)) for u, v in uv_pts]
        clean = [world_pts[0]]
        for p in world_pts[1:]:
            if p.sub(clean[-1]).Length > 0.08:
                clean.append(p)
        if len(clean) < 4:
            return None
        if clean[-1].sub(clean[0]).Length > 0.08:
            clean.append(clean[0])
        edges = []
        for i in range(len(clean) - 1):
            try:
                edges.append(cq.Edge.makeLine(clean[i], clean[i + 1]))
            except Exception:
                pass
        if len(edges) < 3:
            return None
        try:
            wire  = cq.Wire.assembleEdges(edges)
            solid = cq.Solid.extrudeLinear(wire, [], extrude_vec)
            return solid
        except Exception:
            return None

    # +Y wall: extrude inward (-Y direction); -Y wall: extrude inward (+Y direction)
    wall_configs = [
        (
            cq.Plane(origin=cq.Vector(0,  wall_y, 0),
                     xDir=cq.Vector(-1, 0, 0), normal=cq.Vector(0,  1, 0)),
            cq.Vector(0, -LOGO_INLAY_DEPTH, 0),
        ),
        (
            cq.Plane(origin=cq.Vector(0, -wall_y, 0),
                     xDir=cq.Vector( 1, 0, 0), normal=cq.Vector(0, -1, 0)),
            cq.Vector(0,  LOGO_INLAY_DEPTH, 0),
        ),
    ]
    # Counter extrusion is slightly deeper to punch cleanly through the inlay body
    counter_scale = 1.1

    all_solids = []
    for plane, ev in wall_configs:
        counter_ev = cq.Vector(ev.x * counter_scale, ev.y * counter_scale, ev.z * counter_scale)
        for idx in path_indices:
            if idx >= len(paths):
                continue
            path_elem = paths[idx]

            # Split path into closed sub-paths
            cur, sub_lists = [], []
            for seg in path_elem._segments:
                if isinstance(seg, Move) and cur:
                    sub_lists.append(cur)
                    cur = [seg]
                else:
                    cur.append(seg)
            if cur:
                sub_lists.append(cur)
            sub_lists = [s for s in sub_lists
                         if any(isinstance(x, Close) for x in s)]
            if not sub_lists:
                continue

            # Sub-path 0 → letter body
            pts_svg = sample_segments(sub_lists[0])
            if len(pts_svg) < 4:
                continue
            uv_0 = [svg_to_uv(x, y) for x, y in pts_svg]
            # Winding direction of primary outline — counters have opposite sign
            area_0 = signed_area(uv_0)
            letter_solid = make_solid(uv_0, plane, ev)
            if letter_solid is None:
                continue

            # Sub-paths 1+ — counter (cut) if winding OPPOSES primary outline,
            # else a separate filled glyph part (e.g. the dot on 'i') → fuse.
            for extra_segs in sub_lists[1:]:
                pts_c = sample_segments(extra_segs)
                if len(pts_c) < 4:
                    continue
                uv_c = [svg_to_uv(x, y) for x, y in pts_c]
                area_c = signed_area(uv_c)
                is_counter = (area_c > 0) != (area_0 > 0)   # opposite winding = hole
                if is_counter:
                    # True counter (hole) — cut with slightly deeper solid
                    extra_solid = make_solid(uv_c, plane, counter_ev)
                    if extra_solid is not None:
                        try:
                            letter_solid = letter_solid.cut(extra_solid)
                        except Exception as ex:
                            log.debug("Counter cut failed path %d: %s", idx, ex)
                else:
                    # Separate glyph part (e.g. dot on 'i') — extrude and fuse
                    extra_solid = make_solid(uv_c, plane, ev)
                    if extra_solid is not None:
                        try:
                            letter_solid = letter_solid.fuse(extra_solid)
                        except Exception as ex:
                            log.debug("Separate glyph fuse failed path %d: %s", idx, ex)

            all_solids.append(letter_solid)

    if not all_solids:
        log.warning("_build_logo_inlay_mesh: no solids built for indices %s", path_indices)
        return None

    # Collect into a compound — avoids expensive BREP fuse operations
    log.info("Logo inlay: built %d letter solids for path indices %s", len(all_solids), path_indices)
    compound = cq.Compound.makeCompound(all_solids)
    return cq.Workplane().add(compound)


def build_logo_robolabs() -> "cq.Workplane | None":
    """Inlay mesh for 'robolabs' letters (SVG paths 0–7) — white material."""
    return _build_logo_inlay_mesh(list(range(0, 8)))


def build_logo_ai() -> "cq.Workplane | None":
    """Inlay mesh for '.ai' letters (SVG paths 8–9) — green material."""
    return _build_logo_inlay_mesh([8, 9])


# ══════════════════════════════════════════════════════════════════════════════
#  DEPTH CAMERA MESHES  (Intel RealSense D435i, local link frame, mm)
# ══════════════════════════════════════════════════════════════════════════════
#
# Coordinate convention (matches URDF joint orientation, rpy="0 0 0"):
#   +X  forward  (points out of camera lens / toward scene)
#   +Y  left     (camera width axis)
#   +Z  up
#   Front face of camera housing at local x = +CAM_D/2 = +12.5 mm
#   Body centred at origin, so y ∈ [−45, +45], z ∈ [−12.5, +12.5]


def build_depth_camera_housing() -> cq.Workplane:
    """
    D435i camera housing — dark aluminium bar with a sensor-window recess.

    Geometry:
      • Main bar  90×25×25 mm with 1.5 mm edge fillets
      • Front-face sensor window: 78×16 mm rectangular recess 1.2 mm deep
        (shows the imaging strip; lenses protrude above this recess)
    """
    front_x = CAM_D / 2.0    # +12.5 mm

    # Main housing bar — fillet only the long vertical edges (4 edges along Z)
    housing = (
        cq.Workplane("XY")
        .box(CAM_D, CAM_W, CAM_H)
        .edges("|Z")
        .fillet(CAM_BODY_FILLET)
    )

    # Sensor window recess: cut 1.2 mm into the front face
    # The cut extends past CAM_D/2 (front face) in -X direction
    recess = (
        cq.Workplane("YZ")
        .transformed(offset=cq.Vector(0.0, 0.0, front_x))   # at front face
        .rect(CAM_WIN_W, CAM_WIN_H)
        .extrude(CAM_WIN_D)   # extrudes in +X (outward), then we cut
    )
    # We extrude outward and then subtract — net effect: recess into front face
    # Simpler: extrude a box from slightly inside the front face
    recess_box = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(
            front_x - CAM_WIN_D / 2.0, 0.0, 0.0))
        .box(CAM_WIN_D, CAM_WIN_W, CAM_WIN_H)
    )
    housing = housing.cut(recess_box)

    return housing


def build_depth_camera_lens() -> cq.Workplane:
    """
    Lens + emitter array for the D435i front face.

    Four dark discs protruding CAM_LENS_T mm proud of the front face:
      • IR dot projector  (emitter)
      • Left IR imager
      • RGB colour camera  (largest)
      • Right IR imager

    The discs sit in the sensor-window recess area, rising slightly above it.
    """
    front_x = CAM_D / 2.0   # +12.5 mm

    solids = []
    for (ly, lz, lr) in CAM_LENS_SPECS:
        disc = (
            cq.Workplane("YZ")
            # In YZ-plane: offset = (world_Y, world_Z, world_X-normal)
            .transformed(offset=cq.Vector(ly, lz, front_x))
            .circle(lr)
            .extrude(CAM_LENS_T)
        )
        solids.append(disc.val())

    compound = cq.Compound.makeCompound(solids)
    return cq.Workplane().add(compound)


def build_wheel() -> cq.Workplane:
    """
    Construct a single wheel mesh.

    Coordinate convention:
      • Wheel rotation axis is along Z in the STL.
      • The URDF visual applies  rpy="π/2 0 0"  which rotates Z → Y,
        so the wheel spins around the robot's lateral (Y) axis.
      • Wheel is centred at Z = 0  (spans −WH_W/2 … +WH_W/2).

    Geometry:
      • Outer tyre ring  — hollow cylinder (thick wall = TYRE_THICK)
      • Hub disc         — solid cylinder  (radius = HUB_R)
      • SPOKE_N spokes   — rectangular bars, evenly distributed radially
      • Wheel caps       — solid discs flush with both axial faces (r = WH_CAP_R)
    """

    # ── Tyre ring (outer cylinder – inner bore = annular profile) ─────────────
    tyre = (
        cq.Workplane("XY")
        .circle(WH_R)
        .circle(WH_R - TYRE_THICK)   # inner circle → ring cross-section
        .extrude(WH_W)
    )

    # ── Hub disc ───────────────────────────────────────────────────────────────
    hub = (
        cq.Workplane("XY")
        .circle(HUB_R)
        .extrude(WH_W)
    )

    wheel = tyre.union(hub)

    # ── Spokes ──────────────────────────────────────────────────────────────────
    spoke_len   = WH_R - TYRE_THICK - HUB_R   # 62.5 − 12 − 18 = 32.5 mm radial
    spoke_z_off = (WH_W - SPOKE_T) / 2.0      # (25 − 16) / 2  =  4.5 mm
    spoke_cx    = HUB_R + spoke_len / 2.0      # radial centre of spoke

    for i in range(SPOKE_N):
        angle_deg = 360.0 / SPOKE_N * i
        spoke = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(spoke_cx, 0.0, spoke_z_off))
            .box(spoke_len, SPOKE_W, SPOKE_T, centered=(True, True, False))
            .rotate((0, 0, 0), (0, 0, 1), angle_deg)
        )
        wheel = wheel.union(spoke)

    # ── Wheel caps (solid discs that cover the spoke area on both faces) ────────
    # Inner cap sits at z=0 (inner axial face of the un-translated wheel).
    # Outer cap sits at z=WH_W−WH_CAP_T (outer axial face).
    # After the final translate both caps land flush with each face of the tyre.
    inner_cap = (
        cq.Workplane("XY")
        .circle(WH_CAP_R)
        .extrude(WH_CAP_T)
    )
    outer_cap = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0.0, 0.0, WH_W - WH_CAP_T))
        .circle(WH_CAP_R)
        .extrude(WH_CAP_T)
    )
    wheel = wheel.union(inner_cap).union(outer_cap)

    # Centre wheel on Z = 0 (URDF places origin at wheel geometric centre)
    wheel = wheel.translate((0.0, 0.0, -WH_W / 2.0))

    return wheel


def build_wheel_cap() -> cq.Workplane:
    """
    Build just the two cap discs in the same coordinate frame as build_wheel().
    Exported as wheel_cap.stl so the URDF can give them a distinct colour.
    """
    inner_cap = (
        cq.Workplane("XY")
        .circle(WH_CAP_R)
        .extrude(WH_CAP_T)
    )
    outer_cap = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0.0, 0.0, WH_W - WH_CAP_T))
        .circle(WH_CAP_R)
        .extrude(WH_CAP_T)
    )
    caps = inner_cap.union(outer_cap)
    # Apply same centring translation as the full wheel
    caps = caps.translate((0.0, 0.0, -WH_W / 2.0))
    return caps


# ══════════════════════════════════════════════════════════════════════════════
#  PAYLOAD PLATFORM BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_payload_platform() -> cq.Workplane:
    """
    Construct the AMR load-carrying platform.

    The platform attaches to the robot at base_link (origin) via a fixed joint.
    All coordinates are in the base_link frame (mm); URDF applies scale=0.001.

    Z layout (mm):
      150–156   Foot flanges  — 36×36×6 mm square pads, one per post corner
      156–265   Post shafts   — Ø 24 mm solid round uprights (4 off)
      265–285   Top plate     — 440×320×20 mm, 10 mm vertical-edge fillet

    2-D LiDAR constraint:
      Sensor scans at z ≈ 180 mm (fully below platform at z=265).
      Posts at (±205, ±150) mm subtend < 3° each of the 360° scan arc.
    """

    # ── Top plate ──────────────────────────────────────────────────────────────
    plate = (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(PP_PLATE_CX, 0.0, PP_PLATE_Z))
        .box(PP_PLATE_L, PP_PLATE_W, PP_PLATE_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(PP_PLATE_FILLET)
    )

    # ── Corner posts + foot flanges ────────────────────────────────────────────
    for px, py in PP_POSTS:
        # Square foot flange (sits on chassis deck)
        foot = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(px, py, PP_POST_BOT_Z))
            .box(PP_POST_FOOT_W, PP_POST_FOOT_W, PP_POST_FOOT_H,
                 centered=(True, True, False))
            .edges("|Z")
            .fillet(6.0)
        )
        # Round post shaft
        shaft = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(px, py, PP_POST_BOT_Z + PP_POST_FOOT_H))
            .circle(PP_POST_R)
            .extrude(PP_POST_H)
        )
        plate = plate.union(foot).union(shaft)

    return plate


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT HELPER
# ══════════════════════════════════════════════════════════════════════════════

def export_stl(workplane: cq.Workplane, name: str) -> None:
    path = MESH_DIR / name
    exporters.export(
        workplane,
        str(path),
        tolerance=LINEAR_TOL,
        angularTolerance=ANGULAR_TOL,
    )
    size_kb = path.stat().st_size // 1024
    log.info("  %-20s  %5d KB   →  %s", name, size_kb, path)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    MESH_DIR.mkdir(parents=True, exist_ok=True)

    log.info("━━━  RLAI Mesh Generator  ━━━")

    log.info("Building chassis …")
    chassis = build_chassis()
    export_stl(chassis, "chassis.stl")

    log.info("Building wheel …")
    wheel = build_wheel()
    export_stl(wheel, "wheel.stl")

    log.info("Building wheel cap …")
    cap = build_wheel_cap()
    export_stl(cap, "wheel_cap.stl")

    log.info("Building payload platform …")
    platform = build_payload_platform()
    export_stl(platform, "payload_platform.stl")

    log.info("Building logo 'robolabs' inlay …")
    logo_robolabs = build_logo_robolabs()
    if logo_robolabs is not None:
        export_stl(logo_robolabs, "logo_robolabs.stl")
    else:
        log.warning("logo_robolabs mesh is empty — skipped")

    log.info("Building logo '.ai' inlay …")
    logo_ai = build_logo_ai()
    if logo_ai is not None:
        export_stl(logo_ai, "logo_ai.stl")
    else:
        log.warning("logo_ai mesh is empty — skipped")

    log.info("Building depth camera housing …")
    cam_housing = build_depth_camera_housing()
    export_stl(cam_housing, "depth_camera_housing.stl")

    log.info("Building depth camera lens array …")
    cam_lens = build_depth_camera_lens()
    export_stl(cam_lens, "depth_camera_lens.stl")

    log.info("Done — meshes written to %s", MESH_DIR)


if __name__ == "__main__":
    main()
