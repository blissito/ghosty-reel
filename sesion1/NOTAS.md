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
