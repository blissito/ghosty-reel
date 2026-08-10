"""
Escena mixta: estructura monocroma en 3D + anotación a mano en color.

Es la segunda escena del guion, hecha con la técnica que funcionó: geometría 3D
de verdad, contorno generado por Line Art, blanco sobre negro y bloom fuerte.

Decisiones que trae la técnica consigo:
  · Las cajas son volúmenes, así que la cámara puede rodear y se ve que hay
    profundidad — no es un triángulo dibujado, es un circuito en el espacio.
  · El pulso que recorre el ciclo es una esfera emisiva: al pasar, el bloom la
    hace sangrar luz. Es el elemento más vistoso y encima es el que EXPLICA.
  · Las etiquetas van planas y de frente. Si se parentan al grupo que gira,
    quedan ilegibles a los dos segundos.

    blender -b -P escena_loop.py            # secuencia -> out_loop/
    STILL=1 blender -b -P escena_loop.py    # stills en los beats
"""
import bpy, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import texto, trazo, circulo, bloom, solo_entre, boil, AMBAR, VERDE, CIAN

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
lib.CAM_D = 12.5      # esta escena acerca la cámara; k_prof tiene que saberlo
S.render.fps = FPS
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

T_CAJAS, T_LINEAS, T_PULSO, T_CIERRE = 0.4, 2.4, 3.6, 8.0
FIN = 12.0
S.frame_start, S.frame_end = 1, F(FIN)

GEO = bpy.data.collections.new("GEO")
S.collection.children.link(GEO)
giro = bpy.data.objects.new("giro", None)
S.collection.objects.link(giro)


def invisible():
    """La malla existe para que Line Art la recorra, pero no se pinta. Con
    material negro las caras taparían todo lo que hay detrás."""
    m = bpy.data.materials.new("inv")
    m.use_nodes = True
    m.surface_render_method = 'BLENDED'
    nt = m.node_tree
    nt.nodes.clear()
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(t.outputs[0], o.inputs["Surface"])
    return m


def emisivo(fuerza=16.0):
    """Muy por encima de 1: el bloom sólo sangra donde el píxel se satura."""
    m = bpy.data.materials.new("emi")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1, 1, 1, 1)
    e.inputs["Strength"].default_value = fuerza
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def caja(w, h, d, loc, rot=(0, 0, 0)):
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


def tubo(a, b, radio=0.035):
    """Conexión con volumen. Un cilindro se lee como cable en el espacio; una
    línea plana, no."""
    (x1, y1, z1), (x2, y2, z2) = a, b
    dx, dy, dz = x2-x1, y2-y1, z2-z1
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    bpy.ops.mesh.primitive_cylinder_add(radius=radio, depth=L, vertices=8,
                                        location=((x1+x2)/2, (y1+y2)/2, (z1+z2)/2))
    ob = bpy.context.object
    # Dirección esférica: girar sobre Y lleva el eje Z del cilindro a la
    # inclinación, y sobre Z lo orienta en el plano. Con un +pi/2 extra el tubo
    # horizontal apuntaba fuera de cámara y se veía como una esquirla.
    ob.rotation_euler = (0, math.acos(dz/L), math.atan2(dy, dx))
    ob.data.materials.append(invisible())
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    GEO.objects.link(ob)
    ob.parent = giro
    return ob


def lineart(grosor=0.028):
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
    # sin esto, la caja de delante borra todo lo que queda detrás
    la.use_multiple_levels = True
    la.level_start, la.level_end = 0, 3
    nz = ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
    # Ruido ESTÁTICO. Con use_random el temblor se re-aleatoriza cada pocos
    # frames (el "line boil" de la animación tradicional): en un trazo a mano
    # queda vivo, pero en un dibujo técnico se lee como vibración y cansa.
    # BOIL=1 lo enciende si alguna escena lo pide.
    nz.factor, nz.noise_scale, nz.factor_thickness = 0.10, 0.5, 0.15
    nz.use_random = bool(os.environ.get("BOIL"))
    nz.step = 6
    # el circuito se dibuja solo, en el orden en que se explica
    bd = ob.modifiers.new("build", 'GREASE_PENCIL_BUILD')
    bd.use_percentage = True
    for f, v in ((1, 0.0), (F(T_CAJAS), 0.0), (F(T_LINEAS + 1.4), 1.0)):
        bd.percentage_factor = v
        bd.keyframe_insert("percentage_factor", frame=f)
    return ob


# ------------------------------------------------------------ el circuito ---
R = 2.9
NODOS = {}
for nom, ang, rot in (("piensa", 90, (0.0, 0.0, 0.35)),
                      ("actúa", 210, (0.25, 0.0, -0.2)),
                      ("observa", 330, (-0.2, 0.0, 0.15))):
    a = math.radians(ang)
    p = (R*math.cos(a), 0.0, R*math.sin(a))
    NODOS[nom] = p
    caja(1.9, 1.5, 1.9, p, rot)

