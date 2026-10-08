# Semana 3 — Sistemas Distribuidos (FDICI25 / INFO35)

Material de la Semana 3 (3 y 4 de septiembre de 2026). Descomprimir este ZIP
**dentro del repositorio del equipo**, en una carpeta `semana03/`, y hacer commit
antes del laboratorio del viernes.

```
semana03/
├── README.md                         ← este archivo
├── guia_analisis_casos/
│   └── Guia_analisis_casos.md        ← instrumento del viernes (plantilla + 4 casos)
├── taller_multisede/
│   └── Taller_multisede.md           ← escenario y matriz de trade-offs
├── Recordatorio_Evaluacion1.md       ← exposición del jueves 10-09 (20%)
└── demo_cap/                         ← demo del jueves: dos réplicas y una partición
    ├── docker-compose.yml
    ├── Dockerfile
    ├── kv.py
    └── cliente.py
```

## Qué entrega el equipo el viernes 4 (antes de las 16:00)

| Archivo en el repositorio | Contenido |
|---|---|
| `semana03/guia_analisis_casos/caso_<nombre>.md` | Guía de análisis completada para el caso asignado (copiar la plantilla) |
| `semana03/taller_multisede/matriz_<equipo>.md` | Matriz de trade-offs del taller multi-sede |

Commit sugerido: `git commit -m "Semana 3: análisis de caso <nombre> y matriz multi-sede"`.

## Trabajo autónomo de la semana (guía de aprendizaje)

1. Cerrar la investigación sobre aplicaciones de sistemas distribuidos y preparar
   la exposición del **jueves 10 de septiembre** (Evaluación 1, 20%).
2. Lectura complementaria sobre escalabilidad: Tanenbaum & Van Steen (2017) §1.2;
   Coulouris et al. (2001) cap. 2.

## Demo CAP (opcional para reproducir en casa)

```bash
cd semana03/demo_cap
docker compose up -d --build
c python cliente.py a set nota 6.5      # c = docker compose exec cliente
c python cliente.py b get nota
docker network disconnect sd_repl replica_b     # partición
c python cliente.py a set nota 7.0      # modo AP: responde con aviso
c python cliente.py b get nota          # modo AP: 6.5 (dato viejo)
docker compose down
MODO=CP docker compose up -d
docker network disconnect sd_repl replica_b
c python cliente.py a set nota 7.0      # modo CP: 503
docker network connect --alias peer_b sd_repl replica_b
docker compose down -v
```

Alias `c`: PowerShell `function c { docker compose exec cliente @args }` ·
bash/zsh `c() { docker compose exec cliente "$@"; }`.
