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
# AgX (el default) es un tone mapping fotográfico: desatura y comprime los
# claros. En un diagrama de color plano eso apaga la paleta y vuelve gris el
# blanco. Para motion graphics 2D la transformación correcta es Standard.
# El default de EEVEE son 64 muestras + sombras + GI, pensado para render 3D con
# luces. Aquí NO hay una sola luz: todo es emisión plana. Bajar a 8 muestras y
# apagar sombras/GI da 3.5x (0.600 -> 0.173 s/frame) con una diferencia media de
# 0.004/255 contra el render a 64 — imperceptible. Súbelo con SPP=64 si algún día
# la escena lleva luces de verdad.
S.eevee.taa_render_samples = int(os.environ.get('SPP', 8))
if not os.environ.get('SLOW'):
    S.eevee.use_shadows = False
    S.eevee.use_fast_gi = False
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
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
    # '2D' (el default) dibuja los trazos ignorando la profundidad: se pintan
    # SIEMPRE encima de cualquier malla, esté donde esté. Con '3D' entran al
    # z-buffer y un objeto más cercano por fin los tapa.
    gp.stroke_depth_order = '3D'
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
    g.data.stroke_depth_order = '3D'
    for l in g.data.layers:
        l.use_lights = False
    for m in g.data.materials:
        if m and m.grease_pencil:
            m.grease_pencil.color = (*color, 1.0)
            m.grease_pencil.fill_color = (*color, 1.0)   # el texto es RELLENO
    build_in(g, a, b)
    only_between(g, max(1, a - 2), out if out else S.frame_end)
    return g


