# LocalForgeLLM

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <strong>Español</strong>
</p>

**Modelos más grandes en el hardware que ya tienes.** LocalForgeLLM es un framework con el que tu agente de programación construye y optimiza un entorno local de IA. Indica una tarea y, si quieres, un modelo MoE; el agente adapta el modelo, motor, cuantización y parámetros de inicio a tu hardware. El resultado sirve para chat local, visión y agentes de programación.

**Tecnologías:** agentes de programación con IA · documentación de modelos y motores · Python / Bash · motores de inferencia como [llama.cpp](https://github.com/ggml-org/llama.cpp) · backends de CPU / GPU · API HTTP local.

## Instalación

**Necesitas:** un agente de programación con acceso al terminal y espacio para el modelo elegido. El agente selecciona las dependencias y los ajustes de memoria para tu equipo.

1. Abre este repositorio en tu agente de programación y pídele que lea [AGENTS.md](AGENTS.md) y [SKILL.md](SKILL.md).
2. Describe la tarea, el tamaño de contexto deseado y el presupuesto de RAM/VRAM. Indica un modelo o deja que el agente lo elija.
3. Pídele que siga la documentación del framework para instalar el motor, ajustar el modelo y guardar un perfil de inicio funcional.

Como punto de partida concreto, consulta nuestros [ejemplos de inicio de Qwen y Gemma](docs/README.es.md#instalación).

## Cómo funciona

El agente examina tu hardware y la documentación de los modelos, elige un modelo adecuado, un motor y un formato de pesos compatibles, y ajusta la distribución CPU/GPU, el contexto, la caché y los lotes. Ejecuta tu tarea, mide la velocidad y el uso de memoria, afina los parámetros y guarda el mejor perfil funcional. El mismo ciclo sirve para distintas familias MoE y métodos de cuantización.

![A partir de la tarea y el hardware, el agente selecciona el motor, ajusta el modelo, mide los resultados y refina los parámetros hasta guardar un perfil local reutilizable.](docs/assets/how-it-works.svg)

## Ejemplos en una RTX 4060

Ryzen 5 5600 · 32 GB de RAM · 8 GB de VRAM · contexto de 32K · 10 de septiembre de 2026. Estos dos perfiles usan **APEX GGUF + llama.cpp / Vulkan**.

| Modelo / perfil | Generación | RAM | VRAM del modelo |
|:--|--:|:--|--:|
| Qwen3.6 35B-A3B · I-Compact | **21.11 tokens/s** | pico de RSS de 13.43 GiB | 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + visión | **9.78 tokens/s** | límite del servicio de 11 GiB | lectura puntual de 4.88 GiB |

Qwen: 28 solicitudes, hasta 29,087 tokens de contexto. Gemma: una solicitud con visión habilitada. Las velocidades corresponden a la generación de tokens.

![Comparación de Qwen3.6: LocalForgeLLM, 21.11; Colibri, 9.9; FreeToken, 39.3 tokens/s. Nuestro pico de RSS es 13.43 GiB; Colibri declara 40 GB; FreeToken indica 32 GiB de RAM instalada. Las condiciones de prueba difieren.](docs/assets/comparison.svg)

Nuestra velocidad de Qwen es **2.13×** la [velocidad en caliente publicada por Colibri](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md) y **un 46.3% inferior** a la [publicada por FreeToken](https://arxiv.org/html/2608.16157v1#S5), en las configuraciones indicadas arriba. Un modelo de 35B funciona aquí con **13.43 GiB de RSS máximo y 4.07 GiB de VRAM del modelo**. [Ajustes, definiciones de las métricas y fuentes →](docs/README.es.md#comparación-con-colibri-y-freetoken)

## Documentación

[Skill del agente](SKILL.md) · [Manual del framework](docs/README.es.md#manual-para-el-agente) · [Documentación en español](docs/README.es.md) · [Perfiles de inicio](docs/README.es.md#perfiles-de-inicio) · [Metodología de medición](docs/README.es.md#uso-de-recursos-y-metodología) · [Comparación detallada](docs/README.es.md#comparación-con-colibri-y-freetoken)
