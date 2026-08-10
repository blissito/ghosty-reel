"""
Seis diagramas trazados a mano (Grease Pencil) para explicar la sesión 01 del
Taller Sistemas Agénticos: "El harness: anatomía de un agente".

    blender -b -P diagramas.py            # los seis -> out/d1..d6.png
    D=3 blender -b -P diagramas.py        # sólo el tercero

Son bocetos para elegir, no piezas finales: la idea es ver cuál explica mejor
antes de invertir en animarlo.
"""
import bpy, math, os

S = bpy.context.scene
D = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ setup ---
W, H = 1080, 1920
CAM_D, PLANE_W = 16.0, 9.0          # -> x en [-4.5, 4.5], z en [-8, 8]

INK   = (0.96, 0.96, 0.99)
GRIS  = (0.55, 0.56, 0.64)
ROJO  = (1.00, 0.42, 0.52)
AMBAR = (1.00, 0.80, 0.28)
VERDE = (0.40, 0.95, 0.65)
CIAN  = (0.35, 0.80, 1.00)
MORA  = (0.65, 0.45, 1.00)


def limpiar():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in (bpy.data.grease_pencils, bpy.data.materials, bpy.data.curves):
        for b in list(c):
            c.remove(b)


def escena():
    S.render.resolution_x, S.render.resolution_y = W, H
    S.render.engine = 'BLENDER_EEVEE'
    S.eevee.taa_render_samples = 16
    S.eevee.use_shadows = False
    S.eevee.use_fast_gi = False
    S.view_settings.view_transform = 'Standard'   # AgX apagaría la paleta
    S.view_settings.look = 'None'
    S.world = bpy.data.worlds.new("W")
    S.world.use_nodes = True
    S.world.node_tree.nodes["Background"].inputs[0].default_value = (0.043, 0.043, 0.055, 1)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    S.collection.objects.link(cam)
    S.camera = cam
    cam.location = (0, -CAM_D, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.sensor_fit = 'HORIZONTAL'            # en 9:16 el angle iría a la ALTURA
    cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)


# ------------------------------------------------------------ primitivas ---
def trazo(pts, color=INK, grosor=0.022, seed=0, ruido=0.6):
    """Un trazo de Grease Pencil. pts en (x, z); el dibujo vive en y=0."""
    gp = bpy.data.grease_pencils.new("t")
    gp.stroke_depth_order = '3D'
    ob = bpy.data.objects.new("t", gp)
    S.collection.objects.link(ob)
    mat = bpy.data.materials.new("m")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color = (*color, 1.0)
    mat.grease_pencil.fill_color = (*color, 1.0)
    gp.materials.append(mat)
    lay = gp.layers.new("L")
    lay.use_lights = False
    d = lay.frames.new(1).drawing
    d.add_strokes([len(pts)])
    st = d.strokes[0]
    st.cyclic = False                 # cerrar a mano; ver rrect()
    for i, (x, z) in enumerate(pts):
        st.points[i].position = (x, 0.0, z)
        st.points[i].radius = grosor
        st.points[i].opacity = 1.0
    nz = ob.modifiers.new("n", 'GREASE_PENCIL_NOISE')
    nz.factor, nz.noise_scale, nz.factor_thickness = ruido, 0.35, 0.5
    nz.seed = seed
    return ob


def rrect(cx, cz, w, h, r=0.28, color=INK, grosor=0.022, seed=0):
    pts = []
    for ox, oz, a0 in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, math.pi/2),
                       (-w/2+r, -h/2+r, math.pi), (w/2-r, -h/2+r, 3*math.pi/2)):
        for i in range(9):
            a = a0 + (math.pi / 2) * i / 8
            pts.append((cx + ox + r*math.cos(a), cz + oz + r*math.sin(a)))
    return trazo(pts + [pts[0]], color, grosor, seed)


def circulo(cx, cz, r, color=INK, grosor=0.022, seed=0, desde=0.0, hasta=2*math.pi):
    n = max(8, int(28 * (hasta - desde) / (2*math.pi)))
    pts = [(cx + r*math.cos(desde + (hasta-desde)*i/n),
            cz + r*math.sin(desde + (hasta-desde)*i/n)) for i in range(n + 1)]
    return trazo(pts, color, grosor, seed)


