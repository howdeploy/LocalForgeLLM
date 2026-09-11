# Documentación de LocalForgeLLM

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <strong>Español</strong>
</p>

[Volver al proyecto](../README.es.md) · [Instalación](#instalación) · [Perfiles de inicio](#perfiles-de-inicio) · [Mediciones](#mediciones-en-una-rtx-4060)

## Manual para el agente

Empieza por [AGENTS.md](../AGENTS.md) y el [skill común de LocalForgeLLM](../SKILL.md). El framework cubre tres niveles de trabajo con LLM: instalar un modelo y su entorno; ajustarlos o modificarlos; construir un artefacto derivado a partir de los pesos completos. Las actualizaciones y la integración de interfaces se aplican a todos los niveles. La generación de imágenes, vídeo y audio tiene una rama independiente planificada.

| Cuándo leer | Guía |
|:--|:--|
| Entender el framework y las responsabilidades de cada componente | [Arquitectura](architecture.md) |
| Interpretar una tarea, estudiar una implementación o retomar un entorno | [Proceso del agente y registro del entorno](agent-workflow.md) |
| Instalar un modelo publicado y sus dependencias | [Nivel 1 — instalación](llm/install.md) |
| Cambiar contexto, distribución, rendimiento o comportamiento MoE | [Nivel 2 — ajuste y adaptación](llm/tune.md) |
| Descargar un asistente compatible; activar, desactivar o diagnosticar la especulación | [MTP: operaciones, memoria y calidad](implementations/mtp.md) |
| Convertir, calibrar y cuantizar pesos completos | [Nivel 3 — construcción](llm/build.md) |
| Elegir un motor o método de procesamiento de pesos | [Motores](implementations/engines.md) · [APEX](implementations/apex.md) |
| Conectar o personalizar un agente y su interfaz | [Contratos de interfaz](interfaces/README.md) · [Pi](interfaces/pi.md) · [OpenShell](interfaces/openshell.md) · [llama UI](interfaces/llama-ui.md) · [Hermes](interfaces/hermes.md) |
| Actualizar, reparar o restaurar un entorno funcional | [Mantenimiento](operations.md) |
| Verificar capacidades, calidad y uso de recursos | [Validación](validation.md) |
| Desarrollar la futura rama generativa | [Alcance previsto](generative/README.md) |
| Comprobar versiones y fundamentos de las instrucciones | [Fuentes](sources.md) |

Las nuevas guías técnicas se mantienen en inglés; los ejemplos de despliegue de esta página conservan su traducción al español. El [alcance de verificación](sources.md#existing-measured-stack) distingue los datos contrastados con el código de los resultados medidos en un entorno real.

## Cómo funciona

1. Indica a tu agente de programación la tarea, el contexto deseado y el presupuesto de memoria. Especifica un modelo MoE o deja que lo elija. El agente examina la CPU, GPU, RAM, almacenamiento y software instalado.
2. Con la documentación del framework, del modelo y del runtime, selecciona un motor y un formato de pesos compatibles.
3. Ajusta la distribución CPU/GPU, los hilos, el contexto, la precisión de la caché y el tamaño de los lotes para tu tarea.
4. Ejecuta la tarea, comprueba la respuesta, mide la velocidad y el uso de RAM/VRAM, y refina los parámetros. El resultado es un perfil de inicio reutilizable con la versión del motor y sus ajustes.

![Un agente selecciona y optimiza un entorno local según tu tarea y hardware, mide los resultados y guarda un perfil de inicio.](assets/how-it-works.svg)

La instalación y los comandos siguientes son **dos ejemplos para un mismo PC**: Qwen y Gemma con APEX GGUF. El framework aplica el mismo ciclo de selección y ajuste a otros modelos MoE y métodos de cuantización.

## Instalación

**Hardware de referencia:** Linux x86_64, controlador Vulkan, RTX 4060 de 8 GB, Ryzen 5 5600 y 32 GB de RAM. Reserva unos 22 GB de SSD para Gemma con visión o 18 GB para Qwen. Son las configuraciones utilizadas, no requisitos mínimos universales.

1. Descarga el [archivo de llama.cpp b10883 con Vulkan](https://github.com/ggml-org/llama.cpp/releases/download/b10883/llama-b10883-bin-ubuntu-vulkan-x64.tar.gz) y extráelo en `runtime/`.
2. Crea `models/` y descarga uno de los perfiles siguientes. Conserva los nombres originales; el proyector visual se llama `mmproj.gguf`.
3. Inicia el perfil elegido y abre [localhost:8080](http://localhost:8080). Los agentes usan `http://127.0.0.1:8080/v1` con el identificador `gemma-apex` o `qwen-apex`. Ejecuta un solo modelo a la vez.

| Perfil | Descargas |
|:--|:--|
| Gemma 4 26B-A4B Heretic · **I-Balanced** | [Modelo · 19.51 GB](https://huggingface.co/mudler/gemma-4-26B-A4B-it-heretic-APEX-GGUF/resolve/8e3506b8b11a8ac2d666e0df473fa7ba4ec21497/gemma-4-26B-A4B-heretic-APEX-I-Balanced.gguf?download=true) + [visión · 1.19 GB](https://huggingface.co/mudler/gemma-4-26B-A4B-it-heretic-APEX-GGUF/resolve/8e3506b8b11a8ac2d666e0df473fa7ba4ec21497/mmproj.gguf?download=true) |
| Qwen3.6 35B-A3B · **I-Compact** | [Modelo · 17.29 GB](https://huggingface.co/mudler/Qwen3.6-35B-A3B-APEX-GGUF/resolve/316efc983b0d8d41290ceb4ad31bd9a66b6c54e8/Qwen3.6-35B-A3B-APEX-I-Compact.gguf?download=true) · perfil de texto |

## Perfiles de inicio

Ejecuta los comandos desde el directorio que contiene `runtime/` y `models/`. El archivo crea `runtime/llama-b10883/`. En nuestra configuración, `Vulkan0` es la RTX 4060; ajústalo si tus dispositivos aparecen en otro orden.

### Gemma

Requiere una sesión de usuario de systemd. El límite de 11 GiB del servicio incluye la caché de archivos; `mmap` permite liberar páginas del modelo y volver a leerlas desde el SSD. Esto limita la memoria residente a costa de posibles pausas de E/S. No reserva memoria para otras aplicaciones ni garantiza evitar un OOM.

```bash
mkdir -p logs
systemd-run --user --unit=gemma-apex --collect \
  --property=MemoryMax=11G --property=MemorySwapMax=0 \
  --property=OOMPolicy=kill --property=OOMScoreAdjust=1000 \
  --property=LimitCORE=0 --property=CPUQuota=600% \
  --property=Nice=5 --property=TimeoutStopSec=15 \
  --property="StandardOutput=append:$PWD/logs/gemma-server.log" \
  --property=StandardError=inherit \
  "$PWD/runtime/llama-b10883/llama-server" \
  --model "$PWD/models/gemma-4-26B-A4B-heretic-APEX-I-Balanced.gguf" \
  --mmproj "$PWD/models/mmproj.gguf" \
  --no-mmproj-offload --image-max-tokens 1120 \
  --alias gemma-apex --host 127.0.0.1 --port 8080 --cors-origins localhost \
  --device Vulkan0 --gpu-layers all --n-cpu-moe 27 --fit off \
  --load-mode mmap --threads 6 --threads-batch 6 \
  --ctx-size 32768 --parallel 1 --batch-size 1152 --ubatch-size 1152 \
  --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
  --cache-ram 0 --ctx-checkpoints 1 \
  --temp 1.0 --top-p 0.95 --top-k 64 --min-p 0 \
  --log-colors off --log-timestamps
```

Detén el servicio con `systemctl --user stop gemma-apex`. El proyector se ejecuta en la CPU. Mantén ambos tamaños de lote en 1152 con el límite de 1120 tokens por imagen: los microlotes más pequeños provocaron un error de aserción al procesar imágenes en esta compilación.

### Qwen

Se ejecuta en primer plano; detenlo con `Ctrl+C`. Este perfil no tiene límite de memoria del servicio ni proyector visual.

```bash
./runtime/llama-b10883/llama-server \
  --model ./models/Qwen3.6-35B-A3B-APEX-I-Compact.gguf \
  --alias qwen-apex --host 127.0.0.1 --port 8080 --cors-origins localhost \
  --device Vulkan0 --gpu-layers all --n-cpu-moe 36 --fit off \
  --load-mode none --threads 6 --threads-batch 6 \
  --ctx-size 32768 --parallel 1 --batch-size 512 --ubatch-size 128 \
  --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
  --cache-ram 0 --ctx-checkpoints 4 \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0 \
  --log-colors off --log-timestamps
```

## Ejemplo con APEX

Estos perfiles usan pesos GGUF de precisión mixta [APEX](https://github.com/localai-org/apex-quant). La precisión se asigna según la función del tensor y su capa; los perfiles `I-` se calibran con una matriz de importancia. MoE activa parte de los expertos por token, mientras llama.cpp reparte el cómputo entre CPU y GPU. El modelo completo se aloja entre SSD, RAM y VRAM.

## Mediciones en una RTX 4060

Ryzen 5 5600 · 32 GB de RAM · Manjaro Linux · llama.cpp b10883 / Vulkan · 10 de septiembre de 2026.

| Modelo / perfil | Generación | Ventana de contexto | RAM / VRAM del modelo |
|:--|--:|--:|:--|
| Qwen3.6 35B-A3B · I-Compact | **21.11 tokens/s** | **32,768** | pico de RSS de 13.43 GiB / 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + visión | **9.78 tokens/s** | **32,768** | límite del servicio de 11 GiB / lectura puntual de 4.88 GiB |

Qwen: 28 solicitudes completadas, 19.37–22.09 tokens/s y hasta 29,087 tokens de contexto registrados. Gemma: una solicitud completada con visión habilitada, 599 tokens de entrada y 632 de salida. Configurar una ventana de 32K no equivale a probarla llena bajo carga; la velocidad de generación excluye el procesamiento del prompt.

## Uso de recursos y metodología

El seguimiento de Qwen comprende 314 muestras durante los primeros 10 min 44 s de la sesión, incluidas las pausas:

| Recurso | Media / máximo |
|:--|:--|
| RAM del modelo, RSS | 13.23 / 13.43 GiB |
| VRAM del modelo | 4.07 / 4.07 GiB |
| CPU del modelo, normalizada sobre los 12 hilos lógicos | 10.1% / 46.9% |
| Uso de toda la GPU, incluidas las aplicaciones de escritorio | 89.8% / 100% |
| Temperatura de la GPU | 50.4 / 54 °C |

La RAM disponible del sistema bajó hasta 2.53 GiB; la VRAM libre, hasta 811 MiB. Gemma alcanzó el límite de cgroup de 11 GiB, que incluye la caché de archivos y es una medida distinta del RSS. Sus 4.88 GiB de VRAM corresponden a una lectura puntual; no se registró la utilización de CPU/GPU de ese perfil.

Qwen generó 7,820 tokens en 28 solicitudes completadas. La velocidad ponderada por tiempo es `(7820 − 28) / 369.07315 = 21.11 tokens/s`, siguiendo el cómputo del primer token de llama.cpp. El procesamiento de entrada nueva promedió 67.36 tokens/s. Gemma dedicó 97.59 s al prompt y 64.55 s a la generación: 162.13 s en total. Estas medidas describen la velocidad del servicio, no la calidad del modelo.

## Comparación con Colibri y FreeToken

![Comparación de Qwen3.6: LocalForgeLLM, 21.11; Colibri, 9.9; FreeToken, 39.3 tokens/s. Nuestro pico de RSS es 13.43 GiB; Colibri declara 40 GB; FreeToken indica 32 GiB de RAM instalada. El hardware y la cuantización difieren.](assets/comparison.svg)

- **[Colibri](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md):** los autores publican 9.2 / 9.9 tokens/s con historial de enrutamiento frío / caliente, pico de RSS de 40 GB, Threadripper 3945WX + RTX 3070 de 8 GB, int4 y generación de 200 tokens.
- **[FreeToken](https://arxiv.org/html/2608.16157v1#S5):** los autores publican 39.3 tokens/s en una RTX 4060 Laptop de 8 GB + i9-13900H, 32 GiB de LPDDR5, NVFP4 y una tarea de programación con OpenCode. La RAM instalada no es una medición del consumo del proceso.

Nuestra velocidad de Qwen es **2.13×** la velocidad en caliente citada de Colibri y **un 46.3% inferior** a la de FreeToken. Las filas describen distintas CPU, formatos, tareas y formas de calcular la media. Nuestra cifra de memoria y la de Colibri son RSS del proceso; los 32 GiB de FreeToken son capacidad instalada. Los 11 GiB de Gemma son un límite del servicio que incluye la caché de archivos. Conserva estas definiciones al comparar configuraciones.

## Actualización de Gemma MTP — 11 de septiembre

El mismo perfil APEX con un asistente MTP Q8 separado registró **14.83 tokens/s** en dos solicitudes y **15.03 tokens/s** durante los 102.05 s de generación de la respuesta larga. Se conservaron la ventana de 32K y la distribución de los pesos principales; el contexto máximo observado fue de 2265 tokens. La diferencia de **+51.1%** frente a la solicitud anterior sin MTP no es una ganancia causal aislada: las solicitudes difieren. La evaluación formal de calidad, visión y herramientas con MTP sigue pendiente.

[Comparación, dos infografías en inglés, recursos y fuentes](benchmarks/gemma4-mtp.md) · [Mediciones numéricas](benchmarks/gemma4-mtp.csv) · [Descargar, activar y desactivar MTP](implementations/mtp.md)
