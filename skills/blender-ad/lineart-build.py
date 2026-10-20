"""
Contorno que se dibuja solo: Line Art de Grease Pencil + Build (Blender 5.2).

Mallas 3D con color plano (emisión, sin luces), un objeto Grease Pencil con
modificador Line Art que saca su silueta en tinta, y un Build encima que la
traza del frame A al B. Es el modo toon de scene.py con el contorno animado.

    blender -b -P lineart-build.py                       # secuencia en seq_lineart/
    STILLS=12,30,60 OUT=/tmp/x blender -b -P lineart-build.py   # sólo stills

Nombres verificados en 5.2.2: el modificador es "LINEART" (no
"GREASE_PENCIL_LINEART"); el Build sí es "GREASE_PENCIL_BUILD" y anima
`percentage_factor` sobre los trazos que Line Art genera en el mismo stack.
"""
import bpy, math, os

INK, PAPER = "#141A1F", "#F7F0E4"
DRAW_A, DRAW_B = 1, 40          # el contorno se traza en estos frames
FILL_IN = 34                    # el relleno entra cuando el trazo casi cierra


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*[v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
              for v in c], 1.0)


def flat(name, hex_):
    """Emisión a fuerza 1: con view Standard el PNG sale con el mismo hex."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = srgb(hex_)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


S = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
S.render.engine = "BLENDER_EEVEE"
S.render.resolution_x, S.render.resolution_y = 540, 960
S.render.fps, S.frame_start, S.frame_end = 30, 1, 60
S.view_settings.view_transform = "Standard"      # AgX lava la paleta
S.view_settings.look = "None"
S.render.dither_intensity = 0.0
S.render.use_motion_blur = False
S.world = bpy.data.worlds.new("W")
S.world.use_nodes = True
S.world.node_tree.nodes["Background"].inputs[0].default_value = srgb(PAPER)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
S.collection.objects.link(cam)
S.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 9.0
cam.data.dof.use_dof = False                    # sin desenfoque
cam.location = (9, -9, 7.4)
cam.rotation_euler = (math.radians(60), 0, math.radians(45))

# --- lo que se contornea vive en su propia colección --------------------------
col = bpy.data.collections.new("Outline")
S.collection.children.link(col)


def add(op, name, hex_, **kw):
    op(**kw)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(flat(name + "M", hex_))
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


box = add(bpy.ops.mesh.primitive_cube_add, "Box", "#F5C542",
          size=2.4, location=(0, 0, 1.2))
can = add(bpy.ops.mesh.primitive_cylinder_add, "Can", "#F29130",
          vertices=48, radius=0.8, depth=1.6, location=(2.6, -0.6, 0.8))

# Sombra dura: la huella del objeto en tinta, desplazada en el piso. Plana, sin
# alpha ni gradiente; nunca entra a la colección del contorno.
for src, dx, dy in ((box, 0.8, 0.1), (can, 0.6, 0.05)):
    sh = src.copy()
    sh.data = src.data.copy()
    sh.data.materials.clear()
    sh.data.materials.append(flat("Shadow", INK))
    sh.scale = (1, 1, 0.001)
    sh.location = (src.location.x + dx, src.location.y + dy, 0.0)
    S.collection.objects.link(sh)

# --- Line Art + Build ------------------------------------------------------------
gp = bpy.data.grease_pencils.new("Lineart")
la_ob = bpy.data.objects.new("Lineart", gp)
S.collection.objects.link(la_ob)
ink = bpy.data.materials.new("Ink")
bpy.data.materials.create_gpencil_data(ink)
ink.grease_pencil.color = srgb(INK)
gp.materials.append(ink)
lay = gp.layers.new("Lines")
lay.use_lights = False                  # sin esto la tinta sale gris
lay.frames.new(1)

la = la_ob.modifiers.new("Lineart", "LINEART")
la.source_type = "COLLECTION"
la.source_collection = col
la.target_layer = "Lines"
la.target_material = ink
la.radius = 0.06                        # grosor de tinta, en unidades de mundo
la.use_crease = True                    # aristas del cubo también, no sólo silueta
la.use_intersection = False

bd = la_ob.modifiers.new("Build", "GREASE_PENCIL_BUILD")
bd.use_percentage = True                # percentage_factor, no frame_start
for f, v in ((DRAW_A, 0.0), (DRAW_B, 1.0)):
    bd.percentage_factor = v
    bd.keyframe_insert("percentage_factor", frame=f)

# El relleno aparece cuando el trazo casi termina: antes sólo se ve la tinta.
# OJO: con hide_render el objeto sale del depsgraph y Line Art ya no lo ve (el
# contorno no se dibuja nada hasta que aparece el relleno). Se oculta a la
# CÁMARA con visible_camera: sigue en la escena y Line Art lo contornea.
for o in list(col.objects) + [o for o in S.collection.objects
                              if o.name.startswith(("Box.", "Can."))]:
    for f, vis in ((1, False), (FILL_IN, True)):
        o.visible_camera = vis
        o.keyframe_insert("visible_camera", frame=f)

out = os.environ.get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "seq_lineart")
S.render.image_settings.file_format = "PNG"
if os.environ.get("STILLS"):
    for f in (int(x) for x in os.environ["STILLS"].split(",")):
        S.frame_set(f)
        S.render.filepath = os.path.join(out, f"f{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(out, "f_")
    bpy.ops.render.render(animation=True)
