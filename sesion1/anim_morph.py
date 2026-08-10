"""
Experimento: el diagrama se REORGANIZA para convertirse en el siguiente.

En vez de cortar —o de volar la cámara de un diagrama a otro, que se agota a la
tercera vez— las mismas cajas se recolocan. El triángulo del loop se estira en la
fila de ReAct: son los mismos tres pasos, sólo que ahora contados como patrón.

La ventaja sobre el recorrido de cámara es que cada transición es distinta,
porque cada reorganización lo es. Y dice algo: que los conceptos son el mismo
material visto de otra manera.

    blender -b -P anim_morph.py            # secuencia -> out_morph/
    STILL=1 blender -b -P anim_morph.py    # stills en los beats
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import (trazo, rrect, circulo, linea, flecha, texto, dibujar, boil,
                 bloom, INK, GRIS, AMBAR, VERDE, CIAN, CAM_D)

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
S.render.fps = FPS

T_ENTRA, T_MORPH, T_FIN = 0.3, 3.2, 7.5
S.frame_start, S.frame_end = 1, F(T_FIN)
PROF = 1.2
K = (CAM_D + PROF) / CAM_D


def caja_movil(w, h, etiqueta, color, seed, build):
    """Caja centrada en el origen: mover el OBJETO la mueve entera, texto
    incluido. Con los puntos horneados en coordenadas absolutas —como en los
    diagramas estáticos— no habría forma de animarla."""
    cj = rrect(0, 0, w, h, 0.26, color, 0.022, seed, build=build, prof=PROF)
    tx = texto(etiqueta, 0, 0, 0.33, color, build=(build[1] - 4, build[1] + 6), prof=PROF)
    tx.parent = cj
    tx.matrix_parent_inverse = cj.matrix_world.inverted()
    boil(cj, step=3, factor=0.55)
    return cj


def mover(ob, tramos):
    """tramos = [(segundo, x, z, escala)] en coordenadas aparentes. La escala
    importa: tres cajas del ancho del triángulo no caben en fila, así que al
    alinearse encogen — y de paso el gesto se lee como 'esto es un resumen'."""
    for t, x, z, e in tramos:
        ob.location = (x * K, PROF, z * K)
        ob.scale = (K * e, K * e, K * e)
        ob.keyframe_insert("location", frame=F(t))
        ob.keyframe_insert("scale", frame=F(t))
    for fc in lib._fc(ob):
        if fc.data_path in ("location", "scale"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_IN_OUT'


# ---------------------------------------------------- los dos encuadres ----
R, CZ = 3.05, 0.45
TRIANGULO = {"piensa": (0.0, R + CZ),
             "actúa": (R*math.cos(math.radians(210)), R*math.sin(math.radians(210)) + CZ),
             "observa": (R*math.cos(math.radians(330)), R*math.sin(math.radians(330)) + CZ)}
FILA = {"piensa": (-2.72, 1.1), "actúa": (0.0, 1.1), "observa": (2.72, 1.1)}

CAJAS = {}
for i, (nom, col) in enumerate((("piensa", AMBAR), ("actúa", VERDE), ("observa", CIAN))):
    t0 = T_ENTRA + i*0.45
    cj = caja_movil(2.75, 1.30, nom, col, 30 + i, (F(t0), F(t0 + 0.5)))
    # se quedan quietas hasta el morph, y entonces se recolocan escalonadas
    mover(cj, [(1/FPS, *TRIANGULO[nom], 1.0),
               (T_MORPH + i*0.12, *TRIANGULO[nom], 1.0),
               (T_MORPH + 1.1 + i*0.12, *FILA[nom], 0.76)])
    CAJAS[nom] = cj

# --------------------------------------------------------- los rótulos ----
# El título cambia porque cambió la lectura: los mismos tres pasos, ahora
# presentados como uno de los patrones.
texto("el loop del agente", 0, 6.35, 0.60, INK,
      build=(F(T_ENTRA), F(T_ENTRA + 0.7)), out=F(T_MORPH + 0.5), prof=-1.4)
texto("piensa · actúa · observa", 0, 5.55, 0.30, GRIS,
      build=(F(T_ENTRA + 0.4), F(T_ENTRA + 1.0)), out=F(T_MORPH + 0.5), prof=-1.1)

texto("ReAct", 0, 6.35, 0.60, AMBAR,
      build=(F(T_MORPH + 1.0), F(T_MORPH + 1.6)), prof=-1.4)
texto("el mismo ciclo, contado como patrón", 0, 5.55, 0.30, GRIS,
      build=(F(T_MORPH + 1.4), F(T_MORPH + 2.0)), prof=-1.1)

# ------------------------------------------------------------ conexiones ---
# Las del triángulo se retiran justo cuando arranca la reorganización; las de la
# fila entran cuando las cajas ya llegaron.
ORD = ["piensa", "actúa", "observa", "piensa"]
for i in range(3):
    (x1, z1), (x2, z2) = TRIANGULO[ORD[i]], TRIANGULO[ORD[i + 1]]
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz)
    ux, uz = dx/L, dz/L
    t0 = T_ENTRA + 1.7 + i*0.3
    fl = flecha(x1 + ux*1.62, z1 + uz*1.62, x2 - ux*1.62, z2 - uz*1.62,
                GRIS, 0.018, 40 + i, build=(F(t0), F(t0 + 0.3)), prof=PROF)
    lib.solo_entre(fl, F(t0) - 1, F(T_MORPH + 0.1))

for i in range(2):
    x = -1.36 + i*2.72
    t0 = T_MORPH + 1.5 + i*0.2
    fl = flecha(x - 0.42, 1.1, x + 0.42, 1.1, GRIS, 0.018, 50 + i,
                build=(F(t0), F(t0 + 0.2)), prof=PROF, punta=0.13)
    lib.solo_entre(fl, F(t0) - 1, S.frame_end)

# el ciclo de vuelta, que es lo que distingue a ReAct de una fila de pasos
t0 = T_MORPH + 2.0
vuelta = trazo([(2.72, 0.15), (2.72, -0.62), (-2.72, -0.62), (-2.72, 0.15)],
               GRIS, 0.016, 60, build=(F(t0), F(t0 + 0.5)), prof=PROF)
lib.solo_entre(vuelta, F(t0) - 1, S.frame_end)
texto("y vuelve a empezar", 0, -1.15, 0.28, GRIS,
      build=(F(t0 + 0.5), F(t0 + 1.1)), prof=PROF)

# ---------------------------------------------------------------- cámara ---
piv = bpy.data.objects.new("piv", None)
S.collection.objects.link(piv)
piv.location = (0, 0.4, 0.9)
cam = S.camera
cam.parent = piv
cam.location = (0, -16.0, 0)
cam.rotation_euler = (math.pi/2, 0, 0)
for f, (yaw, pitch) in ((1, (-0.05, 0.022)), (F(T_FIN), (0.05, -0.012))):
    piv.rotation_euler = (pitch, 0, yaw)
    piv.keyframe_insert("rotation_euler", frame=f)
for fc in lib._fc(piv):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

bloom(fuerza=0.75, umbral=0.03, tam=0.85)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(2.4), F(3.6), F(4.4), F(6.5)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_morph", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_morph", "f_")
    bpy.ops.render.render(animation=True)
