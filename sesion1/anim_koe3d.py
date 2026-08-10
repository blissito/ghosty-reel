"""
Experimento: objetos 3D en wireframe blanco (referencia Dan Koe).

Geometría 3D de verdad, con el contorno generado por Line Art y un material
NEGRO PURO en las mallas: contra el fondo negro desaparecen, pero siguen
ocultando las aristas de atrás. Eso da el wireframe limpio, con líneas ocultas
eliminadas — que es lo que distingue esos dibujos de una maraña de alambre.

La idea, sin una sola etiqueta dentro de la figura: el modelo es el punto que
brilla, el harness son las cajas que lo envuelven. La cámara rodea y se ve que
son cajas de verdad.

    blender -b -P anim_koe3d.py            # secuencia -> out_koe3d/
    STILL=1 blender -b -P anim_koe3d.py    # stills
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import texto, bloom

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
S.render.fps = FPS
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

FIN = 12.0
S.frame_start, S.frame_end = 1, F(FIN)

GEO = bpy.data.collections.new("GEO")
S.collection.children.link(GEO)
giro = bpy.data.objects.new("giro", None)
S.collection.objects.link(giro)


def invisible():
    """Material transparente. La malla tiene que EXISTIR —Line Art la recorre
    para generar el contorno— pero no debe pintarse: con material negro las
    caras tapaban el núcleo y las cajas interiores."""
    m = bpy.data.materials.new("inv")
    m.use_nodes = True
    m.surface_render_method = 'BLENDED'
    nt = m.node_tree
    nt.nodes.clear()
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs[0], o.inputs["Surface"])
    return m


def caja3d(w, h, d, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.scale = (w/2, d/2, h/2)
    # location=False y rotation=False EXPLÍCITOS: los defaults del operador son
    # True, así que 'aplicar la escala' también horneaba la posición y dejaba
    # el origen del objeto en (0,0,0) — los hijos aterrizaban en el centro.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.rotation_euler = rot
    ob.data.materials.append(invisible())
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    GEO.objects.link(ob)
    ob.parent = giro
    return ob


def lineart(grosor=0.020):
    gp = bpy.data.grease_pencils.new("la")
    gp.stroke_depth_order = '3D'
    ob = bpy.data.objects.new("la", gp)
    S.collection.objects.link(ob)
    mat = bpy.data.materials.new("lm")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (1, 1, 1, 1)
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
    # Por defecto Line Art dibuja SÓLO lo visible, así que la caja de fuera
    # borraba todo lo de dentro. Los "levels" son cuántas veces puede estar
    # ocluida una línea y aun así dibujarse: con 0..3 se ve la estructura entera,
    # como en un dibujo técnico.
    la.use_multiple_levels = True
    la.level_start = 0
    la.level_end = 3
    # temblor mínimo: mucho ruido aquí ensucia la geometría y se pierde la
    # sensación de objeto construido
    nz = ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
    nz.factor, nz.noise_scale, nz.factor_thickness = 0.10, 0.5, 0.15
    nz.use_random = bool(os.environ.get("BOIL"))
    nz.step = 6
    return ob


# --------------------------------------------------- las cajas del harness --
# Tres cajas anidadas, cada una girada un poco distinto: alineadas se leerían
# como una sola caja gruesa.
caja3d(6.4, 6.4, 6.4, (0, 0, 0), (0.0, 0.0, 0.0))
caja3d(4.3, 4.3, 4.3, (0, 0, 0), (0.0, 0.0, math.radians(28)))
caja3d(2.5, 2.5, 2.5, (0, 0, 0), (math.radians(20), 0.0, math.radians(50)))
lineart(0.030)

# ------------------------------------------------------------- el núcleo ---
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.34, location=(0, 0, 0))
nuc = bpy.context.object
m = bpy.data.materials.new("nm")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission")
e.inputs["Color"].default_value = (1, 1, 1, 1)
# muy por encima de 1: el bloom sólo sangra donde el píxel se satura, así que un
# blanco "normal" brillaría igual que las líneas y no se leería como fuente
e.inputs["Strength"].default_value = 16.0
o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(e.outputs[0], o.inputs["Surface"])
nuc.data.materials.append(m)
nuc.parent = giro
for t in [x*0.5 for x in range(int(FIN*2) + 1)]:
    s = 1.0 + 0.13*math.sin(t*1.5)
    nuc.scale = (s, s, s)
    nuc.keyframe_insert("scale", frame=F(t))
for fc in lib._fc(nuc):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ---------------------------------------------------------------- el giro --
# Dos ejes a la vez y lento. Sobre un solo eje se lee como GIF.
for f, rot in ((1, (0.22, 0.0, -0.5)), (F(FIN), (-0.10, 0.0, 0.75))):
    giro.rotation_euler = rot
    giro.keyframe_insert("rotation_euler", frame=f)
for fc in lib._fc(giro):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# ---------------------------------------------------------- subtítulos -----
LINEAS = [(1.2, "un agente no es un modelo"),
          (4.0, "el modelo es el punto del centro"),
          (7.0, "todo lo demás lo construyes tú"),
          (9.6, "eso es el harness")]
for i, (t, txt) in enumerate(LINEAS):
    fin = F(LINEAS[i + 1][0] - 0.15) if i + 1 < len(LINEAS) else F(FIN)
    texto(txt, 0, -6.1, 0.30, (0.88, 0.88, 0.92), build=(F(t), F(t + 0.5)), out=fin)

cam = S.camera
cam.location = (0, -11.5, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

bloom(fuerza=1.5, umbral=0.02, tam=0.9, suavidad=0.5)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(2.0), F(5.0), F(8.0), F(11.0)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_koe3d", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_koe3d", "f_")
    bpy.ops.render.render(animation=True)
