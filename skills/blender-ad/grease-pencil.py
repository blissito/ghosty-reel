"""
Ejemplo mínimo de diagrama trazado a mano con Grease Pencil (Blender 5.2 / GPv3).
Capas concéntricas que se dibujan solas + texto que se escribe solo, en 9:16.

    blender -b -P grease-pencil.py
    ffmpeg -y -framerate 30 -i seq/f_%04d.png -c:v libx264 -pix_fmt yuv420p out.mp4

110 frames ~9s en CPU/GPU modesta. Verifica los gotchas documentados en SKILL.md.
"""
import bpy, math, os

S = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# --- vertical 9:16 -----------------------------------------------------------
S.render.resolution_x, S.render.resolution_y = 540, 960
S.render.engine = 'BLENDER_EEVEE'          # NO 'BLENDER_EEVEE_NEXT'
S.world = bpy.data.worlds.new("W")
S.world.use_nodes = True
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0.043, 0.043, 0.055, 1)

CAM_D, PLANE_W, PLANE_H = 16.0, 9.0, 16.0
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
S.collection.objects.link(cam)
S.camera = cam
cam.location = (0, -CAM_D, 0)
cam.rotation_euler = (math.pi / 2, 0, 0)
cam.data.sensor_fit = 'HORIZONTAL'         # en 9:16 el angle iría a la ALTURA
cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)


def gp_material(name, color):
    mat = bpy.data.materials.new(name)
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (*color, 1.0)
    mat.grease_pencil.fill_color = (*color, 1.0)
    return mat


def rounded_rect(w, h, r, n=12):
    """Contorno con arcos reales. El primer punto se repite al final: cerrar a
    mano evita la cuerda que Build dibuja sobre un trazo cyclic incompleto."""
    pts = []
    for ox, oy, a0 in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, math.pi/2),
                       (-w/2+r, -h/2+r, math.pi), (w/2-r, -h/2+r, 3*math.pi/2)):
        for i in range(n + 1):
            a = a0 + (math.pi / 2) * i / n
            pts.append((ox + r * math.cos(a), 0.0, oy + r * math.sin(a)))
    return pts + [pts[0]]


def build_in(ob, a, b):
    """El trazo se dibuja del frame a al b. percentage_factor, no frame_start."""
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
    lay.use_lights = False                 # sin esto el color sale apagado
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
    nz.seed = seed                         # 'seed', no 'random_seed'
    return ob


def gp_text(body, size, loc, color, a, b):
    cu = bpy.data.curves.new("txt", 'FONT')
    cu.body, cu.size = body, size
    cu.align_x = cu.align_y = 'CENTER'
    ob = bpy.data.objects.new("txt_" + body[:8], cu)
    S.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = loc
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='GREASEPENCIL')   # enum sin guion bajo
    g = bpy.context.view_layer.objects.active
    for l in g.data.layers:
        l.use_lights = False
    for m in g.data.materials:
        if m and m.grease_pencil:
            m.grease_pencil.color = (*color, 1.0)
            m.grease_pencil.fill_color = (*color, 1.0)  # el texto es RELLENO
    build_in(g, a, b)
    return g


# --- escena: el modelo al centro, el harness envolviéndolo --------------------
# tamanos APARENTES (en unidades del plano z=0); el actual se corrige por profundidad
def at_depth(v, y): return v * (CAM_D + y) / CAM_D

LAYERS = [
    ("modelo",     (1.00, 0.42, 0.52), 0.0, 2.7,  2.3),
    ("tools",      (1.00, 0.80, 0.28), 1.0, 4.1,  4.2),
    ("skills",     (0.40, 0.95, 0.65), 2.0, 5.5,  6.1),
    ("mcp",        (0.35, 0.80, 1.00), 3.0, 6.6,  7.8),
    ("subagentes", (0.65, 0.45, 1.00), 4.0, 7.9,  9.6),
]
CZ = -0.7                       # centro del diagrama, algo bajo el medio
for i, (nm, col, y, aw, ah) in enumerate(LAYERS):
    w, h = at_depth(aw, y), at_depth(ah, y)
    ob = make_gp(nm, rounded_rect(w, h, at_depth(0.5, y)), col,
                 (0, y, at_depth(CZ, y)), radius=at_depth(0.028, y), seed=i * 7)
    build_in(ob, 1 + i * 14, 1 + i * 14 + 26)

gp_text("el harness", 0.78, (0, -2.0, 6.2), (0.95, 0.95, 0.98), 40, 75)
gp_text("modelo",  0.34, (0, -0.9, CZ), (1.00, 0.55, 0.62), 55, 80)
gp_text("fixtergeek.com", 0.26, (0, -2.0, -6.6), (0.55, 0.55, 0.62), 85, 100)

S.render.fps = 30
S.frame_start, S.frame_end = 1, 110
S.render.image_settings.file_format = 'PNG'   # este Blender no trae 'FFMPEG'
S.render.filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seq", "f_")
bpy.ops.render.render(animation=True)
