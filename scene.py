"""
Anuncio de EasyBits — motion graphics 3D, Blender headless.

Tres actos:
  1. PROBLEMA  "Tus agentes generan archivos." / "¿Dónde los guardas?"
                 Los títulos aceleran contra la cámara y la atraviesan.
  2. PRODUCTO  Entra la UI real de la app. El cursor 3D hace clic. El botón se
                 despega de la pantalla y del impacto salen archivos 3D que se
                 ordenan solos en el aire.
  3. MARCA     Los archivos se apartan y entra el cierre: logo + easybits.cloud.

La UI no se modela: se captura con Chrome headless (capture.sh) y se aplica como
textura emisiva. Cada elemento que debe moverse en 3D es su propio objeto — por
eso el botón puede salir de la pantalla que lo contenía.

Uso:
    blender -b -P scene.py                 # render completo
    PREVIEW=1 blender -b -P scene.py       # stills baratos para revisar
    ONLY=titles,cursor PREVIEW=1 ...       # aislar objetos (biseccion de bugs)
    RANGE=520,960 blender -b -P scene.py   # re-renderizar solo un tramo
    FRAMES=460,640 PREVIEW=1 blender -b -P scene.py
"""

import bpy, json, math, os, random

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, "scene.json")))

RES_X, RES_Y = CFG["resolution"]
FPS = CFG["fps"]
END = CFG["duration_frames"]
B = CFG["beats"]

# El plano de la página mide 16x9 unidades y la cámara se encuadra para que
# calce exacto. De ahí sale el mapeo píxel->mundo: un rect en píxeles de
# scene.json cae donde debe sin ajustar nada a ojo.
PLANE_W = 16.0
PLANE_H = PLANE_W * RES_Y / RES_X
CAM_D = CFG["camera"]["distance"]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def hex_rgb(h, gamma=2.2):
    h = h.lstrip("#")
    return (*[(int(h[i:i + 2], 16) / 255.0) ** gamma for i in (0, 2, 4)], 1.0)


def px_to_world(px, py):
    return (-PLANE_W / 2 + px / RES_X * PLANE_W,
            PLANE_H / 2 - py / RES_Y * PLANE_H)


def px_size(w, h):
    return (w / RES_X * PLANE_W, h / RES_Y * PLANE_H)


def bezier4(pts, t):
    u = 1 - t
    return tuple(u ** 3 * pts[0][i] + 3 * u ** 2 * t * pts[1][i]
                 + 3 * u * t ** 2 * pts[2][i] + t ** 3 * pts[3][i] for i in (0, 1))


def fcurves(id_data):
    """Blender 4.4+ movió las fcurves a channelbags dentro de slots."""
    ad = id_data.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    if hasattr(act, "fcurves"):
        yield from act.fcurves
        return
    slot = getattr(ad, "action_slot", None)
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot) if slot else None
            if cb:
                yield from cb.fcurves


def _shape(holder, path, frame, index, interp, easing):
    for fc in fcurves(holder):
        if fc.data_path != path or (index != -1 and fc.array_index != index):
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = interp
                if easing:
                    kp.easing = easing


def key(obj, path, frame, value, index=-1, interp="BEZIER", easing=None):
    if index == -1:
        setattr(obj, path, value)
    else:
        getattr(obj, path)[index] = value
    obj.keyframe_insert(data_path=path, frame=frame, index=index)
    _shape(obj, path, frame, index, interp, easing)


def key_socket(mat, socket, frame, value, interp="BEZIER", easing=None):
    """Keyframea un input de nodo (lo usamos para fundidos de emisión)."""
    socket.default_value = value
    socket.keyframe_insert("default_value", frame=frame)
    _shape(mat.node_tree, socket.path_from_id("default_value"), frame, -1,
           interp, easing)


# --------------------------------------------------------------------------- #
# geometría
# --------------------------------------------------------------------------- #

def rounded_rect_mesh(name, w, h, r, seg=8):
    """Rectángulo redondeado REAL, con UVs planares.

    Importa: si la malla fuera un rectángulo recto y el redondeo viviera solo en
    el alpha de la textura, el Solidify extruiría esquinas cuadradas por debajo
    del recorte — se ven como muescas en cuanto el objeto gira.
    """
    r = min(r, w / 2, h / 2)
    cx, cy = w / 2 - r, h / 2 - r
    # Contorno = cuatro arcos consecutivos en sentido antihorario.
    verts = []
    corners = ((cx, cy, 0.0), (-cx, cy, 0.5), (-cx, -cy, 1.0), (cx, -cy, 1.5))
    for ox, oy, a0 in corners:
        for i in range(seg + 1):
            a = (a0 + i / seg * 0.5) * math.pi
            verts.append((ox + r * math.cos(a), oy + r * math.sin(a), 0.0))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [list(range(len(verts)))])
    mesh.update()

    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        vx, vy, _ = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (vx / w + 0.5, vy / h + 0.5)
    return mesh


def card_obj(name, image, w, radius_frac=0.0, depth=0.0, emit=1.0):
    """Plano con textura (alpha) y grosor opcional. La altura sale del aspect
    real del PNG, así nunca se deforma la tipografía."""
    img = bpy.data.images.load(os.path.join(ROOT, image))
    h = w * img.size[1] / img.size[0]
    r = h * radius_frac
    mesh = rounded_rect_mesh(name + "M", w, h, r) if r > 0 else None
    if mesh is None:
        mesh = rounded_rect_mesh(name + "M", w, h, 0.0001)

    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)

    mat, strength = image_emissive(name + "Mat", img, emit)
    o.data.materials.append(mat)
    if depth > 0:
        s = o.modifiers.new("D", "SOLIDIFY")
        s.thickness, s.offset = depth, 0
    return o, mat, strength, (w, h)


