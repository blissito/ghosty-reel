"""
Prototipo: diagrama en 3D REAL, dibujado a mano.

La geometría son volúmenes de verdad; el modificador Line Art los recorre y
genera los trazos de Grease Pencil, que a su vez pasan por Noise para que
tiemblen como a mano. Resultado: la cámara puede orbitar y el dibujo se
redibuja solo, con paralaje verdadero — cosa imposible con trazos planos.

    blender -b -P proto3d.py            # 3 stills
    ANIM=1 blender -b -P proto3d.py     # 90 frames orbitando
"""
import bpy, math, os

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
ANIM = os.environ.get("ANIM")

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- escena ---
S.render.resolution_x, S.render.resolution_y = 1080, 1920
S.render.engine = 'BLENDER_EEVEE'
S.eevee.taa_render_samples = 16
S.eevee.use_shadows = False
S.eevee.use_fast_gi = False
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
S.render.fps = 30
S.world = bpy.data.worlds.new("W")
S.world.use_nodes = True
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0.043, 0.043, 0.055, 1)

AMBAR = (1.00, 0.80, 0.28)
VERDE = (0.40, 0.95, 0.65)
CIAN  = (0.35, 0.80, 1.00)
MORA  = (0.65, 0.45, 1.00)
ROJO  = (1.00, 0.42, 0.52)

GEO = bpy.data.collections.new("GEO")
S.collection.children.link(GEO)


def relleno(color, mezcla=0.05):
    """Relleno apenas más claro que el fondo: da cuerpo sin robar protagonismo
    a la línea. Emisión pura, como todo lo demás en el pipeline."""
    m = bpy.data.materials.new("f")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    bg = (0.043, 0.043, 0.055)
    e.inputs["Color"].default_value = (*[bg[i]*(1-mezcla) + color[i]*mezcla for i in range(3)], 1)
    e.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def losa(nombre, w, h, d, loc, color):
    """Un volumen real: la 'caja' del diagrama deja de ser un rectángulo."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = nombre
    ob.scale = (w/2, d/2, h/2)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(relleno(color))
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    GEO.objects.link(ob)
    # bisel: sin él las aristas son perfectas y el trazo se ve de máquina
    bv = ob.modifiers.new("bevel", 'BEVEL')
    bv.width, bv.segments = 0.06, 2
    return ob


def lineart(color, grosor=0.03, seed=0):
    """Un GP vacío cuyo contenido lo genera Line Art desde la geometría."""
    gp = bpy.data.grease_pencils.new("la")
    gp.stroke_depth_order = '3D'
    ob = bpy.data.objects.new("la", gp)
    S.collection.objects.link(ob)
    mat = bpy.data.materials.new("lm")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (*color, 1.0)
    gp.materials.append(mat)
    lay = gp.layers.new("L")
    lay.use_lights = False
    lay.radius_offset = grosor

    la = ob.modifiers.new("lineart", 'LINEART')
    la.source_type = 'COLLECTION'
    la.source_collection = GEO
    la.target_layer = lay.name
    la.target_material = mat
    la.use_contour = True
    la.use_crease = True
    la.use_intersection = True
    la.use_edge_mark = False
    la.use_material = False

    nz = ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
    nz.factor, nz.noise_scale, nz.factor_thickness = 0.5, 0.3, 0.4
    nz.seed = seed
    return ob


# ------------------------------------------------- el stack de contexto ---
# Las cuatro capas de la ventana de contexto, pero como losas apiladas de
# verdad: al orbitar se ve que una está encima de la otra.
CAPAS = [("system prompt", AMBAR), ("schema de tools", VERDE),
         ("historial", CIAN), ("mensaje", MORA)]
for i, (nom, col) in enumerate(CAPAS):
    losa(nom, 5.4, 0.85, 3.2, (0, 0, 2.6 - i*1.45), col)

losa("modelo", 2.8, 1.6, 2.0, (0, 0, -4.2), ROJO)

lineart((0.95, 0.95, 0.99), 0.075, 3)

# ---------------------------------------------------------------- cámara ---
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
S.collection.objects.link(cam)
S.camera = cam
cam.data.lens = 62

pivote = bpy.data.objects.new("piv", None)
S.collection.objects.link(pivote)
cam.parent = pivote
cam.location = (0, -13.5, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

# La órbita es el punto: con trazos planos no habría nada que orbitar.
for f, (rz, rx) in ((1, (-0.42, 0.20)), (45, (0.0, 0.30)), (90, (0.42, 0.20))):
    pivote.rotation_euler = (rx, 0, rz)
    pivote.keyframe_insert("rotation_euler", frame=f)

S.frame_start, S.frame_end = 1, 90
S.render.image_settings.file_format = 'PNG'
if ANIM:
    S.render.filepath = os.path.join(D, "out3d", "f_")
    bpy.ops.render.render(animation=True)
else:
    for f in (1, 45, 90):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out3d", f"p_{f:03d}")
        bpy.ops.render.render(write_still=True)
