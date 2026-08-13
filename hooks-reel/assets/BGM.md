# Cama musical

**Una pista por escena**, cortada justo en la transición. Todas de Mixkit,
recortadas al largo exacto de su escena, con fade de 1.2s a la entrada y a la
salida, y normalizadas a −20 LUFS para que quepan debajo de la narración.

| Archivo | Fuente | Largo | BPM | Volumen |
| --- | --- | --- | --- | --- |
| `bgm-s1.mp3` | [mixkit 527](https://assets.mixkit.co/music/527/527.mp3), desde 0:10 | 36s | ~117 | 0.13 |
| `bgm-s2.mp3` | [mixkit 155](https://assets.mixkit.co/music/155/155.mp3), desde 0:12 | 63s | ~161 | 0.11 |
| `bgm-s3.mp3` | [mixkit 899](https://assets.mixkit.co/music/899/899.mp3), desde 0:06 | 31s | ~117 | 0.13 |

La escena 2 lleva la más rápida: es la del mecanismo. La 3 cierra con fade
largo de 5s desde el segundo 26.

## Cómo se eligieron

Se descargaron ~37 candidatas de `assets.mixkit.co/music/<id>/<id>.mp3` y se
midieron con un script de tempo y energía (autocorrelación sobre el flujo de
onsets): BPM, RMS y "punch" (qué tan marcado es el golpe). Se buscó **movida**:
BPM alto y punch alto, con RMS moderado para no tapar la voz. La cama del video
anterior (mixkit 593) resultó ser la más suave del lote — por eso no servía aquí.

Licencia Mixkit: uso comercial libre, sin atribución. No se puede redistribuir
la pista por separado.

Es la misma pista que cierra `videos/contexto-escritorio`, así que los dos
videos de la secuencia comparten cama musical.
