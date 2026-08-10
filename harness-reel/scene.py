"""
Reel 9:16 — "El harness" · Taller Sistemas Agénticos.
Diagrama trazado a mano (Grease Pencil) con estructura Open Loop.

    blender -b -P scene.py                 # render completo
    PREVIEW=1 blender -b -P scene.py       # stills al 40% en los beats
    PREVIEW=1 FRAMES=120,540 blender -b -P scene.py
"""
import bpy, math, os, json

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
PREVIEW = os.environ.get("PREVIEW")
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- render ----
S.render.resolution_x, S.render.resolution_y = 1080, 1920
S.render.resolution_percentage = 40 if PREVIEW else 100
S.render.engine = 'BLENDER_EEVEE'
S.render.fps = FPS
S.world = bpy.data.worlds.new("W")
S.world.use_nodes = True
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0.043, 0.043, 0.055, 1)

CAM_D, PLANE_W = 16.0, 9.0        # el dimensionado se calcula contra CAM_D final
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
S.collection.objects.link(cam)
S.camera = cam
cam.rotation_euler = (math.pi / 2, 0, 0)
cam.data.sensor_fit = 'HORIZONTAL'      # en 9:16 el angle iría a la ALTURA
cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)

# ----------------------------------------------------------------- beats ----
# derivados de las duraciones reales de la voz (audio/vo/voN.wav)
B = json.load(open(os.path.join(D, "scene.json")))["beats"]
S.frame_start, S.frame_end = 1, F(B["end"])   # antes de crear nada: only_between lo lee
DIAG_OUT = F(B["cta"] - 0.35)                 # el diagrama se retira al entrar el CTA

# ------------------------------------------------------------- utilidades ----
def fcurves(id_data):
    act = id_data.animation_data.action
    if hasattr(act, "fcurves"):
        yield from act.fcurves
        return
    slot = id_data.animation_data.action_slot
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot)
            if cb:
                yield from cb.fcurves


def only_between(o, a, z):
    """Lo que no está en escena tiene que SALIR DEL RENDER, no solo ser invisible."""
    for f, hidden in ((1, True), (max(2, int(a) - 1), False), (int(z) + 1, True)):
        o.hide_render = hidden
        o.keyframe_insert("hide_render", frame=f)
    for fc in fcurves(o):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def gp_material(name, color):
    mat = bpy.data.materials.new(name)
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (*color, 1.0)
    mat.grease_pencil.fill_color = (*color, 1.0)
    return mat


def rounded_rect(w, h, r, n=14):
    pts = []
    for ox, oy, a0 in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, math.pi/2),
                       (-w/2+r, -h/2+r, math.pi), (w/2-r, -h/2+r, 3*math.pi/2)):
        for i in range(n + 1):
            a = a0 + (math.pi / 2) * i / n
            pts.append((ox + r * math.cos(a), 0.0, oy + r * math.sin(a)))
    return pts + [pts[0]]


def build_in(ob, a, b):
    bd = ob.modifiers.new("build", 'GREASE_PENCIL_BUILD')
    bd.use_percentage = True
    for f, v in ((max(1, a - 1), 0.0), (a, 0.0), (b, 1.0)):
        bd.percentage_factor = v
        bd.keyframe_insert("percentage_factor", frame=f)
    return bd


def make_gp(name, pts, color, loc, radius=0.03, seed=0):
    gp = bpy.data.grease_pencils.new(name)
    ob = bpy.data.objects.new(name, gp)
    S.collection.objects.link(ob)
    gp.materials.append(gp_material(name + "_m", color))
    lay = gp.layers.new("L")
    lay.use_lights = False
    d = lay.frames.new(1).drawing
    d.add_strokes([len(pts)])
    st = d.strokes[0]
    st.cyclic = False
    for i, p in enumerate(pts):
        st.points[i].position = p
        st.points[i].radius = radius
        st.points[i].opacity = 1.0
    ob.location = loc
    nz = ob.modifiers.new("noise", 'GREASE_PENCIL_NOISE')
    nz.factor, nz.noise_scale, nz.factor_thickness = 0.6, 0.35, 0.5
    nz.seed = seed
    return ob


