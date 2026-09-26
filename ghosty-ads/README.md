# Ghosty Ads · El colador

Short vertical (9:16, 63.6 s) que vende Ghosty Ads. En línea en `ventas.ghosty.studio/#ads` y en la galería (`assets/shorts/ghosty-ads.mp4`).

**Versión vigente: `v2.1/`.** Contiene:
- el acto «Ghosty te arma la campaña»: creativo, copy, segmentación y presupuesto, con la campaña en pausa hasta que se prende;
- la escena de comentarios en el anuncio;
- las cifras dichas de corrido («treintaisiete», «treintaiuno»).

`v1` (la raíz) y `v2/` se conservan como historial.

## ⏰ Actualizar después del 31 de octubre de 2026
El CTA dice «te armamos tu primera campaña… **hasta el treintaiuno de octubre**». Después de esa fecha:
1. Cambiar la fecha o quitarla:
   - en `v2.1/voice/lines.tsv`, la línea `ctaC`;
   - en el texto en pantalla de `v2.1/index.html`, que muestra «31 de octubre».
2. Regenerar solo esa voz con em_santa y escucharla. Las cifras se escriben como una palabra fonética (`treintaiuno`); si no, Kokoro las parte.
3. `mix.sh`: la cama sale de `BGM.md`, que tiene el desfase para que el golpe de la pista (60.64 s) caiga en «Tú sólo hablas con los que sí compran». Si cambia la duración, hay que recalcularlo.
4. Verificar sobre el mp4 entregado:
   - fotograma 0 completo;
   - `start_time` en 0;
   - `blackdetect`;
   - transcribir por ventana;
   - los recortes de palomitas en `verif/`.
5. Reemplazar `assets/shorts/ghosty-ads.mp4` en esta galería y el video de la landing, que se carga desde aquí.

## Lo que no está versionado
- **Los mp3 de música:** son CC BY y la regla es no subirlos. La pista es «Funk in my Pocket» de OptiKill (CC BY 3.0) y su fuente está en `BGM.md`.
- **Los renders mp4 y `sfx.wav`:** se regeneran. El final publicado está en `assets/shorts/`.

Música: «Funk in my Pocket» de OptiKill · CC BY 3.0
