# Ghosty Ads — «El colador» (anuncio click-to-Messenger)

workflow: general-video · 1080×1920 · ~44 s · es-MX · voz em_santa (Kokoro) · piel ghosty.studio (fondo claro #f4f5fb, lila #9a99ea/#8483e0, Poppins/Inter) con acabado de caricatura plana: objetos SVG a mano con contorno de tinta #191a20, rellenos sólidos, sombra dura `8px 8px 0` en lila claro. Sin gradientes, blur ni glow. Ghosty = `assets/ghosty.png` (bajado de https://formmy.app/logo.png, sin rotar ni repintar, nunca sobre bloque morado).

**Estado: aprobado y entregado en renders/final.mp4 (53.4 s), música A.**

## Storytelling (3 renglones)

- **Abre:** «Pagas un anuncio y te escriben treinta y siete. ¿Cuántos de verdad compran?»
- **Cierra:** «Tú sólo hablas con los que sí compran.»
- **Se lleva:** Ghosty contesta a cada persona que llega de tu anuncio de Messenger, al instante y a cualquier hora; despide a los curiosos, cotiza y agenda a los que sí, y te manda el reporte a las 9:00 y a las 21:00.
- **Circular:** el mismo celular. Al abrir, globo rojo **37** y una pila de mensajes sin contestar. Al cerrar vuelve ese celular: la pila gris se cae y quedan **3** tarjetas doradas con globo dorado **3**.

## Composición (distinta de «La madrugada»)

La madrugada era un celular fijo al centro con título arriba a la izquierda y fondo de puntos. Aquí la pantalla es un **flujo vertical** que baja: anuncio arriba → Ghosty con su **colador** a media altura → compradores abajo. El fondo es una malla de rombos lila. El celular entra de lado, inclinado y cambiando de tamaño en cada escena; nunca queda fijo al centro. Los títulos van en y 262–440; subtítulo karaoke en pastilla de tinta, y 1262–1380, x 60–920 (fuera de las zonas que tapa TikTok).

## Guion por beats

| t (s) | Se ve | Voz (literal) |
|---|---|---|
| 0.0–4.8 | **Fotograma 0 completo** (SF1): anuncio «Pastelería Lulú» con pastel y botón «Enviar mensaje»; celular inclinado con 6 notificaciones y globo rojo 37; chip «21:47 · cerrando caja». Movimiento: salen burbujas del botón y vuelan al celular, el contador sube 34→37 con rebote y el celular vibra 3 veces. | Pagas un anuncio y te escriben treinta y siete. ¿Cuántos de verdad compran? |
| 4.8–5.5 | Cortinilla 1: rebanadas sesgadas lila/ámbar/menta con `back.out`; un logo de Messenger gigante sella el corte al centro y tapa las 4 esquinas. | — |
| 5.5–11.0 | Ghosty entra desde abajo; las burbujas caen del anuncio hacia él y él regresa globos lila. Cronómetro SVG que se detiene en «0:02» y chip 24/7 (sol y luna girando). | Ghosty le contesta a cada uno al instante, en Messenger, de día y de noche. |
| 11.0–18.0 | Chat en primer plano: «¿Para cuándo y cuántos?» → «2 pasteles, sábado» → llega la cotización PDF (documento SVG) → calendario con palomita «Cita sáb 10:00». El chat se dobla en tarjeta y cae en la columna «Cotizado» del tablero. | Le pregunta lo que falta, le cotiza en PDF, le agenda la cita y te lo deja en tu tablero. |
| 18.0–18.7 | Cortinilla 2: máscara tipográfica «FILTRO» que se abre sobre una palomita gigante. | — |
| 18.7–27.0 | **El colador** (SF2): burbujas grises («asdfgh», «¿eres bot? jaja», «hola hola hola») rebotan en el colador; la dorada «Quiero 2 pasteles p/ sábado» pasa y cae como tarjeta «Compradora». Ghosty contesta «Veo que por ahora no es lo que buscas. ¡Aquí estaré!» y un sello marca «Conversación cerrada». Tarjeta de Beto: el correo se tacha y ondea una bandera roja «Correo no válido». | A los curiosos los despide con amabilidad y deja de gastar en ellos. Y si el correo o el teléfono es falso, te lo marca. |
| 27.0–27.7 | Cortinilla 3: zoom-punch; una luna gigante gira y se vuelve sol. | — |
| 27.7–34.0 | **El reporte** (SF3): el despertador corre de 9:00 a 21:00 y los chips de sol y luna se turnan; en la pantalla bloqueada «21:00» cae el push «Ghosty · Reporte de la noche» (12 escribieron · 3 compran · 1 alerta) y aparecen sus 3 renglones. | Y a las nueve de la mañana y a las nueve de la noche te manda el reporte: quién escribió, qué busca y qué sigue. (Kokoro leía «quiere» como «quiera») |
| 34.0–37.5 | **Cierre circular**: vuelve el celular del inicio con el 37; las notificaciones grises se caen y quedan 3 doradas; el globo se vuelve dorado y marca 3. | Tú sólo hablas con los que sí compran. |
| 37.5–44.0 | **CTA** (SF4): tarjeta «Tu tablero gratis, con tu marca», botón Messenger «Escríbenos», `ghosty.studio/messenger`, sello «Hasta el 31 de octubre»; se abre la caja de regalo SVG; wordmark de Ghosty. Termina lleno, sin fundido a negro. | Escríbenos por Messenger y te armamos tu tablero gratis, con tu marca. Hasta el treinta y uno de octubre. |

Karaoke: una línea a la vez, 72 px; se parte en puntuación o en pausas de más de 0.6 s. La palabra actual va en lila #aeadef, las dichas en blanco y las pendientes en gris. La transcripción se hace **del clip**: `npx hyperframes transcribe <wav> -m large-v3 -l es --json`. Cada destacado (37, PDF, cita, correo falso, 9:00/21:00, 3, fecha) se enciende cuando la voz lo nombra.

## SFX por animación (catálogo CC0 `docs/shorts-taller/sfx/`, al 0.7; nunca el mismo dos veces seguidas)

| t aprox | Animación | SFX |
|---|---|---|
| 0.4 / 0.8 / 1.2 | burbujas salen del botón | pop → 8bit-blip → pop |
| 1.5–2.3 | contador 34→37 con rebote | tick ×3 (impacto del back.out en 1/(s+1)) |
| 2.6 | celular vibra | hit-low |
| 4.8–5.5 | cortinilla rebanadas + glifo Messenger | whoosh-fly (lo que dura el barrido) + stamp al sellar |
| 6.0 | Ghosty entra | bean |
| 6.8 / 7.6 / 8.4 | globos de respuesta | whoosh-short → pop → whoosh-short |
| 9.6 | cronómetro se detiene en 0:02 | ding |
| 12.0 / 13.2 | pregunta / respuesta | pop → tick |
| 14.3 | llega el PDF | paper |
| 15.6 | calendario, palomita | pin |
| 16.8–17.6 | chat se dobla y cae en «Cotizado» | card → land |
| 18.0–18.7 | cortinilla máscara «FILTRO» | riser → hit-sub |
| 19.5 / 20.2 / 20.9 | burbujas grises rebotan en el colador | block → bean → block |
| 21.8 | la dorada pasa | coin |
| 23.6 | sello «Conversación cerrada» | stamp |
| 25.4 | correo tachado + bandera | 8bit-hack → turn |
| 27.0–27.7 | zoom-punch luna→sol | whoosh-fly → hit-low |
| 28.2–29.4 | manecillas 9:00→21:00 | tick (carrete corto) |
| 30.2 | cae el push | ding |
| 31.0 / 31.8 / 32.6 | renglones del reporte | 8bit-blip → tick → 8bit-blip |
| 34.4 | pila gris se cae | land |
| 35.2 | globo 37→3 dorado | coin |
| 38.2 | caja de regalo se abre | pop |
| 40.0 | botón «Escríbenos» late | 8bit-pickup |
| 42.4 | sello de la fecha | stamp |

## Cama musical: 3 candidatas (Openverse → Jamendo, instrumentales, ninguna en `usadas.json`)

Las tres son funk/disco con buen ánimo, en la línea de lo que le gustó a Brenda. Están en `assets/bgm/` (fuera del repo) y todavía **no se han escuchado**: la elección es de oído y luego se mide. La ganadora se registra con `registrar-bgm.mjs`, y su levantada se alinea al cierre (34 s).

| | Pista | Autor | Licencia | BPM · RMS · punch | Por qué |
|---|---|---|---|---|---|
| A | Funk in my Pocket (`cand-A.mp3`) | OptiKill | CC BY 3.0 · jamendo.com/track/1715120 | ~125 (medido 62.5 a medio tiempo) · 0.241 · 11.3 | funk de bolsillo, RMS moderado; cabe bajo la voz sin pelear |
| B | Disco stew (`cand-B.mp3`) | Ehma | CC BY 3.0 · jamendo.com/track/1897164 | ~121 (medido 60.5) · 0.274 · 12.6 | disco con bajo marcado, mismo pulso que «Funky WahWah» sin ser la misma |
| C | Vintage (25th Anniversary Edition) (`cand-C.mp3`) | Daniel Bautista | CC BY 3.0 · jamendo.com/track/1547983 | 104 · 0.343 · 19.3 | la de más golpe; BPM bajo con empuje, como «High hopes». Va a −26 LUFS con sidechain |

Crédito (según la que gane): `Música: "<título>" de <autor> — CC BY 3.0`.

## Pipeline al aprobar

Se reutiliza `../ghosty-madrugada/`: `score.mjs` → `score.gen.json` → `sfx.py` → `mix.sh`. Voz −15 LUFS; cama −26 LUFS con `sidechaincompress` cuya llave es la voz sola; `apad=whole_dur` y ganancia fija + `alimiter`. Se verifica sobre el archivo entregado: frame 0, `blackdetect`, `start_time`=0, transcripción por ventana contra este guion y las cortinillas tapando las 4 esquinas.

Style frames: `styleframes/sf1.png` (0 s), `sf2.png` (~20 s), `sf3.png` (~30 s), `sf4.png` (~40 s), `contacto.png`, fuente en `styleframes/frames.html`.
