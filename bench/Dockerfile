# Banco de pruebas efímero: ¿puede EEVEE renderizar sin GPU?
#
# Todo vive dentro de la imagen. Nada se instala en el host: se construye, se
# corre, se borra. Y un contenedor se parece mucho más a una microVM que el host
# pelado — medir en el host daría un número optimista que luego no se cumple.
FROM debian:12-slim

# mesa-vulkan-drivers trae lavapipe (ICD Vulkan por software). Es la pieza que
# decide todo: sin ella EEVEE no encuentra contexto y ni arranca.
RUN apt-get update && apt-get install -y --no-install-recommends \
      mesa-vulkan-drivers vulkan-tools \
      libgl1 libxi6 libxxf86vm1 libxfixes3 libxrender1 libsm6 \
      libxkbcommon0 libx11-6 libxext6 libxcb1 libwayland-client0 \
      libegl1 libgomp1 xz-utils curl ca-certificates bc python3 \
 && rm -rf /var/lib/apt/lists/*

ARG BLENDER_VERSION=5.2.0
ARG BLENDER_SERIES=5.2
RUN curl -fsSL "https://download.blender.org/release/Blender${BLENDER_SERIES}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
      | tar -xJ -C /opt \
 && ln -s "/opt/blender-${BLENDER_VERSION}-linux-x64/blender" /usr/local/bin/blender

# Vulkan por software, sin display.
ENV VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json \
    LIBGL_ALWAYS_SOFTWARE=1 \
    BLENDER_GPU_BACKEND=VULKAN

WORKDIR /work
ENTRYPOINT ["bash", "/work/bench/lavapipe.sh"]
