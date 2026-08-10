"""
Transición 3D → 2D: el mismo objeto, dos lecturas.

Un montón de anillos apilados a lo largo de un eje. Visto de lado es un túnel
con profundidad; visto de frente son círculos concéntricos y el 3D desaparece.
La cámara rota 90° y hace el viaje entre las dos lecturas sin un solo corte.

El moiré —esas franjas que aparecen entre anillos— no se dibuja: sale solo de
tener muchos anillos casi paralelos. Es interferencia, y es lo que le da la
textura densa.

    blender -b -P anim_tunel.py            # secuencia -> out_tunel/
    STILL=1 blender -b -P anim_tunel.py    # stills en los tres momentos
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import trazo, texto, bloom

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
S.render.fps = FPS
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

FIN = 9.0
S.frame_start, S.frame_end = 1, F(FIN)

grupo = bpy.data.objects.new("grupo", None)
S.collection.objects.link(grupo)

# ------------------------------------------------------------- los anillos --
# Radio con forma de lente: crece hacia el centro del túnel y se cierra en los
# extremos. Un cilindro recto se leería como tubo; la lente tiene silueta.
N = 76
LARGO, R = 11.0, 3.5
for i in range(N):
    u = i / (N - 1)
    y = -LARGO/2 + LARGO*u
    r = R * math.sin(math.pi * u) ** 0.7 + 0.12
    n = 120
    pts = [(r*math.cos(2*math.pi*k/n), r*math.sin(2*math.pi*k/n)) for k in range(n + 1)]
    # el grosor baja hacia los extremos: sin eso el túnel se ve como una reja
    # Trazo MUY fino: la referencia vive del negro entre anillos. Con línea
    # gruesa y bloom fuerte todo se funde en una mancha blanca.
    ob = trazo(pts, (0.85, 0.85, 0.90), 0.0028 + 0.0022*math.sin(math.pi*u),
               seed=i, ruido=0.0)
    ob.location = (0, y, 0)
    # cada anillo girado un pelín respecto al anterior: eso es lo que genera el
    # moiré cuando se miran de canto
    ob.rotation_euler = (0, math.radians(i * 2.4), 0)
    ob.parent = grupo

# -------------------------------------------------------------- el núcleo ---
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.34, location=(0, 0, 0))
nuc = bpy.context.object
m = bpy.data.materials.new("nm")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
e = nt.nodes.new("ShaderNodeEmission")
e.inputs["Color"].default_value = (1, 1, 1, 1)
e.inputs["Strength"].default_value = 9.0
o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(e.outputs[0], o.inputs["Surface"])
nuc.data.materials.append(m)
nuc.parent = grupo

# ---------------------------------------------------------------- cámara ---
# El viaje: empieza mirando el túnel desde un costado (profundidad pura) y acaba
# de frente al eje (círculos concéntricos, 2D puro). Es la misma figura.
piv = bpy.data.objects.new("piv", None)
S.collection.objects.link(piv)
cam = S.camera
cam.parent = piv
cam.location = (0, -15.0, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

for f, (yaw, pitch, dist) in ((1, (1.32, 0.22, 18.5)),
                              (F(FIN*0.55), (0.62, 0.10, 16.5)),
                              (F(FIN), (0.0, 0.0, 17.5))):
    piv.rotation_euler = (pitch, 0, yaw)
    cam.location = (0, -dist, 0)
    piv.keyframe_insert("rotation_euler", frame=f)
    cam.keyframe_insert("location", frame=f)
for ob in (piv, cam):
    for fc in lib._fc(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'

# el conjunto gira despacio sobre su eje: mantiene vivo el moiré
for f, rz in ((1, 0.0), (F(FIN), 0.55)):
    grupo.rotation_euler = (0, rz, 0)
    grupo.keyframe_insert("rotation_euler", frame=f)
for fc in lib._fc(grupo):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# ---------------------------------------------------------- subtítulos -----
for i, (t, txt) in enumerate([(0.8, "el agente vive en un ciclo"),
                              (4.2, "y cada vuelta lo acerca"),
                              (7.0, "hasta resolver")]):
    fin = F([(0.8,), (4.2,), (7.0,)][i + 1][0] - 0.2) if i < 2 else F(FIN)
    texto(txt, 0, -6.6, 0.30, (0.92, 0.92, 0.96),
          build=(F(t), F(t + 0.5)), out=fin, peso="bold")

bloom(fuerza=0.75, umbral=0.15, tam=0.95, suavidad=0.4)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(0.5), F(4.5), F(8.6)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_tunel", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_tunel", "f_")
    bpy.ops.render.render(animation=True)
