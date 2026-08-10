"""
Escena real del video: "el loop del agente", en estilo monocromo luminoso.

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
from lib import texto, trazo, bloom, solo_entre

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
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


def aparece(ob, t0, dur=0.45, eje=None):
    """El objeto crece hasta su tamaño. `eje` limita el crecimiento a una
    dirección — un tubo debe alargarse, no inflarse."""
    base = tuple(ob.scale)
    cero = tuple(0.001 if (eje is None or k == eje) else base[k] for k in range(3))
    for t, e in ((t0 - 1/FPS, cero), (t0, cero), (t0 + dur, base)):
        ob.scale = e
        ob.keyframe_insert("scale", frame=F(t))
    for fc in lib._fc(ob):
        if fc.data_path == "scale":
            for kp in fc.keyframe_points:
                kp.interpolation = 'BACK'
                kp.easing = 'EASE_OUT'
    return ob


def destello(loc, t0, radio=0.5, fuerza=26.0, dur=0.30):
    """Chispazo en el instante de aparecer. Con el bloom encendido, un punto de
    emisión muy alta durante unos frames se lee como si el elemento se
    materializara — es el efecto más barato del estilo y el que más vende."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radio, location=loc)
    d = bpy.context.object
    d.data.materials.append(emisivo(fuerza))
    d.parent = giro
    for t, e in ((t0, 0.05), (t0 + dur*0.35, 1.0), (t0 + dur, 0.02)):
        d.scale = (e, e, e)
        d.keyframe_insert("scale", frame=F(t))
    solo_entre(d, F(t0) - 1, F(t0 + dur) + 1)
    for fc in lib._fc(d):
        if fc.data_path == "scale":
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_OUT'
    return d


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
    # Sólo líneas visibles. Con las ocultas activadas, la arista trasera del
    # marco cruza por encima de la palabra y la parte — en un marco de texto eso
    # ensucia. (Las ocultas sí sirven cuando la figura ES la estructura.)
    la.use_multiple_levels = True
    la.level_start, la.level_end = 0, 0
    nz = ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
    # Ruido ESTÁTICO. Con use_random el temblor se re-aleatoriza cada pocos
    # frames (el "line boil" de la animación tradicional): en un trazo a mano
    # queda vivo, pero en un dibujo técnico se lee como vibración y cansa.
    # BOIL=1 lo enciende si alguna escena lo pide.
    nz.factor, nz.noise_scale, nz.factor_thickness = 0.10, 0.5, 0.15
    nz.use_random = bool(os.environ.get("BOIL"))
    nz.step = 6
    # SIN Build sobre el Line Art: dibuja todo el circuito como un trazo
    # continuo, así que a media animación queda medio rectángulo — y eso se lee
    # como error, no como "dibujándose". Lo que se anima es la GEOMETRÍA: la caja
    # crece y Line Art la sigue.
    return ob


# ------------------------------------------------------------ el circuito ---
# Disposición ELÍPTICA, no circular: el ancho lo limita el cuadro (tres marcos
# en fila no caben más), pero en vertical sobra sitio. Estirar en Z hace que la
# figura ocupe la mitad del encuadre en vez de un tercio.
RX, RZ = 2.35, 3.70
NODOS, CAJAS = {}, {}
# Giros suaves: el marco tiene que seguir leyéndose como marco. Muy inclinado,
# el texto de dentro se escorza y deja de leerse.
for nom, ang, rot in (("piensa", 90, (0.0, 0.10, 0.0)),
                      ("actúa", 210, (0.06, -0.13, 0.0)),
                      ("observa", 330, (-0.05, 0.14, 0.0))):
    a = math.radians(ang)
    p = (RX*math.cos(a), 0.0, RZ*math.sin(a) + 0.35)
    NODOS[nom] = p
    t0 = T_CAJAS + len(NODOS)*0.4 - 0.4
    CAJAS[nom] = aparece(caja(2.40, 1.18, 0.16, p, rot), t0, 0.5)
    destello(p, t0 - 0.06, 0.62)