def image_emissive(name, img, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Strength"].default_value = strength
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    # El alpha de la textura y el fundido de emisión se multiplican: así una
    # tarjeta puede desvanecerse sin perder su recorte.
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    fade = nt.nodes.new("ShaderNodeValue")
    fade.label = "Fade"
    fade.outputs[0].default_value = 1.0

    nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
    nt.links.new(fade.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emi.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    set_blend(mat)
    return mat, fade.outputs[0]


def set_blend(mat):
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    if hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    if hasattr(mat, "show_transparent_back"):
        mat.show_transparent_back = False


def solid(name, color, rough=0.35, metallic=0.0, emit=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if emit:
        b.inputs["Emission Color"].default_value = color
        b.inputs["Emission Strength"].default_value = emit
    return mat


def plane(name, w, h, loc):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    return o


# --------------------------------------------------------------------------- #
# escena
# --------------------------------------------------------------------------- #

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, END
    sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = \
        hex_rgb(CFG["render"]["world_color"])
    sc.world = world


def build_camera():
    """Perspectiva encuadrada para que z=0 mida exactamente 16x9.

    Ortográfica sería más simple, pero entonces los objetos que vuelan hacia el
    espectador no crecerían y todo el 3D se perdería. Con perspectiva el mapeo
    píxel->mundo sigue siendo exacto en z=0, que es donde vive la UI.
    """
    cd = bpy.data.cameras.new("Cam")
    cd.type = "PERSP"
    cd.sensor_fit = "HORIZONTAL"
    cd.angle = 2 * math.atan((PLANE_W / 2) / CAM_D)
    cd.dof.use_dof = True
    cd.dof.focus_distance = CAM_D
    cd.dof.aperture_fstop = CFG["camera"]["fstop"]

    cam = bpy.data.objects.new("Cam", cd)
    cam.location = (0, 0, CAM_D)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    # La cámara nunca se queda quieta, pero tampoco compite con la acción: son
    # empujes lentos que dan vida y luego devuelven el encuadre completo para las
    # escenas que necesitan ancho.
    for frame, z_pos, ease in CFG["camera"]["moves"]:
        key(cam, "location", frame, z_pos, index=2,
            interp="BEZIER", easing=ease)
    return cam


def build_lights():
    # La UI es emisiva y no depende de luz. Estas dos existen solo para dar
    # volumen a lo que se despega del plano: botón, cursor y tarjetas.
    for name, energy, size, loc, rot, color in (
        ("Key", 1100, 10, (-6, 7, 9), (38, 0, -32), (1, 1, 1)),
        ("Rim", 520, 8, (8, -6, 6), (-42, 0, 48), hex_rgb("#BAD9D8")[:3]),
    ):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.size, d.color = energy, size, color
        o = bpy.data.objects.new(name, d)
        o.location = loc
        o.rotation_euler = tuple(math.radians(v) for v in rot)
        bpy.context.collection.objects.link(o)


def only_between(o, a, z):
    """Sacar del render lo que todavía no entra o ya salió.

    Poner alpha 0 NO basta. EEVEE compone las superficies BLENDED en un número
    limitado de capas por píxel y descarta el excedente: los planos de una escena
    futura, invisibles pero presentes en el encuadre, se comen el cupo y tiran la
    capa de lo que SÍ debería verse. Se manifiesta como texto cortado por una
    línea recta, o parpadeando entre frames.

    Fue el bug de "guardas?": trece planos de la escena de la flota, a alpha 0 y
    a 8 segundos de aparecer, cortaban una palabra del primer acto.

    hide_render los quita del apilamiento por completo (y acelera el render).
    """
    for f, hidden in ((1, True), (max(2, int(a) - 1), False), (int(z) + 1, True)):
        o.hide_render = hidden
        o.keyframe_insert("hide_render", frame=f)
    for fc in fcurves(o):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def fade_out(mat, fade, a, z):
    key_socket(mat, fade, a, 1.0)
    key_socket(mat, fade, z, 0.0, easing="EASE_IN")


def retire(o, mat, fade, a, z, from_z, to_z=-3.2):
    """Retirar un objeto = fundirlo Y alejarlo.

    Fundir en el sitio no basta. Los materiales BLENDED de EEVEE no escriben
    profundidad y se ordenan por la distancia del ORIGEN del objeto: dos planos
    translúcidos que se solapan en pantalla casi a la misma Z intercambian orden
    entre frames y parpadean. Mientras una escena se va y la siguiente entra, las
    dos coexisten unos frames — si no se separan en Z, el bug es seguro.

    Alejar al que sale resuelve el orden y además se lee mejor: las cosas se van,
    no desaparecen.
    """
    fade_out(mat, fade, a, z)
    key(o, "location", a, from_z, index=2)
    key(o, "location", z, to_z, index=2, interp="BEZIER", easing="EASE_IN")


def build_titles():
    """Acto 1, palabra por palabra.

    Cada palabra es su propio objeto y entra escalonada: por eso la frase se
    "escribe" en el aire en vez de aparecer como un bloque. Las posiciones NO se
    calculan aquí — las midió el navegador (`assets/layout.json`, ver capture.sh)
    y solo se convierten a coordenadas de mundo. Calcularlas a mano se desalinea
    con cualquier cambio de fuente, kerning o letter-spacing.

    Las palabras cuelgan de un Empty por línea: la entrada se anima por palabra,
    pero la salida —atravesar la cámara, que ES la transición al acto 2— se anima
    una sola vez sobre el padre.
    """
    layout = json.load(open(os.path.join(ROOT, "assets/layout.json")))
    PAD = 10          # el margen que capture.sh añade alrededor de cada palabra

    for li, t in enumerate(CFG["titles"]):
        block = layout[t["layout_key"]]
        scale = t["width"] / block["w"]
        ia, iz = t["in"]
        oa, oz = t["out"]
        y_line = t["y"]

        group = bpy.data.objects.new(f"TitleLine{li}", None)
        group.empty_display_size = 0.4
        bpy.context.collection.objects.link(group)
        group.location = (0, y_line, 1.0)

        mats = []
        words = block["words"]
        for wi, wd in enumerate(words):
            o, mat, fade, _ = card_obj(f"W{li}_{wi}",
                                       f"assets/w{li}_{wi}.png",
                                       (wd["w"] + PAD) * scale)
            mats.append((mat, fade))
            o.parent = group
            # centro de la palabra dentro del bloque, en coordenadas de mundo
            cx = (wd["x"] + (wd["w"] + PAD) / 2 - block["w"] / 2) * scale
            cy = (block["h"] / 2 - wd["y"] - (wd["h"] + PAD) / 2) * scale

            # escalonado: cada palabra arranca un poco después que la anterior
            f0 = ia + wi * t["stagger"]
            f1 = f0 + t["word_dur"]

            key(o, "location", f0, cx, index=0)
            key(o, "location", f0, cy - 0.55, index=1)
            key(o, "location", f0, -1.6, index=2)
            key(o, "location", f1, cy, index=1, interp="BACK", easing="EASE_OUT")
            key(o, "location", f1, wi * 0.012, index=2, interp="BEZIER",
                easing="EASE_OUT")

            # cabecea al entrar y se endereza: da peso sin animar a mano
            key(o, "rotation_euler", f0, math.radians(-42), index=0)
            key(o, "rotation_euler", f1, 0.0, index=0, easing="EASE_OUT")

            key_socket(mat, fade, f0, 0.0)
            key_socket(mat, fade, f0 + 5, 1.0, easing="EASE_OUT")
            only_between(o, f0, oz)

        # salida en grupo: la línea entera acelera contra la cámara
        key(group, "location", oa, 1.0, index=2)
        key(group, "location", oz, CAM_D + 3, index=2, interp="BEZIER", easing="EASE_IN")
        for mat, fade in mats:
            key_socket(mat, fade, oz - 9, 1.0)
            key_socket(mat, fade, oz, 0.0, easing="EASE_IN")


def build_page():
    p = plane("Page", PLANE_W, PLANE_H, (0, 0, 0))
    img = bpy.data.images.load(os.path.join(ROOT, CFG["page"]["texture"]))
    mat, fade = image_emissive("PageMat", img, 1.0)
    p.data.materials.append(mat)

    a, z = B["page_in"]
    key(p, "location", a, -3.5, index=2)
    key(p, "location", z, 0.0, index=2, interp="BEZIER", easing="EASE_OUT")
    key_socket(mat, fade, a, 0.0)
    key_socket(mat, fade, z, 1.0, easing="EASE_OUT")

    # Se retira para dejar la marca sola.
    ca, cz = B["clear"]
    key_socket(mat, fade, ca, 1.0)
    key_socket(mat, fade, cz, 0.0, easing="EASE_IN")
    key(p, "location", ca, 0.0, index=2)
    key(p, "location", cz, -6.0, index=2, interp="BEZIER", easing="EASE_IN")
    only_between(p, a, cz)
    return p


def build_button():
    bc = CFG["button"]
    x, y, w, h = bc["rect_px"]
    bw, bh = px_size(w, h)
    cx, cy = px_to_world(x + w / 2, y + h / 2)

    o, mat, fade, _ = card_obj("Button", bc["texture"], bw,
                               radius_frac=bc["radius_px"] / h)
    o.location = (cx, cy, 0.014)

    # Grosor animado: el botón nace plano y se vuelve sólido. Ese crecimiento
    # ES el "salta de la pantalla"; sin él solo se levantaría una calcomanía.
    sol = o.modifiers.new("Depth", "SOLIDIFY")
    sol.offset, sol.use_rim = 1, True
    sol.material_offset_rim = 1
    o.data.materials.append(solid("BtnSide", hex_rgb(bc["color"]),
                                  rough=0.26, emit=0.5))

    # El botón no existe durante el acto 1: sin esto se ve flotando sobre los
    # títulos, porque una fcurve extrapola su primer valor hacia atrás.
    pa, pz = B["page_in"]
    key_socket(mat, fade, 1, 0.0)
    key_socket(mat, fade, pa, 0.0)
    key_socket(mat, fade, pz, 1.0, easing="EASE_OUT")

    a, z = B["button_pop"]
    mid = a + int((z - a) * 0.45)
    sol.thickness = 0.0
    sol.keyframe_insert("thickness", frame=a)
    sol.thickness = bc["depth"]
    sol.keyframe_insert("thickness", frame=z)

    key(o, "location", a, 0.014, index=2)
    key(o, "location", z, bc["lift"], index=2, interp="BACK", easing="EASE_OUT")
    key(o, "rotation_euler", a, 0.0, index=0)
    key(o, "rotation_euler", mid, math.radians(-15), index=0)
    key(o, "rotation_euler", z, math.radians(-8), index=0)
    key(o, "rotation_euler", a, 0.0, index=1)
    key(o, "rotation_euler", z, math.radians(10), index=1)
    for i in (0, 1):
        key(o, "scale", a, 1.0, index=i)
        key(o, "scale", z, 1.16, index=i, interp="BACK", easing="EASE_OUT")

    ca, cz = B["clear"]
    key_socket(mat, fade, ca, 1.0)
    key_socket(mat, fade, cz, 0.0, easing="EASE_IN")
    sol.thickness = bc["depth"]
    sol.keyframe_insert("thickness", frame=ca)
    sol.thickness = 0.0
    sol.keyframe_insert("thickness", frame=cz)
    key(o, "location", ca, bc["lift"], index=2)
    key(o, "location", cz, -4.0, index=2, interp="BEZIER", easing="EASE_IN")
    only_between(o, B["page_in"][0], cz)
    return o, (cx, cy)


def build_shadow(origin):
    """La página es emisión pura: no recibe luz, así que no puede recibir una
    sombra real. Este blob radial es lo único que hace leer al botón como objeto
    despegado y no como calcomanía flotante."""
    bc = CFG["button"]
    _, _, w, h = bc["rect_px"]
    bw, bh = px_size(w, h)
    cx, cy = origin
    s = plane("Shadow", bw * 2.6, bh * 4.2, (cx, cy, 0.006))

    mat = bpy.data.materials.new("ShadowMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    # Generated va 0..1 desde la ESQUINA del bbox; el gradiente esférico mide
    # desde el origen. Sin recentrar, la sombra nace en una esquina.
    remap = nt.nodes.new("ShaderNodeMapping")
    remap.inputs["Location"].default_value = (-0.5, -0.5, -0.5)
    remap.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.92
    op = nt.nodes.new("ShaderNodeValue")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    dark = nt.nodes.new("ShaderNodeEmission")
    dark.inputs["Color"].default_value = (0, 0, 0, 1)
    dark.inputs["Strength"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    nt.links.new(coord.outputs["Generated"], remap.inputs["Vector"])
    nt.links.new(remap.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(op.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(dark.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    set_blend(mat)
    s.data.materials.append(mat)

    a, z = B["button_pop"]
    key_socket(mat, op.outputs[0], a - 1, 0.0)
    key_socket(mat, op.outputs[0], a + 8, 0.85)
    key_socket(mat, op.outputs[0], z, 0.5)
    key_socket(mat, op.outputs[0], B["clear"][0], 0.5)
    key_socket(mat, op.outputs[0], B["clear"][1], 0.0)
    for i in (0, 1):
        key(s, "scale", a, 0.55, index=i)
        key(s, "scale", z, 1.0, index=i, interp="BACK", easing="EASE_OUT")
    key(s, "location", a, cx, index=0)
    key(s, "location", z, cx + 0.2, index=0)
    key(s, "location", a, cy, index=1)
    key(s, "location", z, cy - 0.28, index=1)
    only_between(s, a - 1, B["clear"][1])


def build_shockwave(origin):
    """Onda de choque del clic: anillo plano que se expande y se apaga.
    Es el acento que hace que el clic se sienta como impacto y no como cambio
    de estado."""
    cx, cy = origin
    bpy.ops.mesh.primitive_circle_add(radius=1.0, vertices=64, fill_type="NGON",
                                      location=(cx, cy, 0.03))
    o = bpy.context.object
    o.name = "Shock"

    mat = bpy.data.materials.new("ShockMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    remap = nt.nodes.new("ShaderNodeMapping")
    remap.inputs["Location"].default_value = (-0.5, -0.5, -0.5)
    remap.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    # El gradiente esférico vale 1 en el centro y 0 en el borde. Con dos paradas
    # sale un DISCO relleno; para que sea un anillo hace falta una tercera que
    # vuelva a cerrar en negro: opaco solo en una banda estrecha junto al borde.
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0, 0, 0, 1)
    cr.elements[1].position = 0.11
    cr.elements[1].color = (0, 0, 0, 1)
    peak = cr.elements.new(0.045)
    peak.color = (1, 1, 1, 1)
    op = nt.nodes.new("ShaderNodeValue")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = hex_rgb("#C9AEFF")
    emi.inputs["Strength"].default_value = 2.2
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    nt.links.new(coord.outputs["Generated"], remap.inputs["Vector"])
    nt.links.new(remap.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(op.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emi.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    set_blend(mat)
    o.data.materials.append(mat)

    a, z = B["shockwave"]
    for i in (0, 1):
        key(o, "scale", a, 0.25, index=i)
        key(o, "scale", z, 2.0, index=i, interp="BEZIER", easing="EASE_OUT")
    key_socket(mat, op.outputs[0], a, 0.0)
    key_socket(mat, op.outputs[0], a + 3, 0.55)
    key_socket(mat, op.outputs[0], z, 0.0, easing="EASE_IN")
    only_between(o, a, z)


def build_file_cards(origin):
    """Acto 2, el remate: del clic salen ARCHIVOS, no confeti.

    El confeti celebra; los archivos dicen qué hace el producto. Cada tarjeta
    hace dos movimientos: estalla hacia afuera y luego se acomoda en una malla
    ordenada. Ese "se ordenan solos" es el mensaje del anuncio.
    """
    cc = CFG["cards"]
    rng = random.Random(cc["seed"])
    ox, oy = origin
    cols, rows = cc["grid"]
    gx, gy = cc["grid_gap"]

    slots = [(( c - (cols - 1) / 2) * gx, ((rows - 1) / 2 - r) * gy)
             for r in range(rows) for c in range(cols)]
    rng.shuffle(slots)

    ba, bz = B["burst"]
    sa, sz = B["settle"]
    ca, cz = B["clear"]
    mats = []

    for i in range(cc["count"]):
        tex = cc["textures"][i % len(cc["textures"])]
        o, mat, fade, (w, h) = card_obj(f"Card{i}", tex, cc["width"],
                                        radius_frac=cc["radius_frac"],
                                        depth=cc["depth"], emit=1.7)
        mats.append((mat, fade))

        birth = ba + rng.randint(0, 14)
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(1.8, 4.6)
        bx = ox + math.cos(ang) * dist
        by = oy + math.sin(ang) * dist * 0.7
        bzz = rng.uniform(3.2, 6.8)          # hacia el espectador

        sx, sy = slots[i % len(slots)]
        szz = cc["grid_z"] + rng.uniform(-0.25, 0.25)

        # nace dentro del botón
        for ax, v in enumerate((ox, oy, 0.2)):
            key(o, "location", birth, v, index=ax)
        for ax in range(3):
            key(o, "scale", birth, 0.02, index=ax)
            key(o, "scale", birth + 6, 1.0, index=ax, interp="BACK", easing="EASE_OUT")

        # estalla
        for ax, v in enumerate((bx, by, bzz)):
            key(o, "location", bz, v, index=ax, interp="BEZIER", easing="EASE_OUT")
        # se ordena
        for ax, v in enumerate((sx, sy, szz)):
            key(o, "location", sz, v, index=ax, interp="BEZIER", easing="EASE_IN_OUT")

        # gira caótico y termina de frente: el orden final se siente ganado
        for ax in range(3):
            key(o, "rotation_euler", birth, rng.uniform(-1.2, 1.2), index=ax,
                interp="BEZIER")
            key(o, "rotation_euler", bz, rng.uniform(-2.5, 2.5), index=ax)
            key(o, "rotation_euler", sz, 0.0, index=ax, easing="EASE_IN_OUT")

        # se apartan para el cierre
        for ax, v in enumerate((sx * 2.6, sy * 2.6, szz + 6.0)):
            key(o, "location", ca, (sx, sy, szz)[ax], index=ax)
            key(o, "location", cz, v, index=ax, interp="BEZIER", easing="EASE_IN")

        key_socket(mat, fade, max(1, birth - 1), 0.0)
        key_socket(mat, fade, birth, 1.0)
        key_socket(mat, fade, ca, 1.0)
        key_socket(mat, fade, cz, 0.0, easing="EASE_IN")
        only_between(o, birth, cz)
    return mats


def build_cursor():
    pts = [(0, 0), (0, -1.0), (0.24, -0.76), (0.42, -1.12),
           (0.58, -1.05), (0.40, -0.70), (0.70, -0.66)]
    s = 0.62
    mesh = bpy.data.meshes.new("CursorMesh")
    mesh.from_pydata([(p[0] * s, p[1] * s, 0) for p in pts], [],
                     [list(range(len(pts)))])
    mesh.update()
    c = bpy.data.objects.new("Cursor", mesh)
    bpy.context.collection.objects.link(c)
    m = c.modifiers.new("D", "SOLIDIFY"); m.thickness, m.offset = 0.11, 0
    b = c.modifiers.new("B", "BEVEL"); b.width, b.segments = 0.016, 3
    c.data.materials.append(solid("CursorMat", hex_rgb(CFG["cursor"]["color"]),
                                  rough=0.22, emit=0.15))

    path = [px_to_world(*p) for p in CFG["cursor"]["path_px"]]
    a, z = B["cursor_in"]
    ca, cz = B["click"]

    # Mismo motivo que el botón: encogido a cero hasta que le toca entrar.
    for ax in range(3):
        key(c, "scale", 1, 0.0, index=ax)
        key(c, "scale", a - 1, 0.0, index=ax)
        key(c, "scale", a + 4, 1.0, index=ax, interp="BACK", easing="EASE_OUT")

    # El easing vive en el parámetro de la Bézier, no en las keyframes: así la
    # velocidad sigue la curva y no el interpolador.
    steps = 24
    for i in range(steps + 1):
        f = a + (z - a) * i / steps
        t = 1 - (1 - i / steps) ** 3
        px, py = bezier4(path, t)
        key(c, "location", f, px, index=0, interp="LINEAR")
        key(c, "location", f, py, index=1, interp="LINEAR")

    key(c, "location", a, 3.4, index=2)
    key(c, "location", z, 0.6, index=2, easing="EASE_OUT")
    key(c, "location", ca, 0.6, index=2)
    key(c, "location", ca + 4, 0.14, index=2, easing="EASE_IN")
    key(c, "location", cz, 0.68, index=2, interp="BACK", easing="EASE_OUT")
    key(c, "rotation_euler", a, math.radians(34), index=0)
    key(c, "rotation_euler", z, math.radians(8), index=0, easing="EASE_OUT")
    key(c, "rotation_euler", a, math.radians(-22), index=1)
    key(c, "rotation_euler", z, 0.0, index=1, easing="EASE_OUT")

    # Sale de cuadro en XY mientras las tarjetas se ordenan.
    ex = B["settle"][0]
    lx, ly = bezier4(path, 1.0)
    key(c, "location", ex, lx, index=0)
    key(c, "location", ex, ly, index=1)
    key(c, "location", ex + 40, lx + 7.0, index=0, easing="EASE_IN")
    key(c, "location", ex + 40, ly - 8.0, index=1, easing="EASE_IN")
    only_between(c, a, ex + 41)


def build_end():
    o, mat, fade, _ = card_obj("End", CFG["end"]["texture"], CFG["end"]["width"],
                               emit=1.6)
    a, z = B["end_in"]
    o.location = (0, 0, 0)
    # Muy por delante del resto: aunque quede un rastro de la escena anterior,
    # el orden de dibujado no puede quedar en duda.
    key(o, "location", a, -6.0, index=2)
    key(o, "location", z, 1.6, index=2, interp="BEZIER", easing="EASE_OUT")
    key(o, "location", END, 2.4, index=2)
    key_socket(mat, fade, a, 0.0)
    key_socket(mat, fade, z, 1.0, easing="EASE_OUT")


# --------------------------------------------------------------------------- #
# escenas 3-5: el agente, la flota, compartir
#
# Las tres reusan la misma maquinaria del acto 2 —planos con textura capturada,
# grosor por Solidify, entrada con overshoot— porque ya está probada. Lo que
# cambia es la coreografía, y eso vive en scene.json.
# --------------------------------------------------------------------------- #

def scene_title(key_name, tex, width, y):
    """Título de escena: entra desde abajo, se sostiene, se va hacia atrás."""
    a, z = B[key_name]
    o, mat, fade, _ = card_obj(f"T_{key_name}", tex, width)
    o.location = (0, y, 0.4)
    key(o, "location", a, y - 0.7, index=1)
    key(o, "location", a + 20, y, index=1, interp="BACK", easing="EASE_OUT")
    key_socket(mat, fade, a, 0.0)
    key_socket(mat, fade, a + 16, 1.0, easing="EASE_OUT")
    key_socket(mat, fade, z - 18, 1.0)
    key_socket(mat, fade, z, 0.0, easing="EASE_IN")
    key(o, "location", z - 18, 0.4, index=2)
    key(o, "location", z, -3.0, index=2, easing="EASE_IN")
    only_between(o, a, z)
    return o


def emit_card(name, tex, start, src, dst, spin=1.0, dur=46, fade_tail=14):
    """Un archivo que sale de un punto y viaja a otro. Es el gesto que repite
    todo el anuncio: en el acto 2 sale del botón, aquí de una tool y de cada
    canal."""
    cc = CFG["cards"]
    o, mat, fade, _ = card_obj(name, tex, cc["width"] * 0.82,
                               radius_frac=cc["radius_frac"],
                               depth=cc["depth"], emit=1.7)
    end = start + dur
    for ax in range(3):
        key(o, "location", start, src[ax], index=ax)
        key(o, "location", end, dst[ax], index=ax,
            interp="BEZIER", easing="EASE_OUT")
        key(o, "scale", start, 0.02, index=ax)
        key(o, "scale", start + 7, 1.0, index=ax, interp="BACK", easing="EASE_OUT")
    for ax in range(3):
        key(o, "rotation_euler", start, random.uniform(-0.9, 0.9) * spin, index=ax)
        key(o, "rotation_euler", end, 0.0, index=ax, easing="EASE_IN_OUT")
    key_socket(mat, fade, max(1, start - 1), 0.0)
    key_socket(mat, fade, start, 1.0)
    key_socket(mat, fade, end - fade_tail, 1.0)
    key_socket(mat, fade, end, 0.0, easing="EASE_IN")
    only_between(o, start, end)
    return o


def build_scene_agent():
    """El agente trabajando: llama sus tools y de cada llamada sale un archivo.

    Es la escena que explica el producto — las otras lo muestran. Por eso las
    tools se leen textuales (`upload_file()`), no como iconos abstractos.
    """
    cfg = CFG["scenes"]["agent"]
    a, z = B["agent"]

    panel, pmat, pfade, (pw, ph) = card_obj("AgentPanel", "assets/agent.png",
                                            cfg["panel_width"],
                                            radius_frac=0.108, depth=0.09)
    px, py = cfg["panel_pos"]
    panel.location = (px, py, 0.15)
    key(panel, "location", a, -3.2, index=2)
    key(panel, "location", a + 26, 0.15, index=2, interp="BACK", easing="EASE_OUT")
    key(panel, "rotation_euler", a, math.radians(-24), index=1)
    key(panel, "rotation_euler", a + 26, math.radians(-7), index=1, easing="EASE_OUT")
    key_socket(pmat, pfade, a, 0.0)
    key_socket(pmat, pfade, a + 18, 1.0, easing="EASE_OUT")
    fade_out(pmat, pfade, z - 22, z)
    key(panel, "location", z - 22, 0.15, index=2)
    key(panel, "location", z, -3.6, index=2, easing="EASE_IN")
    only_between(panel, a, z)

    rng = random.Random(21)
    tx, ty0, gap = cfg["tools_pos"]
    for i in range(3):
        o, mat, fade, (tw, th) = card_obj(f"Tool{i}", f"assets/tool{i}.png",
                                          cfg["tool_width"],
                                          radius_frac=0.19, depth=0.06)
        ty = ty0 - i * gap
        o.location = (tx, ty, 0.5)
        f0 = a + cfg["tool_in"] + i * cfg["tool_stagger"]

        key(o, "location", f0, tx - 1.1, index=0)
        key(o, "location", f0 + 18, tx, index=0, interp="BACK", easing="EASE_OUT")
        key(o, "location", f0, ty, index=1)
        key_socket(mat, fade, f0, 0.0)
        key_socket(mat, fade, f0 + 10, 1.0, easing="EASE_OUT")
        for ax in (0, 1, 2):
            key(o, "scale", f0, 0.6 if ax != 2 else 1.0, index=ax)
            key(o, "scale", f0 + 14, 1.0, index=ax, interp="BACK", easing="EASE_OUT")
        retire(o, mat, fade, z - 26, z - 6, 0.5)
        only_between(o, f0, z - 6)

        # de cada tool sale un archivo hacia el espectador
        emit_card(f"AgentFile{i}", CFG["cards"]["textures"][i * 2],
                  f0 + cfg["emit_delay"], (tx + 0.6, ty, 0.6),
                  (tx + rng.uniform(0.8, 2.4), ty + rng.uniform(1.4, 3.2), 7.5))

    scene_title("agent_title", "assets/t3.png", cfg["title_width"], cfg["title_y"])


def build_scene_fleet():
    """La flota: tres canales distintos alimentando un mismo almacén.

    La convergencia es el mensaje. Los archivos salen de WhatsApp, del widget web
    y de la terminal, y terminan apilados en el MISMO punto.
    """
    cfg = CFG["scenes"]["fleet"]
    a, z = B["fleet"]
    rng = random.Random(33)
    cx, cy = cfg["converge"]

    for i in range(3):
        o, mat, fade, (w, h) = card_obj(f"Chan{i}", f"assets/chan{i}.png",
                                        cfg["panel_width"],
                                        radius_frac=0.096, depth=0.07)
        x = (i - 1) * cfg["spread"]
        y = cfg["panel_y"]
        o.location = (x, y, 0.2)
        f0 = a + i * cfg["stagger"]

        key(o, "location", f0, y - 1.5, index=1)
        key(o, "location", f0 + 22, y, index=1, interp="BACK", easing="EASE_OUT")
        key(o, "rotation_euler", f0, math.radians(-38), index=0)
        key(o, "rotation_euler", f0 + 22, 0.0, index=0, easing="EASE_OUT")
        key_socket(mat, fade, f0, 0.0)
        key_socket(mat, fade, f0 + 12, 1.0, easing="EASE_OUT")
        retire(o, mat, fade, z - 24, z, 0.2)
        only_between(o, f0, z)

        # cada canal manda archivos al mismo punto: eso ES el mensaje
        for k in range(cfg["files_per_channel"]):
            start = a + cfg["emit_in"] + i * 7 + k * cfg["emit_gap"]
            dst = (cx + rng.uniform(-1.5, 1.5),
                   cy + k * 0.34 + rng.uniform(-0.1, 0.1),
                   0.6 + k * 0.09)
            emit_card(f"FleetFile{i}{k}", CFG["cards"]["textures"][(i * 3 + k) % 8],
                      start, (x, y - 0.9, 0.5), dst, spin=0.6, dur=40, fade_tail=8)

    scene_title("fleet_title", "assets/t4.png", cfg["title_width"], cfg["title_y"])


def build_scene_share():
    """Compartir: un link que se multiplica.

    El pill entra solo y sostiene —hay que poder LEER la URL— y recién después se
    replica. Si se replicara de inmediato, el dato que importa no se lee.
    """
    cfg = CFG["scenes"]["share"]
    a, z = B["share"]
    rng = random.Random(44)

    pill, mat, fade, (pw, ph) = card_obj("SharePill", "assets/share.png",
                                         cfg["width"], radius_frac=0.25, depth=0.07)
    pill.location = (0, cfg["y"], 0.6)
    key(pill, "location", a, -2.4, index=2)
    key(pill, "location", a + 22, 0.6, index=2, interp="BACK", easing="EASE_OUT")
    for ax in (0, 1):
        key(pill, "scale", a, 0.72, index=ax)
        key(pill, "scale", a + 22, 1.0, index=ax, interp="BACK", easing="EASE_OUT")
    key_socket(mat, fade, a, 0.0)
    key_socket(mat, fade, a + 14, 1.0, easing="EASE_OUT")
    retire(pill, mat, fade, z - 26, z - 4, 0.6)
    only_between(pill, a, z - 4)

    # copias que salen disparadas: el link viaja
    for i in range(cfg["copies"]):
        o, m2, f2, _ = card_obj(f"ShareCopy{i}", "assets/share.png",
                                cfg["width"] * 0.46, radius_frac=0.25, depth=0.05)
        f0 = a + cfg["copy_in"] + i * cfg["copy_stagger"]
        # círculo completo: media circunferencia las apilaba a la derecha
        ang = math.tau * (i + 0.35) / cfg["copies"]
        dist = rng.uniform(6.5, 9.5)
        for ax, v in enumerate((0.0, cfg["y"], 0.6)):
            key(o, "location", f0, v, index=ax)
        key(o, "location", f0 + 44, math.cos(ang) * dist, index=0, easing="EASE_OUT")
        key(o, "location", f0 + 44, cfg["y"] + math.sin(ang) * dist * 0.48,
            index=1, easing="EASE_OUT")
        key(o, "location", f0 + 44, rng.uniform(3.0, 6.5), index=2, easing="EASE_OUT")
        for ax in range(3):
            key(o, "scale", f0, 0.05, index=ax)
            key(o, "scale", f0 + 10, 1.0, index=ax, interp="BACK", easing="EASE_OUT")
        key(o, "rotation_euler", f0, 0.0, index=1)
        key(o, "rotation_euler", f0 + 44, rng.uniform(-0.8, 0.8), index=1)
        key_socket(m2, f2, max(1, f0 - 1), 0.0)
        key_socket(m2, f2, f0, 1.0)
        key_socket(m2, f2, f0 + 30, 1.0)
        key_socket(m2, f2, f0 + 46, 0.0, easing="EASE_IN")
        only_between(o, f0, f0 + 46)

    scene_title("share_title", "assets/t5.png", cfg["title_width"], cfg["title_y"])


def setup_glow(sc):
    """Bloom. Dejó de ser opción del motor en EEVEE Next y vive en el
    compositor; en Blender 5 el árbol además se mudó a un node group y los
    parámetros del Glare pasaron de propiedades a sockets de entrada. Sin esto
    los emisivos (botón, onda de choque, marca) se ven planos."""
    if hasattr(sc, "compositing_node_group"):                    # Blender 5+
        ng = bpy.data.node_groups.new("Glow", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT",
                                socket_type="NodeSocketColor")
        # El render NO entra por la entrada del grupo: hay que leerlo con un
        # Render Layers DENTRO. Cablearlo desde NodeGroupInput deja el socket en
        # su valor por defecto (blanco) y el video sale en blanco puro.
        rl = ng.nodes.new("CompositorNodeRLayers")
        gout = ng.nodes.new("NodeGroupOutput")
        glare = ng.nodes.new("CompositorNodeGlare")
        for socket, value in (("Type", "Bloom"), ("Quality", "High"),
                              ("Threshold", 0.9), ("Strength", 0.42),
                              ("Size", 7)):
            if socket in glare.inputs:
                try:
                    glare.inputs[socket].default_value = value
                except TypeError:
                    pass
        ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
        ng.links.new(glare.outputs["Image"], gout.inputs[0])
        sc.compositing_node_group = ng
        return

    sc.use_nodes = True                                          # legacy
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    kinds = [i.identifier for i in
             glare.bl_rna.properties["glare_type"].enum_items]
    glare.glare_type = "BLOOM" if "BLOOM" in kinds else "FOG_GLOW"
    glare.quality, glare.threshold = "HIGH", 0.9
    if hasattr(glare, "mix"):
        glare.mix = -0.7
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], comp.inputs["Image"])


def configure_render():
    sc = bpy.context.scene
    r = CFG["render"]
    engines = {e.identifier for e in
               bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if r["engine"].upper() == "CYCLES" and "CYCLES" in engines:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 128
    else:
        sc.render.engine = next(e for e in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")
                                if e in engines)
        for attr, val in (("taa_render_samples", 64), ("use_bloom", True),
                          ("use_gtao", True), ("use_raytracing", True)):
            if hasattr(getattr(sc, "eevee", None), attr):
                setattr(sc.eevee, attr, val)

    if r.get("motion_blur"):
        sc.render.use_motion_blur = True
        if hasattr(sc.render, "motion_blur_shutter"):
            sc.render.motion_blur_shutter = 0.45

    if not os.environ.get('NOGLOW'):
        setup_glow(sc)

    sc.render.image_settings.file_format = "PNG"
    names = [v.identifier for v in
             sc.view_settings.bl_rna.properties["view_transform"].enum_items]
    sc.view_settings.view_transform = "AgX" if "AgX" in names else "Filmic"
    sc.view_settings.look = "AgX - Medium High Contrast" \
        if sc.view_settings.view_transform == "AgX" else "None"


def main():
    reset()
    build_lights()
    only = set(os.environ.get("ONLY", "").split(",")) - {""}
    want = lambda n: not only or n in only

    if want("titles"):
        build_titles()
    origin = px_to_world(CFG["button"]["rect_px"][0] + CFG["button"]["rect_px"][2] / 2,
                         CFG["button"]["rect_px"][1] + CFG["button"]["rect_px"][3] / 2)
    if want("page"):
        build_page()
    if want("button"):
        _, origin = build_button()
    if want("shadow"):
        build_shadow(origin)
    if want("shockwave"):
        build_shockwave(origin)
    if want("cursor"):
        build_cursor()
    if want("cards"):
        build_file_cards(origin)
    if want("agent"):
        build_scene_agent()
    if want("fleet"):
        build_scene_fleet()
    if want("share"):
        build_scene_share()
    if want("end"):
        build_end()
    build_camera()
    configure_render()

    sc = bpy.context.scene
    out = os.path.join(ROOT, CFG["render"]["out_dir"])

    if os.environ.get("PREVIEW"):
        sc.render.resolution_percentage = 40
        if hasattr(getattr(sc, "eevee", None), "taa_render_samples"):
            sc.eevee.taa_render_samples = 16
        for f in [int(x) for x in
                  os.environ.get("FRAMES", "20,70,115,150,200,240,300,340,400").split(",")]:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(out, "preview", f"f{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        print(f"[ok] preview -> {out}/preview")
    else:
        sc.render.resolution_percentage = 100
        sc.render.filepath = os.path.join(out, "frames", "f")
        # RANGE=a,b re-renderiza solo un tramo. Corregir un bug al final de un
        # anuncio de 32s no debería costar los 960 frames otra vez.
        if os.environ.get("RANGE"):
            a, b = (int(v) for v in os.environ["RANGE"].split(","))
            sc.frame_start, sc.frame_end = a, b
        bpy.ops.render.render(animation=True)
        print(f"[ok] frames {sc.frame_start}-{sc.frame_end} -> {out}/frames")

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))


main()