def linea(x1, z1, x2, z2, color=GRIS, grosor=0.018, seed=0):
    return trazo([(x1, z1), (x2, z2)], color, grosor, seed)


def flecha(x1, z1, x2, z2, color=GRIS, grosor=0.018, seed=0, punta=0.16):
    linea(x1, z1, x2, z2, color, grosor, seed)
    a = math.atan2(z2 - z1, x2 - x1)
    for s in (+1, -1):
        b = a + math.pi + s * 0.42
        trazo([(x2, z2), (x2 + punta*math.cos(b), z2 + punta*math.sin(b))],
              color, grosor, seed)


def texto(cuerpo, x, z, tam=0.30, color=INK, align='CENTER'):
    cu = bpy.data.curves.new("c", 'FONT')
    cu.body, cu.size = cuerpo, tam
    cu.align_x, cu.align_y = align, 'CENTER'
    ob = bpy.data.objects.new("x", cu)
    S.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = (x, 0, z)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='GREASEPENCIL')
    g = bpy.context.view_layer.objects.active
    g.data.stroke_depth_order = '3D'
    for l in g.data.layers:
        l.use_lights = False
    for m in g.data.materials:
        if m and m.grease_pencil:
            m.grease_pencil.color = (*color, 1.0)
            m.grease_pencil.fill_color = (*color, 1.0)   # el texto es RELLENO
    return g


def titulo(t, sub=None):
    texto(t, 0, 6.95, 0.52, INK)
    if sub:
        texto(sub, 0, 6.15, 0.26, GRIS)


def caja(cx, cz, w, h, etiqueta, color, tam=0.26, seed=0, r=0.26):
    rrect(cx, cz, w, h, r, color, 0.022, seed)
    texto(etiqueta, cx, cz, tam, color)


# --------------------------------------------------------------- 1 --------
def d1():
    """Agente = modelo + harness. El modelo es la pieza pequeña."""
    titulo("¿qué es un agente?", "modelo + todo lo que construyes alrededor")
    rrect(0, -0.5, 8.2, 11.0, 0.5, MORA, 0.024, 1)
    texto("harness", 0, 4.55, 0.30, MORA)
    caja(0, -0.5, 2.5, 1.5, "modelo", ROJO, 0.32, 2)
    piezas = [("system prompt", -1.95, 2.9, AMBAR), ("tools", 1.95, 2.9, AMBAR),
              ("skills", -1.95, -3.3, VERDE), ("MCP", 1.95, -3.3, CIAN),
              ("subagentes", 0, -4.9, MORA)]
    for i, (nom, x, z, col) in enumerate(piezas):
        caja(x, z, 3.3, 1.15, nom, col, 0.25, 10 + i)
        # conector recortado en ambos extremos, para que no entre en las cajas
        dx, dz = x - 0, z - (-0.5)
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        linea(ux*0.95, -0.5 + uz*0.95, x - ux*0.75, z - uz*0.75, GRIS, 0.014, 20 + i)
    texto("~500,000 líneas en Claude Code.", 0, -6.6, 0.25, GRIS)
    texto("ninguna es el modelo.", 0, -7.1, 0.25, ROJO)


# --------------------------------------------------------------- 2 --------
def d2():
    """El loop. Lo que separa a un agente de una llamada suelta."""
    titulo("el loop del agente", "una llamada no es un agente; el ciclo sí")
    R = 3.0
    nodos = [("piensa", 90, AMBAR), ("actúa", 210, VERDE), ("observa", 330, CIAN)]
    P = {}
    for i, (nom, ang, col) in enumerate(nodos):
        a = math.radians(ang)
        x, z = R * math.cos(a), R * math.sin(a) - 0.2
        P[nom] = (x, z)
        caja(x, z, 2.5, 1.15, nom, col, 0.27, 30 + i)
    orden = ["piensa", "actúa", "observa", "piensa"]
    for i in range(3):
        (x1, z1), (x2, z2) = P[orden[i]], P[orden[i + 1]]
        dx, dz = x2 - x1, z2 - z1
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        flecha(x1 + ux*1.5, z1 + uz*1.5, x2 - ux*1.5, z2 - uz*1.5, GRIS, 0.018, 40 + i)
    texto("hasta", 0, -0.05, 0.26, GRIS)
    texto("resolver", 0, -0.55, 0.26, GRIS)
    texto("El modelo no ejecuta: pide.", 0, -5.3, 0.26, INK)
    texto("El harness ejecuta y le devuelve el resultado.", 0, -5.9, 0.26, GRIS)
    texto("Ese ida y vuelta es todo el truco.", 0, -6.7, 0.26, AMBAR)


