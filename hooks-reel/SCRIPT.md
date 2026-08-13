# Guion de narración — voz `em_santa` (Kokoro, es), velocidad 0.92

> Anglicismos fonéticos en el input del TTS: "hooks" → **juks**, "tools" →
> **tuls**, "FixterGeek" → **fixterguic**, "harness" → **járnes**.
> Las marcas `[pausa]` no se narran: el sintetizador corta ahí y se empalma
> silencio.
>
> Los nombres de framework (LangGraph, OpenAI Agents SDK, PreToolUse) aparecen
> **en pantalla**, no se deletrean en la narración.

Duración objetivo: ~120s. Tres escenas de ~40s.

---

## s1-la-apuesta  (0:00 – 0:40)

Tu agente tiene una regla. La escribiste tú, en el system prompt, con mayúsculas
y todo: nunca borres archivos sin confirmar.

Y casi siempre la respeta.

Casi.

Porque esa regla le llega al modelo como una sugerencia muy bien redactada. La
lee, la considera, y luego decide.

Digamos que se le pasa una de cada cien veces. Un contexto largo, una
instrucción que la contradice a medias, un día raro del modelo.

Parece poco. Pero tu agente corre mil veces al día. Son diez veces cada día en
las que tu regla no existió.

Y una sola de esas diez alcanza para borrar lo que no se podía borrar.

## s2-la-compuerta  (0:40 – 1:22)

Aquí es donde entra el hook.

Es código tuyo que el sistema ejecuta en un punto fijo del ciclo. Antes de usar
una herramienta, después de una respuesta, al terminar la sesión. Tú eliges el
punto y tú escribes el código.

Y la parte que importa: se ejecuta siempre.

El modelo no lo llama, no lo puede saltar, no lo puede evitar. Cuando el agente
quiere correr un comando, esa compuerta lo ve primero. Si el comando no pasa tu
regla, devuelve error y el comando nunca sucede.

Aquí conviene separar dos palabras que se usan como si fueran la misma. El punto
del ciclo donde corre tu código es el hook: el lugar. La regla que escribes
dentro es el guardrail: la política.

Y como son cosas distintas, la misma política se puede colgar de herramientas
que le ponen otro nombre a ese lugar.

Fíjate en lo que cambió. La regla dejó de vivir en un párrafo que el modelo
interpreta, y pasó a vivir en una condición que se cumple o no se cumple.

Una condición la puedes probar. La puedes versionar. Puedes dormir con ella
corriendo en producción.

## s3-la-primitiva  (1:22 – 2:00)

Y esto no es una peculiaridad de una sola herramienta.

Cada quien le puso un nombre distinto. Los tienes en pantalla, y los tres
apuntan al mismo lugar del ciclo: donde metes control que no depende de que el
modelo coopere.

Cuando evalúes una herramienta para construir agentes, busca ese punto. Si no lo
tiene, tu única política de seguridad es la buena fe.

[pausa]

En el correo te dejo el código del guardrail escrito para tres arneses
diferentes, listos para copiar.

> "guardrail" se sintetiza como **gardréil**. Si suena mal, se cambia por
> "guardia" — la frase aguanta el reemplazo sin tocar el resto.

[pausa]

Fixter Geek.
