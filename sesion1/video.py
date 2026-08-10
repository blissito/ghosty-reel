"""
Video de la sesión 01 — una sola toma, sin cortes.

Los beats salen de `scene.json`, que a su vez sale de las duraciones REALES de
la voz. Ningún tiempo está escrito a mano dos veces: cambiar el guion es
regenerar la voz, correr el derivador de beats y volver a renderizar.

La figura central es el grafo que la comunidad ya conoce —el modelo y las tools
como dos nodos, con una condicional en medio— porque explicar sobre algo que ya
viste es más barato que enseñar una metáfora nueva.

    blender -b -P video.py            # secuencia -> out_video/
    STILL=1 blender -b -P video.py    # un still por beat
"""
import bpy, math, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import texto, trazo, bloom, solo_entre, AMBAR

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))
FPS = 30
def F(t): return max(1, int(round(t * FPS)))

lib.limpiar()
lib.escena()
lib.CAM_D = 12.5                      # k_prof tiene que conocer la distancia real
S.render.fps = FPS
S.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

SC = json.load(open(os.path.join(D, "scene.json")))
B = SC["beats"]
FIN = B["end"]
S.frame_start, S.frame_end = 1, F(FIN)

GEO = bpy.data.collections.new("GEO")
S.collection.children.link(GEO)
giro = bpy.data.objects.new("giro", None)
S.collection.objects.link(giro)


