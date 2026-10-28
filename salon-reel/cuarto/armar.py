# Arma el salón de uñas «Uñas Karla» en Blender con muebles Kenney (CC0) y hornea la luz en una sola textura.
# Uso:
#   blender -b -P armar.py -- vista    → render rápido (verif/cuarto-vista.png) para revisar el acomodo
#   blender -b -P armar.py -- hornear  → hornea luz global + sombras a cuarto.png y exporta cuarto.glb
import bpy, sys, os, math
from mathutils import Vector, Matrix

MODO = sys.argv[sys.argv.index("--") + 1]
AQUI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.expanduser("~/fixter2025/videos/_shared/kenney/kenney_furniture-kit/Models/GLTF format")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

PELUCHE_RZ = float(os.environ.get("PELUCHE_RZ", -90))
PISO = 0.05  # alto de las tablas: todo lo demás se apoya encima
ANIM = {}  # piezas animadas en three: grupo → pivote en la base

def tono(mat, h, emite=0.0):
    # copia del material con otro color (cada mueble con su paleta); emite > 0 lo vuelve fuente de luz
    m = mat.copy()
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex2lin(h), 1)
    if emite:
        bsdf.inputs["Emission Color"].default_value = (*hex2lin(h), 1)
        bsdf.inputs["Emission Strength"].default_value = emite
    return m

def pieza(nombre, x, y, rz=0, z=0, s=1.0, colores=None, luz=None, anim=None, solo=None):
    # anim: nombre del grupo de vértices que sobrevive al join; después del horneado se separa como objeto
    # propio (three lo anima). solo: limita el grupo a las caras de esos materiales (pantalla, pantalla de lámpara)
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f"{KIT}/{nombre}.glb")
    nuevos = [o for o in bpy.data.objects if o not in antes]
    raiz = [o for o in nuevos if o.parent is None]
    for o in nuevos:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            nm = slot.material.name.split(".")[0] if slot.material else ""
            if colores and nm in colores:
                slot.material = tono(slot.material, colores[nm])
            if luz and nm in luz:
                slot.material = tono(slot.material, luz[nm][0], luz[nm][1])
    if anim:
        for o in nuevos:
            if o.type != "MESH":
                continue
            vs = set()
            for poly in o.data.polygons:
                mat = o.material_slots[poly.material_index].material if o.material_slots else None
                nm = mat.name.split(".")[0] if mat else ""
                if solo is None or nm in solo:
                    vs.update(poly.vertices)
            if vs:
                o.vertex_groups.new(name=anim).add(list(vs), 1.0, "REPLACE")
                ANIM[anim] = solo is None  # True = pivote en la base (plantas); False = centro
    for o in raiz:
        o.location = (x, y, z + (0 if nombre == "floorFull" else PISO))
        o.rotation_mode = "XYZ"
        o.rotation_euler = (0, 0, math.radians(rz))
        o.scale = (s, s, s)
    return nuevos

def material(nombre, color, rough=0.8):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

def hex2lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)

def caja(nombre, dims, loc, rot, mat, padre=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = nombre; o.scale = dims; o.rotation_euler = rot
    bev = o.modifiers.new("bisel", "BEVEL"); bev.width = min(dims) * 0.25; bev.segments = 2
    o.data.materials.append(mat)
    if padre: o.parent = padre
    return o

def libro(x, y, z, rz, color, abierto=False):
    # libro hecho a mano (el kit sólo trae hileras): pasta de color y hojas blancas; abierto = dos mitades en V
    pasta = material("pasta" + color, hex2lin(color), 0.7)
    hojas = material("hojas", hex2lin("#FBF7EE"), 0.9)
    eje = bpy.data.objects.new("libro", None); scene.collection.objects.link(eje)
    eje.location = (x, y, z); eje.rotation_euler = (0, 0, math.radians(rz))
    if not abierto:
        caja("pasta", (0.15, 0.105, 0.022), (0, 0, 0.011), (0, 0, 0), pasta, eje)
        caja("hojas", (0.142, 0.097, 0.024), (0.004, 0, 0.011), (0, 0, 0), hojas, eje)
        return
    for lado in (-1, 1):
        a = math.radians(7) * lado  # cada mitad se levanta un poco desde el lomo
        cx = lado * 0.052
        caja("pasta", (0.105, 0.15, 0.006), (cx, 0, 0.003 + 0.004), (0, -a, 0), pasta, eje)
        caja("hojas", (0.098, 0.142, 0.012), (cx, 0, 0.012 + 0.004), (0, -a, 0), hojas, eje)

def peluche(x, y, z, rz, alto):
    # «Bear» de jiang liu (Poly Pizza, CC-BY 3.0): osito low poly sentado con moñito rojo. Viene en
    # unidades enormes y en varias piezas: se une, se apoya en su base, se centra y se escala a `alto` m.
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.expanduser("~/fixter2025/videos/_shared/peluche/teddy-jiangliu.glb"))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    mallas = [o for o in nuevos if o.type == "MESH"]
    for o in mallas:
        o.data = o.data.copy()
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4)
    for o in nuevos:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in mallas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mallas[0]
    bpy.ops.object.join()
    oso = bpy.context.object
    vs = [v.co for v in oso.data.vertices]
    mn = Vector([min(c[k] for c in vs) for k in range(3)]); mx = Vector([max(c[k] for c in vs) for k in range(3)])
    k = alto / (mx.z - mn.z)
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    oso.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation(-off))
    # su mapa UV se llama como el de Kenney: al unir todo, su textura sigue leyendo su propio UV
    kenney_uv = next(o.data.uv_layers[0].name for o in bpy.data.objects if o.type == "MESH" and o is not oso and o.data.uv_layers)
    if oso.data.uv_layers:
        oso.data.uv_layers[0].name = kenney_uv
    oso.location = (x, y, z + PISO)
    oso.rotation_mode = "XYZ"  # el importador de glTF lo deja en cuaternión
    oso.rotation_euler = (0, 0, math.radians(rz))
    oso.name = "peluche"
    return oso