# --------------------------------------------------------------- 3 --------
def d3():
    """Tres patrones. Cuándo basta uno solo."""
    titulo("tres patrones", "y cuándo basta con el más simple")
    cols = [
        ("ReAct", 3.5, AMBAR, ["piensa", "actúa", "observa"], "improvisa paso a paso"),
        ("Plan-and-Execute", -0.7, VERDE, ["planea todo", "paso 1", "paso 2"], "decide antes de empezar"),
        ("Reflection", -4.9, CIAN, ["produce", "se critica", "corrige"], "se revisa a sí mismo"),
    ]
    for i, (nom, z0, col, pasos, pie) in enumerate(cols):
        texto(nom, 0, z0 + 1.45, 0.34, col)
        for j, p in enumerate(pasos):
            x = -2.6 + j * 2.6
            caja(x, z0 + 0.45, 2.15, 0.85, p, col, 0.21, 50 + i*5 + j, r=0.2)
            if j < 2:
                flecha(x + 1.15, z0 + 0.45, x + 1.42, z0 + 0.45, GRIS, 0.015, 60 + i*5 + j, 0.11)
        if nom != "Plan-and-Execute":       # los que vuelven al principio
            trazo([(2.6, z0 - 0.15), (2.6, z0 - 0.75), (-2.6, z0 - 0.75), (-2.6, z0 - 0.15)],
                  GRIS, 0.015, 70 + i)
            flecha(-2.6, z0 - 0.45, -2.6, z0 - 0.18, GRIS, 0.015, 75 + i, 0.11)
        texto(pie, 0, z0 - 1.15, 0.22, GRIS)
    texto("La mayoría de los problemas se resuelven", 0, -6.9, 0.25, GRIS)
    texto("con un solo agente en ReAct.", 0, -7.45, 0.25, AMBAR)


# --------------------------------------------------------------- 4 --------
def d4():
    """Hooks: dónde te metes tú."""
    titulo("middleware y hooks", "interceptar al modelo antes y después")
    z = 1.6
    caja(0, z + 2.4, 4.6, 1.2, "tu app", INK, 0.28, 80)
    flecha(0, z + 1.75, 0, z + 1.1, GRIS, 0.018, 81)
    caja(0, z + 0.45, 5.6, 1.1, "hook: antes", AMBAR, 0.26, 82)
    texto("valida · reescribe · bloquea", 0, z - 0.55, 0.21, GRIS)
    flecha(0, z - 0.95, 0, z - 1.55, GRIS, 0.018, 83)
    caja(0, z - 2.35, 3.4, 1.5, "modelo", ROJO, 0.30, 84)
    flecha(0, z - 3.25, 0, z - 3.85, GRIS, 0.018, 85)
    caja(0, z - 4.5, 5.6, 1.1, "hook: después", CIAN, 0.26, 86)
    texto("registra · filtra · reintenta", 0, z - 5.5, 0.21, GRIS)
    flecha(0, z - 5.9, 0, z - 6.5, GRIS, 0.018, 87)
    caja(0, z - 7.2, 4.6, 1.2, "respuesta", INK, 0.28, 88)
    texto("El modelo es una caja que no controlas.", -0.0, -7.35, 0.24, GRIS)