# ------------------------------------------------------------- utilidades --
def invisible():
    """La malla existe para que Line Art la recorra, pero no se pinta."""
    m = bpy.data.materials.new("inv")
    m.use_nodes = True
    m.surface_render_method = 'BLENDED'
    nt = m.node_tree
    nt.nodes.clear()
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(t.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
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
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    return m


def suave(ob, datos=("location", "scale", "rotation_euler")):
    for fc in lib._fc(ob):
        if fc.data_path in datos:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_IN_OUT'


def marco(w, h, loc, rot=(0, 0, 0), fondo=0.16):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.scale = (w/2, fondo/2, h/2)
    # location=False y rotation=False EXPLÍCITOS: los defaults del operador son
    # True y 'aplicar la escala' hornearía también la posición, dejando el
    # origen en (0,0,0) — los hijos aterrizarían en el centro.
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.rotation_euler = rot
    ob.data.materials.append(invisible())
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    GEO.objects.link(ob)
    ob.parent = giro
    return ob


def tubo(a, b, radio=0.030):
    dx, dy, dz = (b[k] - a[k] for k in range(3))
    L = math.sqrt(dx*dx + dy*dy + dz*dz)
    bpy.ops.mesh.primitive_cylinder_add(radius=radio, depth=L, vertices=8,
                                        location=tuple((a[k] + b[k])/2 for k in range(3)))
    ob = bpy.context.object
    ob.rotation_euler = (0, math.acos(dz/L), math.atan2(dy, dx))
    ob.data.materials.append(invisible())
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    GEO.objects.link(ob)
    ob.parent = giro
    return ob


def aparece(ob, t0, dur=0.45, eje=None):
    """Crece hasta su tamaño. `eje` limita el crecimiento — un cable se alarga,
    no se infla. NO se dibuja trazo a trazo: a media animación un rectángulo
    incompleto se lee como error."""
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


def destello(loc, t0, radio=0.55, fuerza=26.0, dur=0.28):
    """Chispazo al materializarse. Con bloom, es el efecto más barato del estilo."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radio, location=loc)
    d = bpy.context.object
    d.data.materials.append(emisivo(fuerza))
    d.parent = giro
    for t, e in ((t0, 0.05), (t0 + dur*0.35, 1.0), (t0 + dur, 0.02)):
        d.scale = (e, e, e)
        d.keyframe_insert("scale", frame=F(t))
    solo_entre(d, F(t0) - 1, F(t0 + dur) + 1)
    suave(d)
    return d


def rotulo(cuerpo, padre, tam=0.30, dz=0.0):
    """El texto vive DENTRO del marco: sin él, la caja deja de ser un elemento."""
    tx = texto(cuerpo, 0, 0, tam, (1, 1, 1), peso="black")
    tx.parent = padre
    tx.location = (0, -0.16, dz)      # delante de la cara, para no z-fightear
    return tx


# ------------------------------------------------- 1. el modelo, y ya está --
# Arranca con el núcleo solo: la creencia que el guion va a desarmar.
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.40, location=(0, 0, 2.1))
nuc = bpy.context.object
nuc.data.materials.append(emisivo(13.0))
nuc.parent = giro
# Late mientras está solo, y CEDE SU LUGAR cuando aparece el marco: comparten
# posición, y con la emisión alta el núcleo borraba la palabra "modelo".
for t in [x*0.5 for x in range(int(B["dos_piezas"]*2) + 1)]:
    e = 1.0 + 0.12*math.sin(t*1.7)
    nuc.scale = (e, e, e)
    nuc.keyframe_insert("scale", frame=F(t))
nuc.scale = (1.0, 1.0, 1.0)
nuc.keyframe_insert("scale", frame=F(B["dos_piezas"] + 0.1))
nuc.scale = (0.18, 0.18, 0.18)
nuc.keyframe_insert("scale", frame=F(B["dos_piezas"] + 0.8))
suave(nuc)
solo_entre(nuc, 1, F(B["dos_piezas"] + 1.0))   # fuera: comparte sitio con el rótulo

# ------------------------------------------- 2. dos piezas: modelo y tools --
M_POS, T_POS = (0, 0, 2.1), (0, 0, -2.6)
m_modelo = marco(2.9, 1.35, M_POS, (0, 0.10, 0))
aparece(m_modelo, B["dos_piezas"], 0.5)
# El marco del modelo nace EN el núcleo y se queda: el punto se abre en marco.
destello(M_POS, B["dos_piezas"] - 0.05, 0.55)
rotulo("modelo", m_modelo, 0.30)

m_tools = marco(2.9, 1.35, T_POS, (0, -0.12, 0))
aparece(m_tools, B["dos_piezas"] + 0.9, 0.5)
# ...y el de tools SALE DISPARADO del mismo punto hacia abajo. No aparece en su
# sitio: viaja hasta él, así la transición dice "de aquí sale aquello".
for t, z in ((B["dos_piezas"] + 0.85, M_POS[2]), (B["dos_piezas"] + 1.5, T_POS[2])):
    m_tools.location = (0, 0, z)
    m_tools.keyframe_insert("location", frame=F(t))
for fc in lib._fc(m_tools):
    if fc.data_path == "location":
        for kp in fc.keyframe_points:
            kp.interpolation = 'BACK'
            kp.easing = 'EASE_OUT'
destello(T_POS, B["dos_piezas"] + 0.85, 0.55)
rotulo("tools", m_tools, 0.30)

# Los cables entran HASTA el centro de los marcos. Si terminan antes, la bola
# sube por encima del final del cable, cruza en el aire y baja: ese tramo fuera
# de las guías se lee como una M.
IDA = ((-0.95, 0, M_POS[2]), (-0.95, 0, T_POS[2]))
VUELTA_T = ((0.95, 0, T_POS[2]), (0.95, 0, M_POS[2]))
aparece(tubo(*IDA), B["dos_piezas"] + 1.7, 0.4, eje=2)
aparece(tubo(*VUELTA_T), B["dos_piezas"] + 2.0, 0.4, eje=2)

# ------------------------------------------------------ 3. la condicional --
# Un rombo en el camino de ida: el punto donde se decide si el ciclo sigue.
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.62, depth=0.16,
                                location=(-0.95, 0, 0.15), rotation=(math.pi/2, 0, 0))
cond = bpy.context.object
cond.data.materials.append(invisible())
for c in list(cond.users_collection):
    c.objects.unlink(cond)
GEO.objects.link(cond)
cond.parent = giro
aparece(cond, B["condicional"] + 0.4, 0.45)
destello((-0.95, 0, 0.15), B["condicional"] + 0.35, 0.55)

texto("¿pidió una tool?", -0.95, -0.62, 0.19, (0.95, 0.95, 1.0),
      build=(F(B["condicional"] + 0.9), F(B["condicional"] + 1.4)),
      out=F(B["historial"] - 0.3), prof=-1.3)

# ------------------------------------------------------------ 4. el pulso --
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.155, location=IDA[0])
pulso = bpy.context.object
pulso.data.materials.append(emisivo(14.0))
pulso.parent = giro

# La ruta pasa por el CENTRO de los marcos y baja/sube por donde están los
# cables. Antes iba de punta a punta de los tubos y cruzaba en diagonal por
# donde no hay nada dibujado.
# El circuito CIERRA en el mismo punto donde abre. Antes arrancaba en la
# posición de flotación —que sólo valía para la primera vuelta— y en cada
# costura la bola rebotaba hacia atrás y se desfasaba.
RUTA = [M_POS, (IDA[0][0], 0, M_POS[2]), (IDA[1][0], 0, T_POS[2]), T_POS,
        (VUELTA_T[0][0], 0, T_POS[2]), (VUELTA_T[1][0], 0, M_POS[2]), M_POS]
LARGOS = [math.dist(RUTA[i], RUTA[i+1]) for i in range(len(RUTA)-1)]
TOTAL = sum(LARGOS)

# El golpe del guion: en "Pide" la bola SALE y se queda suspendida durante la
# pausa. El silencio hace el trabajo; moverla lo arruinaría.
# Sale del modelo y se queda flotando durante la pausa. Congelada se veía
# "atorada"; un cabeceo mínimo la mantiene viva sin distraer.
pulso.location = M_POS
pulso.keyframe_insert("location", frame=F(B["pide"]))
t = B["pide"] + 0.55
while t < B["condicional"] + 1.4:
    # Centrada bajo el marco, no colgada del cable izquierdo: sale del modelo,
    # así que ese es su sitio natural — y la composición queda simétrica.
    pulso.location = (0, 0, 0.95 + 0.09*math.sin((t - B["pide"])*2.2))
    pulso.keyframe_insert("location", frame=F(t))
    t += 0.25

# del punto donde flotaba, sube a la salida del modelo y ya empieza a girar
pulso.location = (0, 0, 0.95)
pulso.keyframe_insert("location", frame=F(B["condicional"] + 1.4))
pulso.location = M_POS
pulso.keyframe_insert("location", frame=F(B["condicional"] + 1.6))

VUELTA = 3.0
t = B["condicional"] + 1.6
while t < FIN - 2.0:
    acum = 0.0
    for i in range(len(RUTA) - 1):
        a, b = RUTA[i], RUTA[i+1]
        for u in (0.0, 1.0):
            pulso.location = tuple(a[k] + (b[k]-a[k])*u for k in range(3))
            # tiempo repartido por LONGITUD: si no, los tramos cortos se
            # recorren igual de lento que los largos y el ritmo se rompe
            pulso.keyframe_insert("location",
                                  frame=F(t + (acum + LARGOS[i]*u)/TOTAL*VUELTA))
        acum += LARGOS[i]
    t += VUELTA
solo_entre(pulso, F(B["pide"]) - 1, S.frame_end)
for fc in lib._fc(pulso):
    modo = 'CONSTANT' if fc.data_path == "hide_render" else 'LINEAR'
    for kp in fc.keyframe_points:
        kp.interpolation = modo

texto("nombre de la tool + argumentos", 0, 0.18, 0.20, AMBAR,
      build=(F(B["argumentos"] + 0.3), F(B["argumentos"] + 0.9)),
      out=F(B["condicional"] + 0.2), prof=-1.3)

# Se retira antes de que los anillos empiecen a acumularse: si no, lo tapan.
texto("el resultado", 2.05, -0.15, 0.19, (0.86, 0.86, 0.92),
      build=(F(B["condicional"] + 5.2), F(B["condicional"] + 5.7)),
      out=F(B["historial"] + 0.3), prof=-1.2)
texto("regresa al modelo", 2.05, -0.62, 0.19, (0.86, 0.86, 0.92),
      build=(F(B["condicional"] + 5.5), F(B["condicional"] + 6.0)),
      out=F(B["historial"] + 0.3), prof=-1.2)

# ---------------------------------------------------------- 5. el historial
# Cada vuelta deja una barra: el contexto que crece es lo que hace que la
# siguiente decisión sea mejor que la anterior.
texto("historial", 2.75, 1.35, 0.22, (0.8, 0.8, 0.86),
      build=(F(B["historial"] + 0.4), F(B["historial"] + 0.9)),
      out=F(B["cta"] - 0.4), prof=-1.0)
for i in range(6):
    t0 = B["historial"] + 0.9 + i*0.85
    if t0 > B["cta"] - 0.8:
        break
    ba = trazo([(2.25, 0.92 - i*0.34), (3.25, 0.92 - i*0.34)], (0.92, 0.92, 0.96),
               0.022, 60 + i, ruido=0.0, build=(F(t0), F(t0 + 0.25)), prof=-1.0)
    solo_entre(ba, F(t0) - 1, F(B["cta"] - 0.4))

# ------------------------------------------- 7b. los anillos de cada vuelta --
# Cada vuelta completa deja un anillo que se va hacia el fondo. Al alejarse la
# cámara en "ciclo", los anillos acumulados forman un túnel: la figura dice que
# el ciclo se repitió muchas veces, sin contarlas.
ANILLOS = 14
for i in range(ANILLOS):
    t0 = B["historial"] + 0.6 + i*0.42
    if t0 > B["cta"] + 0.4:
        break
    n = 72
    r = 2.05 + 0.055*i          # el radio crece un pelín: da moiré al apilarse
    pts = [(r*math.cos(2*math.pi*k/n), r*math.sin(2*math.pi*k/n)) for k in range(n + 1)]
    an = trazo(pts, (0.62, 0.62, 0.68), 0.009, seed=80 + i, ruido=0.0)
    # SIN rotación: trazo() ya dibuja en el plano que mira a la cámara. Rotarlo
    # sobre X los pone de canto (una línea cruzando el diagrama) y sobre Z los
    # saca de su plano (una esfera de meridianos). El túnel son círculos
    # paralelos apilados en profundidad, y ya.
    an.parent = giro
    # nace en el plano del grafo y se aleja: la profundidad la crea el tiempo
    # Nacen DETRÁS del grafo, nunca delante: si arrancan en y negativo tapan las
    # etiquetas de los marcos.
    for t, (y, e) in ((t0, (0.55, 0.35)), (t0 + 0.5, (1.1, 1.0)),
                      (t0 + 5.0, (8.0, 1.0))):
        an.location = (0, y, -0.2)
        an.scale = (e, e, e)
        an.keyframe_insert("location", frame=F(t))
        an.keyframe_insert("scale", frame=F(t))
    solo_entre(an, F(t0) - 1, F(B["cta"] + 1.0))
    suave(an)

# --------------------------------------------------------------- 6. cierre -
for i, (dt, txt, tam, col) in enumerate((
        (0.0, "Sistemas Agénticos", 0.60, (1, 1, 1)),
        (0.7, "primera sesión: tus primeras tools", 0.26, (0.82, 0.82, 0.88)),
        (1.4, "1 de septiembre", 0.34, AMBAR))):
    texto(txt, 0, 2.45 - i*1.12, tam, col,
          build=(F(B["cta"] + 2.3 + dt), F(B["cta"] + 2.9 + dt)), prof=-1.6)
texto("fixtergeek.com/sistemas-agenticos", 0, -1.05, 0.26, (0.72, 0.72, 0.80),
      build=(F(B["cta"] + 4.4), F(B["cta"] + 5.0)), prof=-1.6)

# logo de marca, abajo del todo
im = bpy.data.images.load("/Users/bliss/blender-motion/harness-reel/assets/logo.png")
ar = im.size[1] / im.size[0]
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, -1.6, -2.55))
logo = bpy.context.object
logo.scale = (2.9, 2.9 * ar, 1)
logo.rotation_euler = (math.pi/2, 0, 0)
lm = bpy.data.materials.new("logo_m")
lm.use_nodes = True
lm.surface_render_method = 'BLENDED'
lnt = lm.node_tree
lnt.nodes.clear()
tex = lnt.nodes.new("ShaderNodeTexImage"); tex.image = im; tex.interpolation = 'Cubic'
emi = lnt.nodes.new("ShaderNodeEmission"); emi.inputs["Strength"].default_value = 0.72   # el bloom lo quemaba
tra = lnt.nodes.new("ShaderNodeBsdfTransparent")
mixs = lnt.nodes.new("ShaderNodeMixShader")
sal = lnt.nodes.new("ShaderNodeOutputMaterial")
lnt.links.new(tex.outputs["Color"], emi.inputs["Color"])
lnt.links.new(tex.outputs["Alpha"], mixs.inputs[0])
lnt.links.new(tra.outputs[0], mixs.inputs[1])
lnt.links.new(emi.outputs[0], mixs.inputs[2])
lnt.links.new(mixs.outputs[0], sal.inputs["Surface"])
logo.data.materials.append(lm)
solo_entre(logo, F(B["cta"] + 4.9), S.frame_end)
for t, e in ((B["cta"] + 4.9, 0.85), (B["cta"] + 5.4, 1.0)):
    logo.scale = (2.9*e, 2.9*ar*e, 1)
    logo.keyframe_insert("scale", frame=F(t))
suave(logo)

# ------------------------------------------------------------- 7. Line Art -
gp = bpy.data.grease_pencils.new("la")
gp.stroke_depth_order = '3D'
la_ob = bpy.data.objects.new("la", gp)
S.collection.objects.link(la_ob)
lmat = bpy.data.materials.new("lm")
bpy.data.materials.create_gpencil_data(lmat)
lmat.grease_pencil.color = (1, 1, 1, 1)
gp.materials.append(lmat)
lay = gp.layers.new("L")
lay.use_lights = False
lay.radius_offset = 0.115
la = la_ob.modifiers.new("lineart", 'LINEART')
la.source_type = 'COLLECTION'
la.source_collection = GEO
la.target_layer = lay.name
la.target_material = lmat
la.use_contour = la.use_crease = la.use_intersection = True
# Sólo líneas visibles: con las ocultas, la arista trasera del marco cruza la
# palabra que contiene.
la.use_multiple_levels = True
la.level_start, la.level_end = 0, 0
nz = la_ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
nz.factor, nz.noise_scale, nz.factor_thickness = 0.10, 0.5, 0.15
nz.use_random = bool(os.environ.get("BOIL"))   # el boil vibra: estorba aquí
nz.step = 6

# ---------------------------------------------------------------- cámara ---
piv = bpy.data.objects.new("piv", None)
S.collection.objects.link(piv)
piv.location = (0, 0, -0.2)
cam = S.camera
cam.parent = piv
cam.rotation_euler = (math.pi/2, 0, 0)

# El único movimiento con intención: en "ciclo" la cámara se aleja y el bucle
# entero cabe en el cuadro. Antes y después, deriva mínima.
# El recorrido de cámara ES una transición más: se mete en la condicional para
# mirarla de cerca, y sale de ahí abriéndose hasta que el bucle entero cabe.
for t, (yaw, pitch, d, px, pz) in (
        (0.0,                  (-0.07,  0.03, 11.0,  0.0,  1.4)),
        (B["condicional"],     ( 0.04, -0.01, 12.0,  0.0,  0.2)),
        (B["condicional"]+3.2, ( 0.10, -0.03,  6.2, -0.95, -0.35)),   # dentro
        (B["historial"],       ( 0.02,  0.0,  12.4,  0.0,  0.0)),
        (B["ciclo"] + 1.2,     ( 0.0,   0.0,  16.5,  0.0, -0.2)),
        (B["cta"] + 1.6,       ( 0.0,   0.0,  12.0,  0.0,  0.0)),
        (FIN,                  ( 0.0,   0.0,  11.6,  0.0,  0.0))):
    piv.rotation_euler = (pitch, 0, yaw)
    piv.location = (px, 0, pz)
    cam.location = (0, -d, 0)
    piv.keyframe_insert("location", frame=F(t))
    piv.keyframe_insert("rotation_euler", frame=F(t))
    cam.keyframe_insert("location", frame=F(t))
suave(piv)
suave(cam)

# ------------------------------------------------- 8. colapso al cierre ----
# El diagrama no se apaga: COLAPSA. Todo el grafo converge a un punto, el punto
# revienta, y del destello sale el cierre. Una transición es una oportunidad de
# cambio espectacular; dejar que algo se desvanezca la desperdicia.
T_COL = B["cta"] + 0.9
giro.scale = (1, 1, 1)
giro.keyframe_insert("scale", frame=F(T_COL))
giro.scale = (1.06, 1.06, 1.06)          # respira antes de caer
giro.keyframe_insert("scale", frame=F(T_COL + 0.35))
giro.scale = (0.004, 0.004, 0.004)
giro.keyframe_insert("scale", frame=F(T_COL + 1.05))
for fc in lib._fc(giro):
    if fc.data_path == "scale":
        for kp in fc.keyframe_points:
            kp.interpolation = 'BACK'
            kp.easing = 'EASE_IN'

# el reventón: nace donde murió el grafo
destello((0, 0, -0.2), T_COL + 1.02, 1.9, fuerza=34.0, dur=0.55)

solo_entre(la_ob, 1, F(T_COL + 1.12))
solo_entre(giro, 1, F(T_COL + 1.12))

bloom(fuerza=2.1, umbral=0.02, tam=0.88, suavidad=0.5)

S.render.image_settings.file_format = 'PNG'
if os.environ.get("STILL"):
    for k in ("texto", "dos_piezas", "pide", "condicional", "historial", "ciclo", "cta"):
        f = F(B[k] + 1.6)
        S.frame_set(f)
        S.render.filepath = os.path.join(D, "out_video", f"p_{k}")
        bpy.ops.render.render(write_still=True)
else:
    S.render.filepath = os.path.join(D, "out_video", "f_")
    bpy.ops.render.render(animation=True)