def img_plane(name, path, w, loc, seed=0.0, method='BLENDED'):
    """Plano con textura emisiva y alpha. BLENDED, no DITHERED: el dithering
    deja el borde del recorte moteado en un personaje de contorno suave."""
    im = bpy.data.images.load(path)
    ar = im.size[1] / im.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, w * ar, 1)
    ob.rotation_euler = (math.pi / 2, 0, 0)

    mat = bpy.data.materials.new(name + "_m")
    mat.use_nodes = True
    mat.surface_render_method = method
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.interpolation = 'Cubic'
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Strength"].default_value = 1.25
    tra = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])   # el alpha decide la mezcla
    nt.links.new(tra.outputs[0], mix.inputs[1])
    nt.links.new(emi.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------- 1. gancho ----
# Primeros 3s: solo texto. Sin diagrama que compita.
HOOK = (1.0, 1.0, 1.0)
CS_HOOK = 11.0 / CAM_D           # la cámara arranca cerca; el texto debe encoger
RED = (1.0, 0.45, 0.55)
CZ = -0.7                        # centro del diagrama; el gancho colapsa hacia ahí
for txt, z, col, dt in (("medio millón", 2.35, HOOK, 0.0), ("de líneas", 1.00, HOOK, 0.45),
                        ("ninguna es", -1.05, RED, 1.25), ("el modelo", -2.40, RED, 1.65)):
    g = gp_text(txt, 1.02, (0, 0.0, z), col, F(B["hook"] + dt), F(B["hook"] + dt + 0.75),
                out=F(B["hook_out"] + 0.25), cs=CS_HOOK)
    # Salida: las palabras se encogen hacia el centro justo cuando empieza a
    # trazarse el núcleo. Sin este solape quedaban 12 frames de cuadro vacío.
    for t, sc, dz in ((B["hook_out"] - 0.60, 1.0, 0.0),
                      (B["hook_out"] + 0.20, 0.10, (CZ - z) * CS_HOOK)):
        g.delta_scale = (sc, sc, 1.0)
        g.delta_location = (0, 0, dz)
        g.keyframe_insert("delta_scale", frame=F(t))
        g.keyframe_insert("delta_location", frame=F(t))
    for fc in fcurves(g):
        if "delta_" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_IN'

# ------------------------------------------------------------- 2. capas -----
def at_depth(v, y): return v * (CAM_D + y) / CAM_D

LAYERS = [
    ("modelo",     (1.00, 0.42, 0.52), 0.0, 2.7, 2.3, "nucleo"),
    ("tools",      (1.00, 0.80, 0.28), 1.0, 4.1, 4.2, "tools"),
    ("skills",     (0.40, 0.95, 0.65), 2.0, 5.5, 6.1, "skills"),
    ("mcp",        (0.35, 0.80, 1.00), 3.0, 6.6, 7.8, "mcp"),
    ("subagentes", (0.65, 0.45, 1.00), 4.0, 7.9, 9.6, "subs"),
]
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

gp_text("Taller",             0.52, (0, 0.0,  3.05), (0.62, 0.55, 0.98), F(B["cta"] - .2), F(B["cta"] + 0.5))
gp_text("Sistemas",           1.16, (0, 0.0,  1.75), (0.98, 0.98, 1.00), F(B["cta"] + .1), F(B["cta"] + 0.9))
gp_text("Agénticos",          1.16, (0, 0.0,  0.30), (0.98, 0.98, 1.00), F(B["cta"] + .4), F(B["cta"] + 1.2))
gp_text("1 de septiembre",    0.60, (0, 0.0, -1.65), (1.00, 0.80, 0.28), F(B["cta"] + 1.0), F(B["cta"] + 1.8))
gp_text("fixtergeek.com/sistemas-agenticos",
                              0.34, (0, 0.0, -6.30), (0.70, 0.70, 0.80), F(B["cta"] + 1.7), F(B["cta"] + 2.5))

def glow(name, radius, loc, color, strength, a, out=None, ramp_start=0.70):
    """Halo radial emisivo: el fondo de marca del cierre. Gradiente esférico con
    Mapping a -0.5, porque 'Generated' va 0..1 desde la ESQUINA del bbox."""
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (radius[0], radius[1], 1) if isinstance(radius, tuple) else (radius, radius, 1)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    mat = bpy.data.materials.new(name + "_m")
    mat.use_nodes = True
    mat.surface_render_method = 'BLENDED'
    nt = mat.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (-0.5, -0.5, -0.5)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = 'SPHERICAL'
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    # El halo debe apagarse DENTRO del encuadre. Si el plano es enorme y la caída
    # lenta, el cuadro solo ve el centro del gradiente y queda un lavado plano.
    ramp.color_ramp.elements[0].position = ramp_start
    ramp.color_ramp.elements[1].position = 1.0
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = (*color, 1.0)
    emi.inputs["Strength"].default_value = strength
    tra = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(coord.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix.inputs[0])
    nt.links.new(tra.outputs[0], mix.inputs[1])
    nt.links.new(emi.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out_n.inputs["Surface"])
    ob.data.materials.append(mat)
    only_between(ob, a, out if out else S.frame_end)
    return ob


# --------------------------------------------------- 4. fondo de marca -------
# Detrás del CTA, no en todo el video: en las capas competiría con los trazos.
# El plano se pasa del encuadre a propósito: si el halo termina dentro del cuadro
# se ve el canto recto del plano y deja de leerse como luz.
glow("glow_cta",  (26.0, 34.0), (0, 7.0, 0.9), (0.30, 0.17, 0.78), 0.34, F(B["cta"] - 0.6), ramp_start=0.55)
glow("glow_cta2", (13.0, 15.0), (0, 6.2, 1.5), (0.55, 0.36, 1.00), 0.20, F(B["cta"] - 0.4), ramp_start=0.45)

# Logo de marca, hasta arriba del cierre. Se usa el oficial tal cual: trae las
# letras oscuras con contorno blanco y sobre fondo oscuro lee igual que en el
# sitio. (Con AgX activo salía lavado; el culpable era el tone mapping, no el
# logo. LOGO=logo-light.png usa una variante aclarada desde el SVG.)
LOGO = img_plane("logo", os.path.join(D, "assets", os.environ.get("LOGO", "logo.png")),
                 4.35, (0, 0.0, 6.35))
only_between(LOGO, F(B["cta"] - 0.5), S.frame_end)
for dt, s in ((0.0, 0.86), (0.45, 1.0)):
    LOGO.delta_scale = (s, s, 1.0)
    LOGO.keyframe_insert("delta_scale", frame=F(B["cta"] - 0.5 + dt))
for fc in fcurves(LOGO):
    if "delta_scale" in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BACK'
            kp.easing = 'EASE_OUT'

# ------------------------------------------------------------- 5. Ghosty ----
# Acompaña todo el video y "narra": flota, se inclina y late con la voz.
GH = img_plane("ghosty", os.path.join(D, "assets", "ghosty.png"),
               1.30, (2.55, -6.0, -5.55), method='DITHERED')
GH_AR = GH.data.materials[0].node_tree.nodes["Image Texture"].image
GH_AR = GH_AR.size[1] / GH_AR.size[0]

# Recorrido por beats: entra abajo-derecha, sube junto al diagrama, y en el
# cierre se planta grande al centro. Posiciones APARENTES, corregidas por y.
# Delante de todo: los trazos viven en y=0..4, así que Ghosty va MUCHO más
# cerca de la cámara. Los BLENDED se ordenan por distancia del ORIGEN, y con
# sólo 2 unidades de separación el orden se volvía ambiguo entre frames.
GY = -6.0
GK = (CAM_D + GY) / CAM_D
PATH = [
    (B["hook"] + 0.4, 3.05, -6.10, 0.72),
    (B["hook_out"],   2.60, -4.90, 0.95),
    (B["tools"],      2.95, -3.40, 1.05),
    (B["skills"],    -3.00, -2.60, 1.05),
    (B["mcp"],       -3.15,  3.10, 1.05),
    (B["subs"],       3.20,  3.60, 1.05),
    (B["harness"],    3.00, -4.20, 1.15),
    (B["cta"] - 0.5,  0.00, -3.95, 2.55),
    (B["end"],        0.00, -3.95, 2.55),
]
for t, x, z, sc in PATH:
    GH.location = (x * GK, GY, z * GK)
    GH.scale = (sc * GK, sc * GK * GH_AR, 1)
    GH.keyframe_insert("location", frame=F(t))
    GH.keyframe_insert("scale", frame=F(t))

# Cabeceo: flotar es una senoidal encima del recorrido, no parte de él.
for f in range(1, S.frame_end + 1, 5):
    t = f / FPS
    GH.rotation_euler = (math.pi / 2, 0, math.radians(7.0 * math.sin(t * 1.9)))
    GH.keyframe_insert("rotation_euler", frame=f)
    GH.delta_location = (0, 0, 0.20 * math.sin(t * 2.6 + 1.1))
    GH.keyframe_insert("delta_location", frame=f)

# "Habla": late apenas mientras hay voz. Sin esto sólo flota, no narra.
VO = json.load(open(os.path.join(D, "scene.json")))["vo"]
for v in VO:
    for dt, s in ((0.0, 1.0), (0.12, 1.075), (0.30, 1.0)):
        GH.delta_scale = (s, s, 1.0)
        GH.keyframe_insert("delta_scale", frame=F(v["at"] + dt))
    GH.delta_scale = (1.0, 1.0, 1.0)
    GH.keyframe_insert("delta_scale", frame=F(v["at"] + v["dur"]))

for fc in fcurves(GH):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ------------------------------------------------------------- 6. cámara ----
# retroceso lento: el encuadre se abre conforme nacen las capas
for t, d in ((0.0, 11.0), (B["nucleo"], 11.0), (B["subs"] + 1.0, 16.0), (B["cta"] - 0.4, 16.0)):
    cam.location = (0, -d, 0)
    cam.keyframe_insert("location", frame=F(t))
for fc in fcurves(cam):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ----------------------------------------------- 7. separación de pasadas ----
# EEVEE dibuja los trazos de Grease Pencil SIEMPRE encima de las mallas. No es
# un problema de orden ni de z-buffer: se comprobó con las cuatro combinaciones
# de stroke_depth_order (2D/3D) x surface_render_method (DITHERED/BLENDED) y el
# trazo gana en todas. Por eso Ghosty se renderiza en su propia pasada con fondo
# transparente y se compone encima con ffmpeg (ver mix.sh).
COL_MAIN = bpy.data.collections.new("MAIN")
COL_GH = bpy.data.collections.new("GH")
S.collection.children.link(COL_MAIN)
S.collection.children.link(COL_GH)
# Recorrer S.objects, NO S.collection.objects: bpy.ops.mesh.primitive_plane_add
# enlaza a una colección llamada "Collection", no a la master de la escena, así
# que los planos (personaje, logo, halos) quedaban fuera del reparto y salían en
# LAS DOS pasadas. Hay que desenlazar de todas sus colecciones actuales.
for o in list(S.objects):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    (COL_GH if o is GH else COL_MAIN).objects.link(o)
COL_GH.objects.link(cam)        # la cámara debe vivir en ambas pasadas

ONLY_GH = os.environ.get("ONLY") == "ghosty"
for c in bpy.context.view_layer.layer_collection.children:
    if c.name == "MAIN":
        c.exclude = ONLY_GH
    elif c.name == "GH":
        c.exclude = not ONLY_GH
S.render.film_transparent = ONLY_GH

# ------------------------------------------------------------- 8. salida ----
S.render.image_settings.file_format = 'PNG'
if ONLY_GH:
    S.render.image_settings.color_mode = 'RGBA'
S.render.filepath = os.path.join(D, "out", "ghosty" if ONLY_GH else "frames", "f_")

if PREVIEW:
    frames = os.environ.get("FRAMES")
    picks = [int(x) for x in frames.split(",")] if frames else \
            [F(B[k]) + 12 for k in ("hook", "nucleo", "tools", "mcp", "harness", "cta")]
    for f in picks:
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "preview", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
elif os.environ.get('RANGE'):
    a, b = (int(x) for x in os.environ['RANGE'].split(','))
    S.frame_start, S.frame_end = a, b     # re-render de un tramo, sin repetir todo
    bpy.ops.render.render(animation=True)
elif os.environ.get('BENCH'):
    S.frame_start, S.frame_end = 400, 439      # 40 frames del tramo con capas
    bpy.ops.render.render(animation=True)
else:
    bpy.ops.render.render(animation=True)