def botella(x, y, z, color, alto=0.06):
    # frasco de esmalte: cuerpo de vidrio de color con bisel y tapa negra alta (el kit no trae)
    cuerpo = material("esmalte" + color, hex2lin(color), 0.25)
    tapa = material("tapa", hex2lin("#2A2A33"), 0.4)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.022, depth=alto, location=(x, y, z + alto / 2))
    o = bpy.context.object; o.data.materials.append(cuerpo)
    bev = o.modifiers.new("bisel", "BEVEL"); bev.width = 0.006; bev.segments = 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.011, depth=0.045, location=(x, y, z + alto + 0.0225))
    o = bpy.context.object; o.data.materials.append(tapa)
    bev = o.modifiers.new("bisel", "BEVEL"); bev.width = 0.003; bev.segments = 2

def repisas(objs, minarea=0.02):
    # alturas de las caras que miran hacia arriba (las tablas del librero), de abajo a arriba
    bpy.context.view_layer.update()
    zs = {}
    for o in objs:
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        for p in o.data.polygons:
            n = (mw.to_3x3() @ p.normal).normalized()
            if n.z > 0.95:
                z = round((mw @ p.center).z, 3)
                zs[z] = zs.get(z, 0) + p.area * (mw.to_scale().x ** 2)
    return sorted(z for z, a in zs.items() if a > minarea)

ESM = ["#F39A86", "#E76F8A", "#B8B2F2", "#8483E0", "#85DDCB", "#F7C873", "#F2A7C3", "#E4544F"]

# --- el piso: tablas Kenney 2×2 sobre una losa gruesa (la orilla se ve: es un diorama) ---
L = 2.0
for i in range(2):
    for j in range(2):
        pieza("floorFull", -1 + i, -1 + j, colores={"wood": "#EDC79C"})
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.1))
losa = bpy.context.object
losa.name = "losa"
losa.scale = (L + 0.03, L + 0.03, 0.2)
bev = losa.modifiers.new("bisel", "BEVEL"); bev.width = 0.025; bev.segments = 3
losa.data.materials.append(material("losa", hex2lin("#B9825A")))

# Kenney: cada pieza crece desde su origen hacia +x/+y y su frente mira a -y. La cámara entra por la
# esquina -x/-y: los muros van al fondo (+y) y a la derecha (+x), y nunca tapan la toma.
MURO = {"_defaultMat": "#ECE4FA", "wood": "#FFF6EE", "metalDark": "#ECE4FA"}
pieza("wallWindow", -1, 0.95, colores={**MURO, "glass": "#9FB6F2"})
pieza("wallDoorway", 0, 0.95, colores=MURO)          # la puerta de la calle (ahí cuelga CERRADO)
# muro derecho: 3 mm más alto para que su canto no pelee con el del fondo en la esquina
pieza("wall", 1.0, -1.05, rz=90, z=0.003, colores=MURO)
pieza("wall", 1.0, -0.05, rz=90, z=0.003, colores=MURO)