# --------------------------------------------------------------- 5 --------
def d5():
    """La curva. Por qué se mueve cada mes."""
    titulo("confiabilidad vs. agencia", "el intercambio que define tu diseño")
    x0, z0, xw, zh = -3.5, -4.2, 7.4, 8.9

    def curva(t):
        return z0 + zh * (0.97 - 0.92 * t**1.8)

    linea(x0, z0, x0, z0 + zh + 0.3, GRIS, 0.018, 90)
    linea(x0, z0, x0 + xw + 0.3, z0, GRIS, 0.018, 91)
    texto("+ confiable", x0 + 1.15, z0 + zh + 0.62, 0.23, GRIS)
    texto("+ agencia", x0 + xw - 0.6, z0 - 0.55, 0.23, GRIS)

    trazo([(x0 + xw*t/26, curva(t/26)) for t in range(27)], AMBAR, 0.028, 92, ruido=0.4)

    # Las etiquetas van en el hueco que deja la curva: arriba-derecha en el tramo
    # alto, abajo-izquierda en el bajo. Encima de la línea no se leen.
    marcas = [(0.05, "script", VERDE, 1.75, 0.42),
              (0.42, "agente con tools", CIAN, 1.15, 0.85),
              (0.82, "agente autónomo", MORA, -1.30, -0.95)]
    for i, (t, nom, col, dx, dz) in enumerate(marcas):
        x, z = x0 + xw*t, curva(t)
        circulo(x, z, 0.13, col, 0.02, 93 + i)
        texto(nom, x + dx, z + dz, 0.24, col)
        linea(x + dx*0.22, z + dz*0.30, x + dx*0.72, z + dz*0.72, col, 0.012, 97 + i)

    # Una sola flecha para el movimiento. Una segunda curva completa convergía en
    # los extremos y se leía como un ojo, no como un desplazamiento.
    mx, mz = x0 + xw*0.55, curva(0.55)
    flecha(mx + 0.35, mz + 0.35, mx + 1.5, mz + 1.5, MORA, 0.022, 99, 0.2)
    for j, ln in enumerate(("cada mes", "se mueve", "hacia acá")):
        texto(ln, mx + 2.45, mz + 1.95 - j*0.44, 0.24, MORA)

    texto("Diseñas para la curva de hoy,", 0, -6.1, 0.27, INK)
    texto("sabiendo que la de mañana es otra.", 0, -6.75, 0.27, GRIS)


def d6():
    """Qué entra realmente en cada llamada."""
    titulo("qué entra en una llamada", "el contexto es el estado del agente")
    capas = [("system prompt", AMBAR, "quién es y qué no debe hacer"),
             ("schema de tools", VERDE, "qué puede pedir, y cómo"),
             ("historial", CIAN, "lo que ya pasó en la sesión"),
             ("mensaje", MORA, "lo que le acabas de pedir")]
    z = 4.6
    for i, (nom, col, pie) in enumerate(capas):
        caja(-0.2, z, 6.4, 1.0, nom, col, 0.26, 100 + i, r=0.22)
        texto(pie, -0.2, z - 0.72, 0.19, GRIS)
        z -= 1.75
    rrect(-0.2, 1.85, 7.2, 7.3, 0.4, GRIS, 0.016, 110)
    texto("ventana de contexto", -0.2, 5.62, 0.22, GRIS)
    flecha(-0.2, -2.35, -0.2, -3.0, GRIS, 0.018, 111)
    caja(-0.2, -3.75, 3.2, 1.2, "modelo", ROJO, 0.30, 112)
    flecha(-0.2, -4.5, -0.2, -5.1, GRIS, 0.018, 113)
    caja(-0.2, -5.75, 4.4, 1.1, "pide una tool", VERDE, 0.26, 114)
    # el resultado entra al HISTORIAL, no al schema: el schema no cambia
    trazo([(2.1, -5.75), (3.6, -5.75), (3.6, 1.1)], VERDE, 0.016, 115)
    flecha(3.6, 1.1, 3.15, 1.1, VERDE, 0.016, 116, 0.12)
    texto("el resultado vuelve al contexto", 0, -7.3, 0.24, VERDE)


# ------------------------------------------------------------------ main ---
DIAGRAMAS = [d1, d2, d3, d4, d5, d6]
solo = os.environ.get("D")
S.render.image_settings.file_format = 'PNG'
for i, fn in enumerate(DIAGRAMAS, 1):
    if solo and int(solo) != i:
        continue
    limpiar()
    escena()
    fn()
    S.render.filepath = os.path.join(D, "out", f"d{i}")
    bpy.ops.render.render(write_still=True)
    print(f"  d{i}  {fn.__doc__.splitlines()[0]}")
