# Sesión 01 — notas de producción

Video de 1–2 min explicando "El harness: anatomía de un agente" (sesión 01 del
Taller Sistemas Agénticos). Referente visual: las cheat sheets de ByteByteGo —
cada figura explica **un** concepto, sin adornos.

## Pendiente: cierre estilo meme del autobús

Al terminar los videos, hacer una imagen de cierre con la estructura del meme de
los dos pasajeros del autobús (el que mira su teléfono en la ventana gris vs. el
que mira el atardecer):

- **Lado gris** — "Sigue haciendo scroll" · "Sigue confundido" · "Sigue atrás"
- **Lado atardecer** — "Entiende cómo funciona por dentro" · "Construye el suyo"
  · "Modelos mentales claros"

Sirve como pieza de cierre compartible y como creativo suelto para redes. Ojo:
el original es de ByteByteGo, así que la composición se toma como referencia
—dos lados contrastados— pero el dibujo y el copy son propios.

## Ideas de dirección guardadas

**Recorrido de cámara entre diagramas.** Construir los cinco diagramas en un
mismo espacio 3D y que la cámara viaje entre ellos en vez de cortar. Con bloom y
paralaje se vería como un recorrido por una sala de diagramas flotantes, y
resolvería todas las transiciones del video de una sola vez.

Riesgo anotado: **puede volverse monótono** — si todas las transiciones son el
mismo vuelo lateral, el recurso se agota a la tercera. Si se usa, conviene variar
el tipo de desplazamiento en cada tránsito (acercarse, rodear, retroceder) o
combinarlo con otro recurso.

## Dirección visual (cerrada)

**Estilo**: monocromo luminoso sobre negro puro. Geometría 3D real, contorno
generado por Line Art, bloom fuerte. Los marcos son volúmenes que CONTIENEN su
texto — una caja sin texto dentro deja de ser un elemento y se vuelve adorno.

**La mezcla es la gramática**: el blanco 3D es la estructura, el color a mano es
la anotación. Así el color significa en vez de decorar.

**Aparición de elementos**: crecen con rebote (BACK/EASE_OUT) y sueltan un
destello. NO se dibujan trazo a trazo — a media animación un rectángulo
incompleto se lee como error. Lo que se anima es la geometría; Line Art la sigue.

### Gotchas verificados

| problema | causa | solución |
|---|---|---|
| las etiquetas hijas caían en el centro | `transform_apply(scale=True)` aplica TAMBIÉN la ubicación: los otros parámetros son `True` por defecto | `transform_apply(location=False, rotation=False, scale=True)` |
| "observa" salía "obser/a" | Arial Black y Arial Bold **mutilan la "v"** al convertir a Grease Pencil | Verdana Bold o Tahoma Bold |
| la caja de fuera borraba el interior | Line Art dibuja sólo lo visible | `use_multiple_levels`, `level_end=3` — pero con `0` en marcos de texto, o la arista trasera cruza la palabra |
| las mallas tapaban todo | material negro | material **transparente**: la malla existe para Line Art pero no se pinta |
| las líneas vibraban | `use_random` del ruido (line boil) | ruido estático; el boil sirve en trazo a mano, estorba en dibujo técnico |
| los elementos con `prof` se desbordaban | `k_prof` asume la cámara a `CAM_D` | asignar `lib.CAM_D` antes de crear objetos |
| la bola saltaba en las esquinas | recorría los extremos recortados de los tubos | recorrer los NODOS, con tiempo repartido **por longitud de tramo** |

## Vocabulario de transiciones

Decisión de dirección: **el video es una sola toma continua y las transiciones
son de primera clase**. Ninguna se repite — así el recurso no se agota, que era
el riesgo del recorrido de cámara.

| # | transición | qué dice | estado |
|---|---|---|---|
| 1 | **reorganización** — las cajas se recolocan de una figura a la siguiente | los conceptos son el mismo material visto de otra manera | probado (`anim_morph.py`) |
| 2 | **entrar** — la cámara se mete en un elemento y dentro está el siguiente diagrama | esto que era una caja tiene interior | por probar |
| 3 | **rotar / túnel** — anillos apilados: de lado son profundidad, de frente círculos concéntricos | el mismo objeto leído de dos maneras | probado (`anim_tunel.py`) — la más vistosa |
| 4 | **colapsar** — todo converge a un punto y del punto sale la figura nueva | reducción a la esencia | por probar |
| 5 | **des-dibujar** — el trazo se borra en reversa y desde el último punto nace el otro | continuidad de la mano que dibuja | Build con keyframes invertidos, por verificar |
| 6 | **alejarse** — lo que parecía el todo era una parte de algo mayor | cambio de escala conceptual | por probar |

La #5 es la más barata de probar: `percentage_factor` de 1 a 0 en vez de 0 a 1.

## Diagramas

`diagramas.py` genera seis bocetos para elegir cuál explica mejor antes de
invertir en animarlos:

| | idea |
|---|---|
| d1 | agente = modelo + harness; el modelo es la pieza pequeña |
| d2 | el loop piensa → actúa → observa; el modelo pide, el harness ejecuta |
| d3 | tres patrones: ReAct, Plan-and-Execute, Reflection |
| d4 | middleware y hooks: interceptar antes y después de cada llamada |
| d5 | la curva confiabilidad vs. agencia, y por qué se mueve |
| d6 | qué entra en cada llamada: la ventana de contexto como estado |

```bash
blender -b -P diagramas.py      # los seis -> out/d1..d6.png
D=3 blender -b -P diagramas.py  # sólo uno
```
