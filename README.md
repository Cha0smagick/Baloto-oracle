# 🔮 Baloto Oracle

> **Análisis Estadístico Completo de la Lotería Baloto Colombia**

[![Deploy Status](https://github.com/Cha0smagick/Baloto-oracle/workflows/Deploy%20to%20GitHub%20Pages/badge.svg)](https://github.com/Cha0smagick/Baloto-oracle/actions)
[![CI Status](https://github.com/Cha0smagick/Baloto-oracle/workflows/CI%20Checks/badge.svg)](https://github.com/Cha0smagick/Baloto-oracle/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Visits](https://visitor-badge.laobi.icu/badge?page_id=Cha0smagick.baloto-oracle)](https://github.com/Cha0smagick/Baloto-oracle)

Un oráculo interactivo para la lotería **Baloto Colombia** que aplica estadística descriptiva e inferencial completa (parámetros y no paramétricos), visualiza patrones históricos, calcula probabilidades bayesianas e implementa modelado predictivo múltiple para el próximo sorteo.

**Autor**: [Alejandro Quintero](https://github.com/alejandroquintero) — Profesor de Estadística, Corporación Universitaria Iberoamericana  
**Motivación**: *"Me lo preguntaban mucho y pues sí, ¿por qué no? ¿Por qué no poner el sistema online disponible para cualquiera?"*

## ✨ Características

### 📊 Estadística Descriptiva
- **Mapa de calor de frecuencias** (números 1-43) con código de colores y z-scores
- **Frecuencia de Superbalota** (1-16) con detección de números calientes/fríos
- **Análisis por posición** (1ª a 5ª bola) con gráficos de líneas
- **Distribución de sumas** con estadísticos teóricos vs observados
- **Balance Par/Impar y Alto/Bajo** con gráficos de dona interactivos
- **Números consecutivos** y **gaps entre números** con análisis temporal
- **Patrones de repetición** de sorteos recientes (ventana móvil)
- **Comparativa Baloto vs Revancha** lado a lado
- **Evolución del Jackpot** con detección de rollovers

### 🔬 Estadística Inferencial Completa

#### Pruebas Paramétricas
- **Chi-cuadrado bondad de ajuste** — H₀: distribución uniforme de números, con la referencia corregida por muestreo sin reemplazo: `(38/42)·χ²₄₂`
- **Portmanteau de autocorrelación** — H₀: independencia entre sorteos (`Q = n·Σrᵢ² ~ χ²₄₃` sobre las 43 series binarias)
- **Test binomial exacto de los 43 números** — Significancia individual, bilateral
- **Corrección Benjamini-Hochberg (FDR)** — sobre las 43 comparaciones, no sobre las que ya salieron extremas
- **Corrección Bonferroni** — α = 0.05/43 ≈ 0.00116 como referencia conservadora
- **Intervalos de confianza 95%** — t-Student para la media de las sumas; banda esperada bajo H₀ para la frecuencia de cada número
- **Normalidad** — Shapiro-Wilk y Anderson-Darling sobre las sumas (con asimetría y curtosis)

#### Pruebas No Paramétricas
- **Mann-Whitney U** — Compara sumas entre sorteos impar-pesados vs par-pesados
- **Chi-cuadrado por posición** — Cada posición contra la distribución nula **exacta** del estadístico de orden de una 5-subconjunto de 1..43 (Kruskal-Wallis y ANOVA sobre posiciones ya ordenadas son tautologías: rechazan siempre)
- **Friedman** — Estabilidad de patrones consecutivos a través del tiempo
- **Wilcoxon signed-rank** — Cambio sistemático en sumas: primera vs segunda mitad histórica

### 🤖 Modelado Predictivo Múltiple
- **Bayesiano (Beta-Binomial)** — Prior con todo el histórico previo a la ventana, likelihood con la ventana reciente (sin solape)
- **Cadenas de Markov** — Matriz de transición 43×43 normalizada por fila
- **Regresión lineal temporal** — Tendencias en sumas y frecuencias con ventanas **no solapadas** y FDR sobre los 43 números
- **Suavizado exponencial (EWMA)** — Pronóstico con factor α configurable
- **Ensemble ponderado** — 50% Bayesiano + 25% Markov + 25% ExpSmoothing
- **Top 5 / Top 10** números por cada modelo con probabilidades normalizadas

> ⚠️ **Los sorteos son eventos aleatorios independientes. El rendimiento pasado NO predice resultados futuros. Todos los modelos tienen validez predictiva nula. Juega responsablemente.**

### 🎮 Visualizador Interactivo & UX
- **100% Responsive** — Mobile-first, breakpoints 480px, 768px, 1024px
- **Tema Oscuro/Claro** — Persistente en localStorage, transiciones suaves
- **Fondo animado** — Partículas con conexiones (Canvas API, pausa en background tab)
- **Filtrado dinámico** — Juego (Baloto/Revancha/Ambos), período, tipo de vista
- **4 visualizaciones D3.js** — Frecuencias, Línea temporal, Patrones, Jackpots
- **Tabla histórica** — Últimos 20 sorteos con bolas visuales coloreadas
- **Contador de visitas** — Badge en README + contador en página
- **Navegación accesible** — ARIA labels, focus visible, skip link, `prefers-reduced-motion`
- **Toasts notificaciones** — Feedback no intrusivo

## 🚀 Demo en Vivo

**[https://cha0smagick.github.io/Baloto-oracle/](https://cha0smagick.github.io/Baloto-oracle/)**

## 📦 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/Cha0smagick/Baloto-oracle.git
cd baloto-oracle

# Instalar dependencias Python
pip install -r requirements.txt

# Pipeline completo: descarga, análisis, validación y embebido en data.js
python scripts/fetch_baloto_data.py   # scrape oficial + fusión con el histórico
python scripts/analyze_baloto.py      # motor estadístico
python scripts/validate_baloto.py     # validación (pares ciegos, ML, tests exactos)
python scripts/generate_data_js.py    # embebe todo en src/js/data.js
python scripts/verify_output.py       # aborta si el artefacto no cuadra

# Tests
python -m pytest scripts/ -v

# Servir frontend (requiere Node.js 18+)
npx serve .
# Abrir http://localhost:3000
```

## 🏗️ Arquitectura

```
baloto-oracle/
├── 📁 data/
│   ├── 📁 raw/           # CSVs originales (desde 2021-05-01)
│   └── 📁 processed/     # JSONs para frontend (baloto, revancha, metadata, analysis, validation)
├── 📁 scripts/
│   ├── fetch_baloto_data.py    # Scraper oficial + fusión por fecha (nunca pierde historia)
│   ├── analyze_baloto.py       # Motor estadístico descriptivo e inferencial
│   ├── validate_baloto.py      # Pares ciegos, ML supervisado/no supervisado, tests exactos
│   ├── generate_data_js.py     # Embebe el JSON en window.BAL_DATA
│   ├── verify_output.py        # Contrato del artefacto publicado
│   └── test_pipeline.py        # Tests del parser y de la integridad de datos
├── 📁 src/
│   ├── 📁 js/main.js           # SPA vanilla ES Modules (~2200 líneas)
│   ├── 📁 js/data.js           # Generado — no editar a mano
│   └── 📁 css/main.css         # CSS Variables, Grid/Flex, animaciones (~1500 líneas)
├── 📁 .github/workflows/
│   ├── update-data.yml         # Auto-update Lun/Mié/Sáb 00:30 UTC + backup diario
│   └── ci.yml                  # Lint, tests, sintaxis JS, HTML y enlaces
├── index.html                  # SPA semántica + CSP + SRI
├── AUDIT.md                    # Auditoría de 2026-11 y plan de corrección
├── package.json                # Node deps (serve)
├── requirements.txt            # Python deps (con cotas por major)
└── CHANGELOG.md                # Keep a Changelog format
```

## 🔄 Actualización Automática (GitHub Actions)

| Trigger | Frecuencia | Acción |
|---------|------------|--------|
| `schedule` | Lun/Mié/Sáb 00:30 UTC | Descarga nuevos sorteos, recalcula análisis y validación, verifica el artefacto, despliega |
| `schedule` | Diario 06:00 UTC | Backup por si falla el principal |
| `workflow_dispatch` | Manual | Fuerza actualización completa (`force_update: true`) |
| `push` / `pull_request` | Cada commit | Lint (ruff/black/isort), pytest, `node --check`, validación HTML y de enlaces |

**Despliegue**: GitHub Pages automático tras actualización exitosa. El artefacto publicado se construye en `_site/` (solo `index.html`, `src/`, `assets/`, `data/`).

## 📈 Metodología Estadística Detallada

### Datos
- **Fuente**: scraping del sitio oficial `baloto.com/resultados` (paginado hasta el fin del historial)
- **Período**: 2021-05-01 – presente (cambio de formato a 5/43 + 1/16 Superbalota)
- **Sorteos**: Lunes, Miércoles y Sábado · 23:00 COT · Canal RCN (los lunes solo desde 2025-06)
- **Formato**: 5 números (1–43) + 1 Superbalota (1–16)
- **Premios**: 9 categorías · Odds jackpot 1:15.401.568 · Odds cualquier premio 1:19.34
- **Historial**: el scraper fusiona por fecha con el histórico almacenado, así que un scrape parcial nunca borra sorteos anteriores

### Análisis Descriptivo
- Frecuencias absolutas/relativas con **z-scores** calculados sobre `√(n·p·(1−p)·(N−k)/(N−1))` (z > 1.5 caliente, z < −1.5 frío)
- Estadísticos por posición (media, mediana, desv. est. por bola 1–5)
- Sumas: media teórica 110, desv. teórica 26.39 (sin reemplazo), percentiles 25/50/75/90/95
- Paridad: 6 patrones (5-0 a 0-5) con % observado vs teórico
- Rango: Alto (23–43) vs Bajo (1–22), mismos 6 patrones
- Consecutivos: Distribución 0–3+ pares, probabilidad ≥1 par
- Gaps: Media, mediana, distribución de diferencias entre bolas adyacentes
- Repeticiones: Ventana 10 sorteos, con la línea base teórica al lado (3.55 esperadas)

### Inferencial Paramétrico
| Prueba | H₀ | Estadístico | Decisión |
|--------|-----|-------------|----------|
| Chi² bondad ajuste | Uniforme 1/43 | χ²(42) corregido por (38/42) | p ≥ 0.05 → No rechazar |
| Portmanteau lag-1 | Independencia de las 43 series | Q = n·Σrᵢ² ~ χ²(43) | p ≥ 0.05 → No rechazar |
| Binomial (43 números) | p = 5/43 | Exacto bilateral | FDR α = 0.05 |
| IC 95% media sumas | μ = 110 | t-Student | [108.0, 112.1] |
| Banda esperada H₀ | p = 5/43 | Wald (Normal) | [0.0917, 0.1408] |
| Shapiro-Wilk (sumas) | Normalidad | W | p < 0.05 → No normal |
| Anderson-Darling | Normalidad | A² | A² > crítico 5% → No normal |

### Inferencial No Paramétrico
| Prueba | Comparación | Uso |
|--------|-------------|-----|
| Mann-Whitney U | Suma (impar-pesado vs par-pesado) | ¿Influye paridad en suma? |
| Chi² por posición | Posición observada vs orden estadístico exacto | ¿Es justa cada posición? |
| Friedman | Consecutivos por trimestre | ¿Patrón estable en tiempo? |
| Wilcoxon signed-rank | Sumas 1ª mitad vs 2ª mitad | ¿Deriva temporal? |

### Modelado Predictivo (Solo Académico)

**Bayesiano (Beta-Binomial conjugado)**
```
Prior:      Beta(α = count_previo + 1, β = previos×5 − count_previo + 1)
Likelihood: ventana reciente (últimos 50 sorteos), sin solape con el prior
Posterior:  Beta(α + count_reciente, β + reciente×5 − count_reciente)
P(next) = E[Posterior], normalizado a 5 números por sorteo
```

**Markov Chain (Orden 1)**
- Matriz T[43×43]: T[i][j] = P(número j en sorteo t+1 | número i en sorteo t)
- Predicción: Σ_{i∈último_sorteo} T[i][·] normalizado

**Regresión Tendencial**
- Suma ~ β₀ + β₁·t + ε (t = índice sorteo)
- Frecuencia por ventana 100 sorteos: slope, p-valor por número

**Suavizado Exponencial (EWMA)**
- Sₜ = α·Xₜ + (1-α)·Sₜ₋₁, α = 0.3 default
- Xₜ ∈ {0,1} indicadora de aparición

**Ensemble**
- 0.50 × Bayesiano + 0.25 × Markov + 0.25 × EWMA
- Normalizado a 5 números

> **Todos los modelos: Confianza Muy Baja / Nula**. La lotería es proceso aleatorio sin memoria.

## 🎨 Stack Tecnológico

| Capa | Tecnologías |
|------|-------------|
| **Análisis/Backend** | Python 3.11, Pandas 2, NumPy, SciPy, StatsModels, scikit-learn |
| **Frontend Core** | Vanilla JS (ES Modules), Chart.js 4.4, D3.js 7 |
| **Estilos/UI** | CSS Custom Properties, CSS Grid/Flexbox, Mobile-first, Animaciones CSS |
| **Calidad Código** | Ruff, Black, isort, pytest, html5validator, lychee |
| **CI/CD** | GitHub Actions (matrix: Ubuntu, Python 3.11, Node 18) |
| **Hosting** | GitHub Pages (static JSON + SPA) |
| **Datos** | JSON estático (sin servidor, sin BD, sin API keys) |

## 📁 Esquema de Datos (JSON)

```json
// data/processed/baloto.json
[
  {
    "draw_id": 1234,
    "date": "2026-08-05",
    "numbers": [8, 11, 22, 30, 31],
    "superbalota": 2,
    "jackpot": 51600000000,
    "game": "Baloto"
  }
]

// data/processed/analysis_results.json
{
  "descriptive": { 
    "number_frequencies": {...}, 
    "superbalota_frequencies": {...},
    "position_frequencies": {...},
    "sum_statistics": {...},
    "odd_even_balance": {...},
    "high_low_balance": {...},
    "consecutive_numbers": {...},
    "number_gaps": {...},
    "repeating_numbers": {...},
    "jackpot_statistics": {...}
  },
  "inferential": {
    "parametric": {
      "uniformity_test": {...},
      "independence_test": {...},
      "hot_cold_significance": {...},
      "confidence_intervals": {...},
      "normality_shapiro": {...},
      "normality_anderson": {...}
    },
    "non_parametric": {
      "mann_whitney_odd_even": {...},
      "kruskal_wallis_position": {...},
      "friedman_consecutive": {...},
      "wilcoxon_signed_rank": {...}
    }
  },
  "predictive_modeling": {
    "bayesian": {...},
    "bayesian_superbalota": {...},
    "markov_chain": {...},
    "regression_trends": {...},
    "exponential_smoothing": {...},
    "ensemble": {...}
  },
  "predictions": { "next_draw_numbers": {...}, "next_superbalota": {...} },
  "metadata": { "analysis_date": "...", "total_draws_analyzed": 1455, ... }
}
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'feat: añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre Pull Request

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE) para detalles.

## ⚖️ Aviso Legal & Juego Responsable

- **No afiliado** a Baloto, Coljuegos, ni operadores oficiales de lotería
- **Datos de fuentes públicas** (Kaggle, sitios de resultados históricos abiertos)
- **Solo fines educativos, académicos y de entretenimiento**
- **Juego responsable**: La ludopatía es una enfermedad reconocida. Si necesitas ayuda, busca apoyo profesional en líneas locales (Colombia: 018000 112 222).
- **Solo mayores de 18 años** en Colombia
- **No constituye asesoría financiera ni de apuestas**

## 🙏 Créditos & Agradecimientos

- **Autor**: Alejandro Quintero — Profesor de Estadística, Corporación Universitaria Iberoamericana
- **Datos**: [Javier Forero en Kaggle](https://www.kaggle.com/jaforero) (CC0 / MIT)
- **Gráficos**: [Chart.js](https://chartjs.org), [D3.js](https://d3js.org)
- **Iconos**: SVG inline, Emojis nativos Unicode
- **Inspiración**: Análisis estadístico de loterías mundiales, literatura de inferencia bayesiana
- **Comunidad**: A todos los que me preguntaron "¿y esto se puede hacer?" — **Sí, se puede. ¿Por qué no?**

---

<div align="center">

**Hecho con ❤️, 📊 y 🧮 para la comunidad de datos de Colombia y el mundo**

[![GitHub Stars](https://img.shields.io/github/stars/Cha0smagick/Baloto-oracle?style=social)](https://github.com/Cha0smagick/Baloto-oracle/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Cha0smagick/Baloto-oracle?style=social)](https://github.com/Cha0smagick/Baloto-oracle/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/Cha0smagick/Baloto-oracle)](https://github.com/Cha0smagick/Baloto-oracle/issues)

[Reportar Issue](https://github.com/Cha0smagick/Baloto-oracle/issues) • [Solicitar Feature](https://github.com/Cha0smagick/Baloto-oracle/issues/new) • [Ver Changelog](CHANGELOG.md)

</div>