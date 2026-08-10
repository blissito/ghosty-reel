"""
d2 animado — "el loop del agente".

Tres ideas de motion graphics, ninguna a costa de la legibilidad:

1. **El dibujo se dibuja solo.** Cada trazo entra en su beat, en el orden en que
   se explica. El espectador ve construirse el argumento, no un cuadro terminado.
2. **2.5D.** El diagrama sigue siendo plano, pero sus elementos viven a
   profundidades distintas. Un movimiento mínimo de cámara da paralaje real —el
   título flota sobre las cajas— sin tocar la lectura.
3. **Un pulso recorre el ciclo.** Un punto viaja por las flechas: es lo que
   convierte tres cajas en un loop.

    blender -b -P anim_d2.py           # secuencia -> out_d2/
    STILL=1 blender -b -P anim_d2.py   # stills en los beats
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import (trazo, rrect, circulo, linea, flecha, texto, caja, dibujar,
                 boil, flujo, bloom,
                 INK, GRIS, ROJO, AMBAR, VERDE, CIAN, MORA)

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
S.render.fps = FPS

# ------------------------------------------------------------------ beats --
T_TIT, T_NODOS, T_FLECHAS, T_PULSO, T_PIE = 0.2, 1.0, 2.6, 4.0, 6.2
FIN = 9.0
S.frame_start, S.frame_end = 1, F(FIN)

# --------------------------------------------------------------- el dibujo -
# prof < 0 = más cerca de la cámara. El título flota al frente; las cajas al
# fondo. Con la cámara quieta no se nota; en cuanto se mueve, aparece el volumen.
texto("el loop del agente", 0, 6.35, 0.60, INK, build=(F(T_TIT), F(T_TIT + 0.8)), prof=-1.5)
texto("una llamada no es un agente; el ciclo sí", 0, 5.55, 0.30, GRIS,
      build=(F(T_TIT + 0.5), F(T_TIT + 1.2)), prof=-1.1)

R = 3.05
NODOS = [("piensa", 90, AMBAR), ("actúa", 210, VERDE), ("observa", 330, CIAN)]
P = {}
for i, (nom, ang, col) in enumerate(NODOS):
    a = math.radians(ang)
    x, z = R*math.cos(a), R*math.sin(a) + 0.45
    P[nom] = (x, z)
    t0 = T_NODOS + i*0.5
    cj, _ = caja(x, z, 2.75, 1.30, nom, col, 0.33, 30 + i,
                 build=(F(t0), F(t0 + 0.55)), prof=1.3)
    boil(cj, step=3, factor=0.55)

ORDEN = ["piensa", "actúa", "observa", "piensa"]
TRAMOS = []
for i in range(3):
    (x1, z1), (x2, z2) = P[ORDEN[i]], P[ORDEN[i + 1]]
    dx, dz = x2 - x1, z2 - z1
    L = math.hypot(dx, dz)
    ux, uz = dx/L, dz/L
    a = (x1 + ux*1.62, z1 + uz*1.62)
    b = (x2 - ux*1.62, z2 - uz*1.62)
    TRAMOS.append((a, b))
    t0 = T_FLECHAS + i*0.35
    flecha(*a, *b, GRIS, 0.018, 40 + i, build=(F(t0), F(t0 + 0.3)), prof=1.3)

texto("hasta", 0, 0.72, 0.30, GRIS, build=(F(T_PULSO), F(T_PULSO + 0.4)), prof=1.3)
texto("resolver", 0, 0.15, 0.30, GRIS, build=(F(T_PULSO + 0.2), F(T_PULSO + 0.6)), prof=1.3)

for i, (t, col) in enumerate(((T_PIE, INK), (T_PIE + 0.7, GRIS), (T_PIE + 1.6, AMBAR))):
    linea_txt = ["El modelo no ejecuta: pide.",
                 "El harness ejecuta y le devuelve el resultado.",
                 "Ese ida y vuelta es todo el truco."][i]
    texto(linea_txt, 0, -4.15 - i*0.72 - (0.35 if i == 2 else 0), 0.30, col,
          build=(F(t), F(t + 0.6)), prof=-0.9)

# ------------------------------------------------------------- la pelota ---
# Recorre el ciclo. Es lo que convierte tres cajas en un loop: sin ella, las
# flechas son decoración. Con bloom encima, además brilla al pasar.
pelota = circulo(0, 0, 0.15, AMBAR, 0.038, 99, prof=1.28)
VUELTA = 2.1
inicio = T_PULSO + 0.3
t = inicio
while t < FIN:
    for j, ((ax, az), (bx, bz)) in enumerate(TRAMOS):
        t0 = t + j*(VUELTA/3)
        for u in (0.0, 1.0):
            pelota.location = ((ax + (bx-ax)*u) * 1.08, 1.28, (az + (bz-az)*u) * 1.08)
            pelota.keyframe_insert("location", frame=F(t0 + u*(VUELTA/3)))
    t += VUELTA
for f, v in ((1, True), (F(inicio) - 1, False)):
    pelota.hide_render = v
    pelota.keyframe_insert("hide_render", frame=f)
for fc in lib._fc(pelota):
    modo = 'CONSTANT' if fc.data_path == "hide_render" else 'LINEAR'
    for kp in fc.keyframe_points:
        kp.interpolation = modo

bloom(fuerza=0.75, umbral=0.03, tam=0.85)

# ---------------------------------------------------------------- cámara ---
cam = S.camera
# Trasladar la cámara con planos que miran de frente sólo produce deslizamiento:
# nada se escorza y se lee como capas resbalando. Orbitando, en cambio, los
# rectángulos se ven en ángulo y aparece la perspectiva — más sensación de 3D
# con MENOS movimiento en pantalla.
piv = bpy.data.objects.new("piv", None)
S.collection.objects.link(piv)
piv.location = (0, 0.4, 0.6)          # centro del diagrama, no del mundo
cam.parent = piv
cam.location = (0, -16.0, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

for f, (yaw, pitch) in ((1, (-0.058, 0.026)), (F(FIN), (0.058, -0.014))):
    piv.rotation_euler = (pitch, 0, yaw)
    piv.keyframe_insert("rotation_euler", frame=f)
for fc in piv.animation_data.action.layers[0].strips[0].channelbag(
        piv.animation_data.action_slot).fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# Con la órbita, la separación en profundidad puede ser MAYOR sin que nada se
# salga del cuadro: el escorzo hace el trabajo que antes hacía el desplazamiento.

# ---------------------------------------------------------------- salida ---
S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(1.8), F(3.4), F(5.0), F(8.0)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_d2", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_d2", "f_")
    bpy.ops.render.render(animation=True)