ORDEN = ["piensa", "actúa", "observa", "piensa"]
TRAMOS = []
for i in range(3):
    a, b = NODOS[ORDEN[i]], NODOS[ORDEN[i + 1]]
    dx, dz = b[0]-a[0], b[2]-a[2]
    L = math.hypot(dx, dz)
    ux, uz = dx/L, dz/L
    p1 = (a[0] + ux*1.15, 0.0, a[2] + uz*1.15)
    p2 = (b[0] - ux*1.15, 0.0, b[2] - uz*1.15)
    TRAMOS.append((p1, p2))
    tubo(p1, p2)

lineart(0.028)

# --------------------------------------------------------------- el pulso ---
# Recorre el circuito. Es lo más vistoso de la escena y a la vez lo que explica:
# sin él, tres cajas conectadas no son un ciclo.
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0))
pulso = bpy.context.object
pulso.data.materials.append(emisivo(18.0))
pulso.parent = giro

VUELTA = 2.4
t = T_PULSO
while t < FIN:
    for j, (p1, p2) in enumerate(TRAMOS):
        t0 = t + j*(VUELTA/3)
        for u in (0.0, 1.0):
            pulso.location = tuple(p1[k] + (p2[k]-p1[k])*u for k in range(3))
            pulso.keyframe_insert("location", frame=F(t0 + u*(VUELTA/3)))
    t += VUELTA
solo_entre(pulso, F(T_PULSO) - 1, S.frame_end)
for fc in lib._fc(pulso):
    modo = 'CONSTANT' if fc.data_path == "hide_render" else 'LINEAR'
    for kp in fc.keyframe_points:
        kp.interpolation = modo

# ------------------------------------------------------------ las etiquetas -
# Planas y de frente. Parentadas al grupo que gira quedarían ilegibles enseguida.
for i, (nom, dx, dz) in enumerate((("piensa", 0.0, 1.62), ("actúa", 0.0, -1.62),
                                   ("observa", 0.0, -1.62))):
    p = NODOS[nom]
    t0 = T_CAJAS + 0.3 + i*0.45
    texto(nom, p[0] + dx, p[2] + dz, 0.30, (0.95, 0.95, 1.0), build=(F(t0), F(t0 + 0.4)))

# ------------------------------------------------------------- subtítulos ---
LINEAS = [(0.6, "el modelo no ejecuta: pide"),
          (3.6, "el harness ejecuta y le devuelve el resultado"),
          (6.6, "y vuelve a empezar"),
          (T_CIERRE + 1.4, "ese ida y vuelta es el agente")]
for i, (t, txt) in enumerate(LINEAS):
    fin = F(LINEAS[i + 1][0] - 0.2) if i + 1 < len(LINEAS) else F(FIN)
    texto(txt, 0, -5.35, 0.28, (0.88, 0.88, 0.92), build=(F(t), F(t + 0.5)), out=fin)

# ------------------------------------------------------------------ giro ----
# Muy contenido: lo justo para que se lea el volumen sin desalinear las
# etiquetas, que no giran con él.
for f, rot in ((1, (0.13, 0.0, -0.16)), (F(FIN), (0.02, 0.0, 0.16))):
    giro.rotation_euler = rot
    giro.keyframe_insert("rotation_euler", frame=f)
for fc in lib._fc(giro):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
        kp.easing = 'EASE_IN_OUT'

# ------------------------------------------------- la anotación en color ---
# La estructura es blanca y 3D; el color entra sólo para MARCAR, a mano, encima.
# Es la diferencia entre el plano técnico y lo que alguien escribe sobre él.
COLOR = {"piensa": AMBAR, "actúa": VERDE, "observa": CIAN}
for i, nom in enumerate(("piensa", "actúa", "observa")):
    p = NODOS[nom]
    t0 = T_CIERRE - 2.4 + i*0.55
    # el círculo va delante de la estructura (prof negativo) para que se lea
    # como anotación sobre el dibujo, no como parte de él
    an = circulo(p[0], p[2], 1.18, COLOR[nom], 0.032, 70 + i,
                 build=(F(t0), F(t0 + 0.45)), prof=-1.6)
    boil(an, step=3, factor=0.7)

texto("tres pasos, un solo ciclo", 0, -3.55, 0.30, AMBAR,
      build=(F(T_CIERRE + 0.2), F(T_CIERRE + 0.8)), prof=-1.6)

cam = S.camera
cam.location = (0, -12.5, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

bloom(fuerza=1.4, umbral=0.02, tam=0.85, suavidad=0.5)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(1.6), F(3.2), F(5.2), F(9.6)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_mix", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_mix", "f_")
    bpy.ops.render.render(animation=True)
