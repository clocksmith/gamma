# Translation Vocabulary Gap Report

- core_paths: `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl, projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl`
- extension_paths: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_03_draft_full.jsonl, projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed_plus_manual.jsonl`
- total_rows: `2130`

This report uses stopword-filtered content words and contiguous content bigrams.

## English

- total_texts: `2130`
- total_tokens: `24995`

### Most Common Content Words

| word | count | per_10k |
| --- | --- | --- |
| new | 131 | 52.41 |
| will | 62 | 24.8 |
| my | 57 | 22.8 |
| city | 51 | 20.4 |
| time | 47 | 18.8 |
| students | 44 | 17.6 |
| several | 44 | 17.6 |
| i'm | 43 | 17.2 |
| data | 41 | 16.4 |
| recommend | 41 | 16.4 |
| company | 39 | 15.6 |
| next | 37 | 14.8 |
| market | 37 | 14.8 |
| need | 36 | 14.4 |
| like | 35 | 14.0 |
| water | 34 | 13.6 |
| local | 34 | 13.6 |
| announced | 32 | 12.8 |
| me | 31 | 12.4 |
| asked | 30 | 12.0 |
| approved | 28 | 11.2 |
| first | 28 | 11.2 |
| energy | 27 | 10.8 |
| project | 26 | 10.4 |
| reduce | 26 | 10.4 |
| between | 25 | 10.0 |
| long | 25 | 10.0 |
| two | 25 | 10.0 |
| night | 25 | 10.0 |
| going | 25 | 10.0 |

### Most Common Content Bigrams

| phrase | count | per_10k |
| --- | --- | --- |
| asked students | 24 | 9.6 |
| doctors recommend | 18 | 7.2 |
| specialists recommend | 16 | 6.4 |
| professor asked | 14 | 5.6 |
| city council | 14 | 5.6 |
| analysts expect | 13 | 5.2 |
| instructor asked | 13 | 5.2 |
| market expects | 13 | 5.2 |
| next month | 10 | 4.0 |
| renewable energy | 9 | 3.6 |
| blood pressure | 8 | 3.2 |
| make sure | 8 | 3.2 |
| i'm going | 8 | 3.2 |
| artificial intelligence | 8 | 3.2 |
| long term | 8 | 3.2 |
| software update | 7 | 2.8 |
| next week | 7 | 2.8 |
| real time | 6 | 2.4 |
| new research | 6 | 2.4 |
| looking forward | 6 | 2.4 |

### Under-Served Content Words

Core terms with count >= `3` and extension/core rate <= `0.35`.

| word | core_count | ext_count | core_per_10k | ext_per_10k | coverage_ratio |
| --- | --- | --- | --- | --- | --- |
| asked | 27 | 3 | 16.8 | 3.36 | 0.2 |
| announced | 27 | 5 | 16.8 | 5.6 | 0.334 |
| health | 19 | 2 | 11.82 | 2.24 | 0.19 |
| reduce | 22 | 4 | 13.69 | 4.48 | 0.328 |
| system | 20 | 3 | 12.44 | 3.36 | 0.27 |
| allows | 17 | 2 | 10.58 | 2.24 | 0.212 |
| specialists | 15 | 1 | 9.33 | 1.12 | 0.12 |
| analysts | 14 | 1 | 8.71 | 1.12 | 0.129 |
| areas | 13 | 1 | 8.09 | 1.12 | 0.139 |
| code | 11 | 0 | 6.84 | 0.0 | 0.0 |
| doctors | 16 | 3 | 9.95 | 3.36 | 0.338 |
| trade | 16 | 3 | 9.95 | 3.36 | 0.338 |
| thousands | 14 | 2 | 8.71 | 2.24 | 0.257 |
| expect | 12 | 1 | 7.47 | 1.12 | 0.15 |
| expects | 12 | 1 | 7.47 | 1.12 | 0.15 |
| remains | 12 | 1 | 7.47 | 1.12 | 0.15 |
| developers | 10 | 0 | 6.22 | 0.0 | 0.0 |
| ensure | 10 | 0 | 6.22 | 0.0 | 0.0 |
| historical | 10 | 0 | 6.22 | 0.0 | 0.0 |
| i'll | 10 | 0 | 6.22 | 0.0 | 0.0 |
| increase | 10 | 0 | 6.22 | 0.0 | 0.0 |
| social | 10 | 0 | 6.22 | 0.0 | 0.0 |
| version | 10 | 0 | 6.22 | 0.0 | 0.0 |
| agreement | 13 | 2 | 8.09 | 2.24 | 0.277 |
| instructor | 13 | 2 | 8.09 | 2.24 | 0.277 |

### Under-Served Content Bigrams

| phrase | core_count | ext_count | core_per_10k | ext_per_10k | coverage_ratio |
| --- | --- | --- | --- | --- | --- |
| asked students | 24 | 0 | 14.93 | 0.0 | 0.0 |
| specialists recommend | 15 | 1 | 9.33 | 1.12 | 0.12 |
| professor asked | 13 | 1 | 8.09 | 1.12 | 0.139 |
| analysts expect | 12 | 1 | 7.47 | 1.12 | 0.15 |
| instructor asked | 12 | 1 | 7.47 | 1.12 | 0.15 |
| market expects | 12 | 1 | 7.47 | 1.12 | 0.15 |
| rural areas | 5 | 0 | 3.11 | 0.0 | 0.0 |
| environmental impact | 4 | 0 | 2.49 | 0.0 | 0.0 |
| generate electricity | 4 | 0 | 2.49 | 0.0 | 0.0 |
| ministry announced | 4 | 0 | 2.49 | 0.0 | 0.0 |
| office approved | 4 | 0 | 2.49 | 0.0 | 0.0 |
| trade agreement | 4 | 0 | 2.49 | 0.0 | 0.0 |
| venture capital | 4 | 0 | 2.49 | 0.0 | 0.0 |
| agency approved | 3 | 0 | 1.87 | 0.0 | 0.0 |
| agreement between | 3 | 0 | 1.87 | 0.0 | 0.0 |
| agreement will | 3 | 0 | 1.87 | 0.0 | 0.0 |
| air quality | 3 | 0 | 1.87 | 0.0 | 0.0 |
| authority announced | 3 | 0 | 1.87 | 0.0 | 0.0 |
| contract includes | 3 | 0 | 1.87 | 0.0 | 0.0 |
| drinking water | 3 | 0 | 1.87 | 0.0 | 0.0 |
| explained how | 3 | 0 | 1.87 | 0.0 | 0.0 |
| fuel prices | 3 | 0 | 1.87 | 0.0 | 0.0 |
| intellectual property | 3 | 0 | 1.87 | 0.0 | 0.0 |
| large scale | 3 | 0 | 1.87 | 0.0 | 0.0 |
| night bus | 3 | 0 | 1.87 | 0.0 | 0.0 |

## Spanish

- total_texts: `2130`
- total_tokens: `27324`

### Most Common Content Words

| word | count | per_10k |
| --- | --- | --- |
| está | 114 | 41.72 |
| si | 85 | 31.11 |
| me | 61 | 22.32 |
| empresa | 55 | 20.13 |
| datos | 50 | 18.3 |
| nueva | 49 | 17.93 |
| nuevo | 48 | 17.57 |
| ciudad | 46 | 16.84 |
| tiempo | 38 | 13.91 |
| recomiendan | 37 | 13.54 |
| agua | 34 | 12.44 |
| seguridad | 34 | 12.44 |
| mercado | 34 | 12.44 |
| noche | 33 | 12.08 |
| reducir | 32 | 11.71 |
| pidió | 30 | 10.98 |
| forma | 29 | 10.61 |
| anunció | 28 | 10.25 |
| puede | 26 | 9.52 |
| aprobó | 26 | 9.52 |
| tras | 26 | 9.52 |
| equipo | 26 | 9.52 |
| semana | 26 | 9.52 |
| mejor | 25 | 9.15 |
| proyecto | 25 | 9.15 |
| tan | 25 | 9.15 |
| mañana | 25 | 9.15 |
| mejorar | 24 | 8.78 |
| están | 24 | 8.78 |
| varios | 24 | 8.78 |

### Most Common Content Bigrams

| phrase | count | per_10k |
| --- | --- | --- |
| médicos recomiendan | 18 | 6.59 |
| especialistas recomiendan | 16 | 5.86 |
| profesora pidió | 13 | 4.76 |
| docente pidió | 13 | 4.76 |
| mercado prevé | 13 | 4.76 |
| analistas esperan | 12 | 4.39 |
| empresa está | 12 | 4.39 |
| próximo mes | 10 | 3.66 |
| nueva ley | 9 | 3.29 |
| largo plazo | 9 | 3.29 |
| dónde está | 9 | 3.29 |
| inteligencia artificial | 8 | 2.93 |
| presión arterial | 7 | 2.56 |
| tiempo real | 6 | 2.2 |
| artificial está | 6 | 2.2 |
| puede ser | 6 | 2.2 |
| me gustaría | 6 | 2.2 |
| próxima semana | 6 | 2.2 |
| ambas partes | 5 | 1.83 |
| estoy considerando | 5 | 1.83 |

### Under-Served Content Words

Core terms with count >= `3` and extension/core rate <= `0.35`.

| word | core_count | ext_count | core_per_10k | ext_per_10k | coverage_ratio |
| --- | --- | --- | --- | --- | --- |
| pidió | 27 | 3 | 14.97 | 3.23 | 0.216 |
| anunció | 25 | 3 | 13.86 | 3.23 | 0.233 |
| permite | 21 | 2 | 11.64 | 2.15 | 0.185 |
| salud | 19 | 2 | 10.53 | 2.15 | 0.204 |
| sistema | 20 | 3 | 11.09 | 3.23 | 0.291 |
| riesgo | 19 | 3 | 10.53 | 3.23 | 0.307 |
| especialistas | 15 | 1 | 8.32 | 1.08 | 0.129 |
| zonas | 15 | 1 | 8.32 | 1.08 | 0.129 |
| estudio | 13 | 0 | 7.21 | 0.0 | 0.0 |
| prevé | 14 | 1 | 7.76 | 1.08 | 0.139 |
| miles | 15 | 2 | 8.32 | 2.15 | 0.259 |
| alumnado | 13 | 1 | 7.21 | 1.08 | 0.149 |
| transporte | 13 | 1 | 7.21 | 1.08 | 0.149 |
| aplicaciones | 11 | 0 | 6.1 | 0.0 | 0.0 |
| carga | 11 | 0 | 6.1 | 0.0 | 0.0 |
| docente | 12 | 1 | 6.65 | 1.08 | 0.162 |
| esperan | 12 | 1 | 6.65 | 1.08 | 0.162 |
| desarrolladores | 10 | 0 | 5.54 | 0.0 | 0.0 |
| rendimiento | 10 | 0 | 5.54 | 0.0 | 0.0 |
| calidad | 11 | 1 | 6.1 | 1.08 | 0.177 |
| industria | 9 | 0 | 4.99 | 0.0 | 0.0 |
| mayor | 9 | 0 | 4.99 | 0.0 | 0.0 |
| usuarios | 9 | 0 | 4.99 | 0.0 | 0.0 |
| personas | 12 | 2 | 6.65 | 2.15 | 0.324 |
| red | 12 | 2 | 6.65 | 2.15 | 0.324 |

### Under-Served Content Bigrams

| phrase | core_count | ext_count | core_per_10k | ext_per_10k | coverage_ratio |
| --- | --- | --- | --- | --- | --- |
| especialistas recomiendan | 15 | 1 | 8.32 | 1.08 | 0.129 |
| analistas esperan | 12 | 0 | 6.65 | 0.0 | 0.0 |
| docente pidió | 12 | 1 | 6.65 | 1.08 | 0.162 |
| mercado prevé | 12 | 1 | 6.65 | 1.08 | 0.162 |
| profesora pidió | 12 | 1 | 6.65 | 1.08 | 0.162 |
| casco antiguo | 5 | 0 | 2.77 | 0.0 | 0.0 |
| segundo plano | 5 | 0 | 2.77 | 0.0 | 0.0 |
| energías renovables | 4 | 0 | 2.22 | 0.0 | 0.0 |
| impacto ambiental | 4 | 0 | 2.22 | 0.0 | 0.0 |
| redes sociales | 4 | 0 | 2.22 | 0.0 | 0.0 |
| acuerdo comercial | 3 | 0 | 1.66 | 0.0 | 0.0 |
| agua potable | 3 | 0 | 1.66 | 0.0 | 0.0 |
| autoridad portuaria | 3 | 0 | 1.66 | 0.0 | 0.0 |
| clave privada | 3 | 0 | 1.66 | 0.0 | 0.0 |
| contrato incluye | 3 | 0 | 1.66 | 0.0 | 0.0 |
| está evolucionando | 3 | 0 | 1.66 | 0.0 | 0.0 |
| está invirtiendo | 3 | 0 | 1.66 | 0.0 | 0.0 |
| evitar errores | 3 | 0 | 1.66 | 0.0 | 0.0 |
| explicó cómo | 3 | 0 | 1.66 | 0.0 | 0.0 |
| gran escala | 3 | 0 | 1.66 | 0.0 | 0.0 |
| mil años | 3 | 0 | 1.66 | 0.0 | 0.0 |
| nueva política | 3 | 0 | 1.66 | 0.0 | 0.0 |
| nuevas medidas | 3 | 0 | 1.66 | 0.0 | 0.0 |
| propiedad intelectual | 3 | 0 | 1.66 | 0.0 | 0.0 |
| puede mejorar | 3 | 0 | 1.66 | 0.0 | 0.0 |