pieza("rugRound", -0.05, 0.05, colores={"carpet": "#A9DDCF", "carpetDarker": "#86C9B6"})
# --- la estación de manicure, al centro: mesa, silla de la clienta (adelante) y de Karla (atrás) ---
pieza("table", -0.35, 0.05, colores={"wood": "#FFF6EE"})
pieza("chairCushion", 0.15, 0.0, rz=180, colores={"carpet": "#F39A86", "wood": "#C98F5F"})
pieza("chairCushion", -0.1, 0.55, colores={"carpet": "#B8B2F2", "wood": "#C98F5F"})
MESA = 0.327 + PISO
# lámpara UV de uñas: arco blanco con base, la luz por dentro (lila tenue)
uvb = material("uv", hex2lin("#FFFFFF"), 0.35)
uvl = material("uvluz", hex2lin("#C9B8FF"), 0.5)
uvl.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (*hex2lin("#C9B8FF"), 1)
uvl.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.5
caja("uvbase", (0.2, 0.15, 0.02), (-0.2, 0.3, MESA + 0.01), (0, 0, 0), uvb)
caja("uvtecho", (0.2, 0.15, 0.025), (-0.2, 0.3, MESA + 0.11), (0, 0, 0), uvb)
caja("uvatras", (0.2, 0.025, 0.1), (-0.2, 0.365, MESA + 0.06), (0, 0, 0), uvb)
caja("uvled", (0.16, 0.11, 0.006), (-0.2, 0.3, MESA + 0.096), (0, 0, 0), uvl)
# frascos sobre la mesa y una toallita
for k, c in enumerate(["#E4544F", "#F2A7C3", "#8483E0"]):
    botella(0.18 + k * 0.06, 0.38, MESA, c)
caja("toalla", (0.16, 0.12, 0.012), (0.08, 0.18, MESA + 0.006), (0, 0, math.radians(8)), material("toalla", hex2lin("#FFFFFF"), 0.95))

# --- repisa de esmaltes en el muro derecho, viendo hacia adentro (-x) ---
rep = pieza("bookcaseOpen", 0.7, -0.35, rz=-90, colores={"wood": "#FFF6EE"})
niveles = repisas(rep)
print("REPISAS", niveles)
for n, z in enumerate(niveles):
    for k in range(5):
        botella(0.8, -0.7 + k * 0.075, z, ESM[(k + n * 3) % len(ESM)])
# espejo del tocador en el muro derecho, al fondo
pieza("bathroomMirror", 0.9, 0.58, z=0.5, rz=-90)
pieza("pottedPlant", 0.84, 0.76, colores={"plant": "#5DBB7A"}, anim="anim_pottedPlant")

# --- sala de espera en la orilla izquierda: sillón viendo hacia adentro (+x) ---
pieza("loungeSofa", -0.55, -0.02, rz=90, colores={"carpet": "#B8B2F2", "wood": "#C98F5F"})
pieza("pillowBlue", -0.86, 0.62, z=0.2, rz=90)

# --- recepción adelante a la izquierda, volteada (la pantalla mira hacia Ghosty, que flota detrás) ---
pieza("desk", -0.2, -0.45, rz=180, colores={"wood": "#FFF6EE", "metal": "#5B6172"})
pieza("laptop", -0.35, -0.48, z=0.384, rz=180, s=0.7)
pieza("lampRoundTable", -0.78, -0.62, z=0.384, rz=180, luz={"lamp": ("#FFE3A3", 3.0)}, anim="anim_lampRoundTable_shade", solo={"lamp"})
pieza("plantSmall1", -0.27, -0.66, z=0.384, anim="anim_plantSmall1")
# --- luz de noche: cielo lila oscuro, luna fría por la ventana, lámparas cálidas encendidas ---
mundo = bpy.data.worlds.new("cielo"); scene.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (*hex2lin("#8E86D8"), 1)
mundo.node_tree.nodes["Background"].inputs["Strength"].default_value = float(os.environ.get("CIELO", 0.55))
sol = bpy.data.lights.new("luna", "SUN"); sol.energy = float(os.environ.get("LUNA", 1.3)); sol.angle = math.radians(8)
sol.color = hex2lin("#D7DCFF")
so = bpy.data.objects.new("luna", sol); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(8), math.radians(-35))
rel = bpy.data.lights.new("relleno", "AREA"); rel.energy = 90; rel.size = 3; rel.color = hex2lin("#C9C2FF")
ro = bpy.data.objects.new("relleno", rel); scene.collection.objects.link(ro)
ro.location = (-3, -3, 3); ro.rotation_euler = (math.radians(55), 0, math.radians(-45))
# focos cálidos: la lámpara de recepción y la luz de la mesa de manicure
for nombre, loc, w in (("foco_recepcion", (-0.72, -0.62, 0.95), 18), ("foco_mesa", (0.05, 0.28, 1.15), 22)):
    pl = bpy.data.lights.new(nombre, "POINT"); pl.energy = w; pl.color = hex2lin("#FFD9A0"); pl.shadow_soft_size = 0.25
    po = bpy.data.objects.new(nombre, pl); scene.collection.objects.link(po); po.location = loc
