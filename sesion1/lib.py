"""Primitivas de dibujo a mano (Grease Pencil) compartidas por los diagramas.

Todo vive en el plano y=0 y se mide en unidades de mundo: con PLANE_W=9 y
formato 9:16, x va de -4.5 a 4.5 y z de -8 a 8.
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
    # Casi negro (~#121212), no gris medio ni negro puro: el negro absoluto da un
    # contraste demasiado duro con el trazo claro y cansa la vista; el gris medio
    # le roba fuerza al dibujo. Un pelo de azul lo aleja del gris muerto.
    S.world.node_tree.nodes["Background"].inputs[0].default_value = (0.0060, 0.0060, 0.0078, 1)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    S.collection.objects.link(cam)
    S.camera = cam
    cam.location = (0, -CAM_D, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.sensor_fit = 'HORIZONTAL'            # en 9:16 el angle iría a la ALTURA
    cam.data.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)


# ------------------------------------------------------------ primitivas ---
def trazo(pts, color=INK, grosor=0.022, seed=0, ruido=0.6, build=None, prof=0.0):
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
    if build:
        dibujar(ob, *build)
    k = k_prof(prof)
    ob.scale = (k, k, k)          # escala respecto al origen: posición Y grosor
    ob.location = (0, prof, 0)
    lay.opacity = atmosfera(prof)
    return ob


def atmosfera(prof):
    """Perspectiva atmosférica: lo lejano pierde contraste. Es lo que más vende
    la profundidad en 2.5D — más que el paralaje, que por sí solo se lee como
    capas deslizándose."""
    return max(0.55, 1.0 - max(0.0, prof) * 0.16)


def k_prof(prof):
    """Factor que devuelve a su tamaño APARENTE algo que se movió en profundidad.
    Sin esto, separar las capas para dar paralaje también cambia el encuadre:
    lo cercano se magnifica, lo lejano encoge, y la composición deja de caber.

    OJO: usa el CAM_D del módulo. Si tu escena mueve la cámara a otra distancia,
    asigna `lib.CAM_D = <la tuya>` ANTES de crear los objetos, o la compensación
    sale con el factor equivocado y los elementos con `prof` se desbordan."""
    return (CAM_D + prof) / CAM_D


def dibujar(ob, a, b):
    """El trazo se dibuja del frame a al b. percentage_factor, no frame_start:
    así el dibujo se ata al beat del guion y no a un rango fijo."""
    bd = ob.modifiers.new("build", 'GREASE_PENCIL_BUILD')
    bd.use_percentage = True
    for f, v in ((max(1, a - 1), 0.0), (a, 0.0), (b, 1.0)):
        bd.percentage_factor = v
        bd.keyframe_insert("percentage_factor", frame=f)
    return bd


def rrect(cx, cz, w, h, r=0.28, color=INK, grosor=0.022, seed=0, build=None, prof=0.0):
    pts = []
    for ox, oz, a0 in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, math.pi/2),
                       (-w/2+r, -h/2+r, math.pi), (w/2-r, -h/2+r, 3*math.pi/2)):
        for i in range(9):
            a = a0 + (math.pi / 2) * i / 8
            pts.append((cx + ox + r*math.cos(a), cz + oz + r*math.sin(a)))
    return trazo(pts + [pts[0]], color, grosor, seed, build=build, prof=prof)


def circulo(cx, cz, r, color=INK, grosor=0.022, seed=0, desde=0.0, hasta=2*math.pi, build=None, prof=0.0):
    n = max(8, int(28 * (hasta - desde) / (2*math.pi)))
    pts = [(cx + r*math.cos(desde + (hasta-desde)*i/n),
            cz + r*math.sin(desde + (hasta-desde)*i/n)) for i in range(n + 1)]
    return trazo(pts, color, grosor, seed, build=build, prof=prof)


def linea(x1, z1, x2, z2, color=GRIS, grosor=0.018, seed=0, build=None, prof=0.0):
    return trazo([(x1, z1), (x2, z2)], color, grosor, seed, build=build, prof=prof)


def flecha(x1, z1, x2, z2, color=GRIS, grosor=0.018, seed=0, punta=0.16, build=None, prof=0.0):
    ln = linea(x1, z1, x2, z2, color, grosor, seed, build=build, prof=prof)
    a = math.atan2(z2 - z1, x2 - x1)
    for s in (+1, -1):
        b = a + math.pi + s * 0.42
        trazo([(x2, z2), (x2 + punta*math.cos(b), z2 + punta*math.sin(b))],
              color, grosor, seed, build=build, prof=prof)
    return ln


# OJO con la tipografía: al convertir texto a Grease Pencil, Arial Black y Arial
# Bold MUTILAN la "v" — pierde la diagonal izquierda y se lee como barra. Se
# verificó glifo por glifo. Verdana Bold y Tahoma Bold convierten limpio.
FUENTES = {
    "black": "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "bold":  "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
}
_cache_fuente = {}


def fuente(peso):
    """La tipografía por defecto de Blender es demasiado ligera para este estilo:
    sobre negro y con bloom, un trazo fino se disuelve. Los rótulos piden peso."""
    if peso not in _cache_fuente:
        ruta = FUENTES.get(peso)
        _cache_fuente[peso] = bpy.data.fonts.load(ruta) if ruta and os.path.exists(ruta) else None
    return _cache_fuente[peso]


def texto(cuerpo, x, z, tam=0.30, color=INK, align='CENTER', build=None, prof=0.0,
          out=None, peso=None):
    cu = bpy.data.curves.new("c", 'FONT')
    cu.body, cu.size = cuerpo, tam
    cu.align_x, cu.align_y = align, 'CENTER'
    f = fuente(peso)
    if f:
        cu.font = f
    # Sin subir la resolución, al convertir a Grease Pencil los ángulos agudos se
    # mutilan: la "v" de "observa" perdía medio glifo y se leía como barra.
    cu.resolution_u = 16
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
    if build:
        dibujar(g, *build)
    k = k_prof(prof)
    g.scale = (k, k, k)
    g.location = (x * k, prof, z * k)   # NO (0, prof, 0): borraría la posición
    for l in g.data.layers:
        l.opacity = atmosfera(prof)
    if out:
        solo_entre(g, max(1, build[0] - 2) if build else 1, out)
    return g


def titulo(t, sub=None):
    texto(t, 0, 6.95, 0.52, INK)
    if sub:
        texto(sub, 0, 6.15, 0.26, GRIS)


def caja(cx, cz, w, h, etiqueta, color, tam=0.26, seed=0, r=0.26, build=None, prof=0.0):
    ob = rrect(cx, cz, w, h, r, color, 0.022, seed, build=build, prof=prof)
    t = texto(etiqueta, cx, cz, tam, color,
              build=(build[1] - 4, build[1] + 6) if build else None, prof=prof)
    return ob, t




def boil(ob, step=3, factor=0.55):
    """Line boil: el temblor del trazo se re-aleatoriza cada `step` frames, como
    en la animación tradicional donde cada dibujo se redibuja. Es lo que separa
    un trazo hecho a mano de una línea vectorial quieta.

    Ojo: el Noise ya trae use_random=True y step=4 por defecto, así que un poco
    de boil existe aunque nadie lo pida. Bajar el step lo hace evidente."""
    for m in ob.modifiers:
        if m.type == 'GREASE_PENCIL_NOISE':
            m.use_random = True
            m.random_mode = 'STEP'
            m.step = step
            m.factor = factor
    return ob


def flujo(ob, ciclo_s, fin_s, fps=30, dash=6, hueco=10):
    """Marcha de guiones a lo largo del trazo: la energía recorriendo el camino.
    Anima dash_offset, que es entero — la interpolación tiene que ser LINEAR o
    los guiones se aceleran y frenan en cada vuelta."""
    d = ob.modifiers.new("dash", 'GREASE_PENCIL_DASH')
    seg = d.segments[0]
    seg.dash, seg.gap = dash, hueco
    total = dash + hueco
    t = 0.0
    while t <= fin_s + ciclo_s:
        d.dash_offset = int(round(-total * (t / ciclo_s)))
        d.keyframe_insert("dash_offset", frame=max(1, int(t * fps)))
        t += ciclo_s
    for fc in _fc(ob):
        if "dash_offset" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    return ob


def resplandor(ob, veces=2.6, opacidad=0.12):
    """Bloom barato: una copia del trazo, mucho más gruesa y casi transparente,
    detrás. Evita el compositor de Blender 5, que para esto es un campo minado."""
    g = ob.copy()
    g.data = ob.data.copy()
    S.collection.objects.link(g)
    for l in g.data.layers:
        l.radius_offset = (l.radius_offset or 0) + 0.06
        l.opacity = opacidad
    g.scale = ob.scale
    g.location = (ob.location[0], ob.location[1] + 0.02, ob.location[2])
    return g


def _fc(ob):
    act = ob.animation_data.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    slot = ob.animation_data.action_slot
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot)
            if cb:
                out += list(cb.fcurves)
    return out


def bloom(fuerza=0.6, umbral=0.05, tam=0.8, suavidad=0.4):
    """Bloom real, en el compositor. Es lo que hace que la tinta clara sobre
    casi-negro se sienta luminosa en vez de impresa.

    Tres trampas de Blender 5, todas verificadas aquí:
      1. El árbol se mudó a `scene.compositing_node_group`.
      2. Los parámetros del Glare pasaron de propiedades a SOCKETS: no existe
         `glare_type`, es `inputs["Type"].default_value = 'Bloom'` (un menú).
      3. El render NO entra por la entrada del grupo. Hay que leerlo con un
         Render Layers DENTRO. Cablearlo desde NodeGroupInput deja el socket en
         su valor por defecto y el video sale en blanco puro.
    """
    ng = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')

    rl = ng.nodes.new("CompositorNodeRLayers")      # DENTRO del grupo
    rl.scene = S
    gl = ng.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = 'Bloom'       # socket de menú, no propiedad
    gl.inputs["Quality"].default_value = 'High'
    gl.inputs["Threshold"].default_value = umbral
    gl.inputs["Strength"].default_value = fuerza
    gl.inputs["Size"].default_value = tam
    gl.inputs["Smoothness"].default_value = suavidad
    out = ng.nodes.new("NodeGroupOutput")

    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs[0], out.inputs[0])

    S.compositing_node_group = ng
    S.render.use_compositing = True
    return ng


def solo_entre(ob, a, z):
    """Lo que no está en escena tiene que SALIR DEL RENDER, no sólo volverse
    invisible: EEVEE compone las superficies transparentes en un número limitado
    de capas por píxel y descarta el excedente, así que un objeto invisible a
    ocho segundos de distancia puede cortar lo que sí debería verse."""
    for f, oculto in ((1, True), (max(2, int(a) - 1), False), (int(z) + 1, True)):
        ob.hide_render = oculto
        ob.keyframe_insert("hide_render", frame=f)
    for fc in _fc(ob):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'   # un booleano no se interpola
    return ob