ORDEN = ["piensa", "actúa", "observa", "piensa"]
TRAMOS = []
for i in range(3):
    a, b = NODOS[ORDEN[i]], NODOS[ORDEN[i + 1]]
    dx, dz = b[0]-a[0], b[2]-a[2]
    L = math.hypot(dx, dz)
    ux, uz = dx/L, dz/L
    p1 = (a[0] + ux*1.35, 0.0, a[2] + uz*1.35)
    p2 = (b[0] - ux*1.35, 0.0, b[2] - uz*1.35)
    TRAMOS.append((p1, p2))
    aparece(tubo(p1, p2), T_LINEAS + i*0.3, 0.35, eje=2)  # se alarga, no se infla

lineart(0.115)

# --------------------------------------------------------------- el pulso ---
# Recorre el circuito. Es lo más vistoso de la escena y a la vez lo que explica:
# sin él, tres cajas conectadas no son un ciclo.
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0))
pulso = bpy.context.object
pulso.data.materials.append(emisivo(18.0))
pulso.parent = giro

VUELTA = 2.4
# La bola recorre los NODOS, no los extremos recortados de los tubos: así entra
# de verdad en cada marco en vez de saltar de una punta a la otra en las
# esquinas. Se reparte el tiempo por longitud de tramo, o los lados cortos se
# recorren igual de lento que los largos y el movimiento se siente arrítmico.
RUTA = [NODOS[n] for n in ORDEN]                       # cierra en el primero
LARGOS = [math.dist(RUTA[i], RUTA[i + 1]) for i in range(3)]
TOTAL = sum(LARGOS)

t = T_PULSO
while t < FIN:
    acum = 0.0
    for i in range(3):
        a, b = RUTA[i], RUTA[i + 1]
        for u in (0.0, 1.0):
            pulso.location = tuple(a[k] + (b[k] - a[k])*u for k in range(3))
            pulso.keyframe_insert(
                "location", frame=F(t + (acum + LARGOS[i]*u) / TOTAL * VUELTA))
        acum += LARGOS[i]
    t += VUELTA
solo_entre(pulso, F(T_PULSO) - 1, S.frame_end)
for fc in lib._fc(pulso):
    modo = 'CONSTANT' if fc.data_path == "hide_render" else 'LINEAR'
    for kp in fc.keyframe_points:
        kp.interpolation = modo

# ------------------------------------------------------------ las etiquetas -
# DENTRO del marco, sobre su cara frontal. La caja es el marco del texto: sin el
# texto adentro deja de ser un elemento y se vuelve un adorno geométrico.
for i, nom in enumerate(("piensa", "actúa", "observa")):
    t0 = T_CAJAS + 0.3 + i*0.45
    tx = texto(nom, 0, 0, 0.27, (1.0, 1.0, 1.0), build=(F(t0), F(t0 + 0.4)), peso="black")
    tx.parent = CAJAS[nom]
    # SIN matrix_parent_inverse: cancela la transformación del padre y las tres
    # etiquetas terminaban apiladas en el centro del mundo.
    tx.location = (0, -0.18, 0)      # justo delante de la cara, para no z-fightear

# ------------------------------------------------------------- subtítulos ---
LINEAS = [(0.6, "el modelo no ejecuta: pide"),
          (3.6, "el harness ejecuta y le devuelve el resultado"),
          (6.6, "y vuelve a empezar"),
          (T_CIERRE + 1.4, "ese ida y vuelta es el agente")]
for i, (t, txt) in enumerate(LINEAS):
    fin = F(LINEAS[i + 1][0] - 0.2) if i + 1 < len(LINEAS) else F(FIN)
    texto(txt, 0, -4.75, 0.30, (0.93, 0.93, 0.96), build=(F(t), F(t + 0.5)), out=fin, peso="bold")

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

cam = S.camera
cam.location = (0, -12.5, 0)
cam.rotation_euler = (math.pi/2, 0, 0)

bloom(fuerza=2.3, umbral=0.02, tam=0.85, suavidad=0.5)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for f in (F(1.6), F(3.2), F(5.2), F(9.6)):
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_loop", f"p_{f:04d}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_loop", "f_")
    bpy.ops.render.render(animation=True)