def gp_text(body, size, loc, color, a, b, out=None, align='CENTER', cs=1.0):
    """size y loc son APARENTES (unidades del plano z=0 con la cámara en CAM_D).
    `cs` = distancia de cámara en ese beat / CAM_D, porque el retroceso cambia el
    encuadre. Sin esta corrección el texto se magnifica y se sale del cuadro."""
    y = loc[1]
    k = cs * (CAM_D + y) / CAM_D
    cu = bpy.data.curves.new("txt", 'FONT')
    cu.body, cu.size = body, size * k
    cu.align_x, cu.align_y = align, 'CENTER'
    ob = bpy.data.objects.new("t_" + body[:10].replace(" ", "_"), cu)
    S.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = (loc[0] * k, y, loc[2] * k)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='GREASEPENCIL')
    g = bpy.context.view_layer.objects.active
    for l in g.data.layers:
        l.use_lights = False
    for m in g.data.materials:
        if m and m.grease_pencil:
            m.grease_pencil.color = (*color, 1.0)
            m.grease_pencil.fill_color = (*color, 1.0)   # el texto es RELLENO
    build_in(g, a, b)
    only_between(g, max(1, a - 2), out if out else S.frame_end)
    return g


# ------------------------------------------------------------- 1. gancho ----
# Primeros 3s: solo texto. Sin diagrama que compita.
HOOK = (1.0, 1.0, 1.0)
CS_HOOK = 11.0 / CAM_D           # la cámara arranca cerca; el texto debe encoger
RED = (1.0, 0.45, 0.55)
for txt, z, col, dt in (("medio millón", 2.35, HOOK, 0.0), ("de líneas", 1.00, HOOK, 0.45),
                        ("ninguna es", -1.05, RED, 1.25), ("el modelo", -2.40, RED, 1.65)):
    gp_text(txt, 1.02, (0, 0.0, z), col, F(B["hook"] + dt), F(B["hook"] + dt + 0.75),
            out=F(B["hook_out"]), cs=CS_HOOK)

# ------------------------------------------------------------- 2. capas -----
def at_depth(v, y): return v * (CAM_D + y) / CAM_D

LAYERS = [
    ("modelo",     (1.00, 0.42, 0.52), 0.0, 2.7, 2.3, "nucleo"),
    ("tools",      (1.00, 0.80, 0.28), 1.0, 4.1, 4.2, "tools"),
    ("skills",     (0.40, 0.95, 0.65), 2.0, 5.5, 6.1, "skills"),
    ("mcp",        (0.35, 0.80, 1.00), 3.0, 6.6, 7.8, "mcp"),
    ("subagentes", (0.65, 0.45, 1.00), 4.0, 7.9, 9.6, "subs"),
]
CZ = -0.7
for i, (nm, col, y, aw, ah, key) in enumerate(LAYERS):
    a = F(B[key])
    ob = make_gp(nm, rounded_rect(at_depth(aw, y), at_depth(ah, y), at_depth(0.5, y)),
                 col, (0, y, at_depth(CZ, y)), radius=at_depth(0.026, y), seed=i * 7)
    build_in(ob, a, a + int(0.85 * FPS))
    only_between(ob, a - 1, DIAG_OUT)
    # etiqueta sobre el canto superior de cada capa
    lz = CZ + ah / 2 - 0.42
    gp_text(nm, 0.30, (0, y - 0.35, lz), col, a + 6, a + 20, out=DIAG_OUT)

# -------------------------------------------------------------- 3. cierre ----
gp_text("el harness", 0.80, (0, 0.0, 6.30), (0.96, 0.96, 0.99),
        F(B["harness"]), F(B["harness"] + 1.0), out=F(B["cta"] - 0.2))

gp_text("Sistemas Agénticos", 0.74, (0, 0.0,  1.35), (0.96, 0.96, 0.99), F(B["cta"]),      F(B["cta"] + 0.9))
gp_text("1 de septiembre",    0.54, (0, 0.0, -0.45), (1.00, 0.80, 0.28), F(B["cta"] + .7), F(B["cta"] + 1.5))
gp_text("fixtergeek.com",     0.32, (0, 0.0, -6.40), (0.55, 0.55, 0.62), F(B["cta"] + 1.4), F(B["cta"] + 2.1))

# ------------------------------------------------------------- 4. cámara ----
# retroceso lento: el encuadre se abre conforme nacen las capas
for t, d in ((0.0, 11.0), (B["nucleo"], 11.0), (B["subs"] + 1.0, 16.0), (B["cta"] - 0.4, 16.0)):
    cam.location = (0, -d, 0)
    cam.keyframe_insert("location", frame=F(t))
for fc in fcurves(cam):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ------------------------------------------------------------- 5. salida ----
S.render.image_settings.file_format = 'PNG'
S.render.filepath = os.path.join(D, "out", "f_")

if PREVIEW:
    frames = os.environ.get("FRAMES")
    picks = [int(x) for x in frames.split(",")] if frames else \
            [F(B[k]) + 12 for k in ("hook", "nucleo", "tools", "mcp", "harness", "cta")]
    for f in picks:
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "preview", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