scene.render.engine = "CYCLES"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.cycles.device = "GPU"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = True

if MODO == "vista":
    cam = bpy.data.cameras.new("cam"); cam.lens = 50
    co = bpy.data.objects.new("cam", cam); scene.collection.objects.link(co)
    # «vista sofa»: acercamiento al sillón para revisar el peluche
    sofa = sys.argv[-1] == "sofa"
    co.location = (-0.6, -1.1, 0.75) if sofa else (-3.6, -3.6, 3.0)
    direc = (Vector((0.7, -0.12, 0.35)) if sofa else Vector((0, 0.1, 0.25))) - co.location
    co.rotation_euler = direc.to_track_quat("-Z", "Y").to_euler()
    scene.camera = co
    scene.render.resolution_x, scene.render.resolution_y = 900, 900
    scene.cycles.samples = 64
    scene.render.filepath = os.path.join(AQUI, "../verif/cuarto-vista.png")
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

# --- hornear: todo en una malla, segundo UV de lightmap, luz combinada a una textura ---
mallas = [o for o in bpy.data.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in mallas:
    o.select_set(True)
bpy.context.view_layer.objects.active = mallas[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.convert(target="MESH")  # aplica el bisel
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
cuarto = bpy.context.object
cuarto.name = "cuarto"
uv = cuarto.data.uv_layers.new(name="luz")
cuarto.data.uv_layers.active = uv
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")

RES = 4096
img = bpy.data.images.new("cuarto", RES, RES)
for slot in cuarto.material_slots:
    nt = slot.material.node_tree
    n = nt.nodes.new("ShaderNodeTexImage"); n.image = img
    u = nt.nodes.new("ShaderNodeUVMap"); u.uv_map = "luz"
    nt.links.new(u.outputs["UV"], n.inputs["Vector"])
    nt.nodes.active = n
scene.cycles.samples = 768
scene.cycles.use_denoising = False
scene.render.bake.margin = 8
bpy.ops.object.bake(type="COMBINED")
img.filepath_raw = os.path.join(AQUI, "cuarto.png"); img.file_format = "PNG"; img.save()

# material final: sólo la textura horneada, en el UV de luz (three la pinta sin luces)
for slot in cuarto.material_slots:
    pass
horneado = bpy.data.materials.new("horneado"); horneado.use_nodes = True
nt = horneado.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeBsdfPrincipled")
tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "luz"
nt.links.new(uvn.outputs["UV"], tx.inputs["Vector"])
nt.links.new(tx.outputs["Color"], em.inputs["Base Color"])
nt.links.new(em.outputs["BSDF"], out.inputs["Surface"])
cuarto.data.materials.clear()
cuarto.data.materials.append(horneado)
# el glb sólo lleva el UV de luz
while len(cuarto.data.uv_layers) > 1:
    for l in cuarto.data.uv_layers:
        if l.name != "luz":
            cuarto.data.uv_layers.remove(l)
            break
# piezas animadas: cada grupo se separa como objeto propio (conserva su UV de luz y la textura horneada)
# con el origen en su pivote: base de la maceta para las plantas, centro para pantalla y lámparas
sueltos = [cuarto]
for g, base in ANIM.items():
    bpy.ops.object.select_all(action="DESELECT")
    cuarto.select_set(True); bpy.context.view_layer.objects.active = cuarto
    cuarto.vertex_groups.active_index = cuarto.vertex_groups[g].index
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    nuevo = [o for o in bpy.context.selected_objects if o is not cuarto][0]
    nuevo.name = g
    ws = [nuevo.matrix_world @ v.co for v in nuevo.data.vertices]
    lo = Vector([min(w[i] for w in ws) for i in range(3)]); hi = Vector([max(w[i] for w in ws) for i in range(3)])
    piv = (lo + hi) / 2
    if base:
        piv.z = lo.z
    bpy.ops.object.select_all(action="DESELECT")
    nuevo.select_set(True); bpy.context.view_layer.objects.active = nuevo
    scene.cursor.location = piv
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    nuevo.vertex_groups.clear()
    sueltos.append(nuevo)
    print("SEPARADO", g, len(nuevo.data.vertices), tuple(round(c, 3) for c in piv))
cuarto.vertex_groups.clear()
bpy.ops.object.select_all(action="DESELECT")
for o in sueltos:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(AQUI, "cuarto.glb"), use_selection=True, export_format="GLB", export_image_format="NONE")
print("HORNEADO OK")
