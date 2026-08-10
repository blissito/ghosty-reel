"""
Experimento: estilo monocromo luminoso (referencia Dan Koe).

Cambia todo respecto de la cheat sheet: sin color, sin cajas, sin etiquetas
dentro de la figura. Una sola forma geométrica de líneas finas girando despacio,
un núcleo que sangra luz, y el texto abajo como subtítulo.

Encaja raro de bien con nuestro tema: el modelo es el punto brillante del centro
y el harness son las capas de geometría que lo envuelven. La figura DICE la idea
sin una sola etiqueta.

    blender -b -P anim_koe.py            # secuencia -> out_koe/
    STILL=1 blender -b -P anim_koe.py    # stills
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import trazo, texto, dibujar, bloom, solo_entre

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
S.render.fps = FPS
# Negro puro, no el casi-negro de las cheat sheets: aquí el fondo no es una
# superficie de lectura sino vacío, y el bloom necesita que no haya piso.
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

FIN = 10.0
S.frame_start, S.frame_end = 1, F(FIN)
BLANCO = (1.0, 1.0, 1.0)

grupo = bpy.data.objects.new("giro", None)
S.collection.objects.link(grupo)


def anillo(radio, eje_rot, angulo, grosor=0.012, seed=0, build=None):
    """Un aro de líneas. Girando el objeto se colocan en 3D: juntos forman la
    esfera de alambre sin modelar nada."""
    n = 64
    pts = [(radio*math.cos(2*math.pi*i/n), radio*math.sin(2*math.pi*i/n))
           for i in range(n + 1)]
    ob = trazo(pts, BLANCO, grosor, seed, ruido=0.25, build=build)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = tuple(angulo if e == eje_rot else 0.0 for e in range(3))
    ob.parent = grupo
    return ob


# --------------------------------------------------------- la esfera ------
# Meridianos: el mismo aro girado sobre Z. Paralelos: aros más chicos, subidos.
R = 2.9
MER = 10
for i in range(MER):
    anillo(R, 2, math.pi * i / MER, 0.010, i, build=(F(0.3 + i*0.06), F(1.4 + i*0.06)))

PAR = 7
for j in range(1, PAR):
    lat = math.pi * j / PAR - math.pi/2
    r = R * math.cos(lat)
    ob = anillo(r, 0, math.pi/2, 0.010, 20 + j, build=(F(1.0 + j*0.08), F(2.1 + j*0.08)))
    ob.location = (0, 0, R * math.sin(lat))

# ------------------------------------------------------------ el núcleo ----
# Emisión muy por encima de 1: el bloom sólo sangra donde el píxel se satura, así
# que un blanco "normal" brilla igual que las líneas y no se lee como fuente.
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.30, location=(0, 0, 0))
nucleo = bpy.context.object
nucleo.name = "nucleo"
m = bpy.data.materials.new("nm")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission")
e.inputs["Color"].default_value = (1, 1, 1, 1)
e.inputs["Strength"].default_value = 14.0
o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(e.outputs[0], o.inputs["Surface"])
nucleo.data.materials.append(m)
nucleo.parent = grupo

# late despacio: la figura respira en vez de sólo girar
for t in [x*0.5 for x in range(int(FIN*2) + 1)]:
    s = 1.0 + 0.14*math.sin(t*1.6)
    nucleo.scale = (s, s, s)
    nucleo.keyframe_insert("scale", frame=F(t))
for fc in lib._fc(nucleo):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ------------------------------------------------------------- el giro -----
# Lento y en dos ejes a la vez: un giro sobre un solo eje se lee como un GIF.
for f, rot in ((1, (0.10, 0.0, -0.35)), (F(FIN), (-0.06, 0.0, 0.55))):
    grupo.rotation_euler = rot
    grupo.keyframe_insert("rotation_euler", frame=f)
for fc in lib._fc(grupo):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# ---------------------------------------------------------- subtítulos -----
# Abajo, pequeños, uno a la vez. La figura no lleva etiquetas: el texto va por
# fuera y la imagen se queda limpia.
LINEAS = [(2.6, "el modelo es el punto del centro"),
          (5.0, "todo lo demás lo construyes tú"),
          (7.4, "eso es el harness")]
for i, (t, txt) in enumerate(LINEAS):
    g = texto(txt, 0, -5.6, 0.30, (0.86, 0.86, 0.90),
              build=(F(t), F(t + 0.5)),
              out=F(LINEAS[i + 1][0] - 0.15) if i + 1 < len(LINEAS) else F(FIN))

# ---------------------------------------------------------------- cámara ---
cam = S.camera
cam.location = (0, -13.0, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

bloom(fuerza=1.6, umbral=0.02, tam=0.9, suavidad=0.5)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(1.2), F(3.0), F(6.0), F(9.0)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_koe", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_koe", "f_")
    bpy.ops.render.render(animation=True)
