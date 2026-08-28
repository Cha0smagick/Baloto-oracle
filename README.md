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
- **Chi-cuadrado bondad de ajuste** — H₀: distribución uniforme de números
- **Test Ljung-Box** — H₀: independencia entre sorteos (autocorrelación lags 1-10)
- **Test binomial exacto** — Significancia individual de números calientes/fríos
- **Corrección Bonferroni** — α = 0.05/43 ≈ 0.00116 para comparaciones múltiples
- **Intervalos de confianza 95%** — Wald (proporciones) y t-Student (medias)
- **Normalidad** — Shapiro-Wilk y Anderson-Darling para sumas de sorteos

#### Pruebas No Paramétricas
- **Mann-Whitney U** — Compara sumas entre sorteos impar-pesados vs par-pesados
- **Kruskal-Wallis** — Igualdad de distribuciones entre posiciones (1ª a 5ª bola)
- **Friedman** — Estabilidad de patrones consecutivos a través del tiempo (medidas repetidas)
- **Wilcoxon signed-rank** — Cambio sistemático en sumas: primera vs segunda mitad histórica

### 🤖 Modelado Predictivo Múltiple
- **Bayesiano (Beta-Binomial)** — Actualización conjugada prior + likelihood reciente
- **Cadenas de Markov** — Matriz de transición 43×43 entre sorteos consecutivos
- **Regresión lineal temporal** — Tendencias en sumas y frecuencias por ventana deslizante
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
- **Navegación accesible** — ARIA labels, focus visible, skip links
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

# Generar datos y análisis completo
python scripts/fetch_baloto_data.py
python scripts/analyze_baloto.py

# Servir frontend (requiere Node.js 18+)
npx serve .
# Abrir http://localhost:3000
```

## 🏗️ Arquitectura

```
baloto-oracle/
├── 📁 data/
│   ├── 📁 raw/           # CSVs originales (1455+ sorteos desde 2017)
│   └── 📁 processed/     # JSONs para frontend (baloto, revancha, metadata, analysis)
├── 📁 scripts/
│   ├── fetch_baloto_data.py    # Genera datos históricos sintéticos + reales
│   └── analyze_baloto.py       # Motor estadístico completo (800+ líneas)
├── 📁 src/
│   ├── 📁 js/main.js           # SPA vanilla ES Modules (600+ líneas)
│   ├── 📁 css/main.css         # CSS Variables, Grid/Flex, Animations (800+ líneas)
│   └── 📁 components/          # Componentes reutilizables
├── 📁 .github/workflows/
│   ├── update-data.yml         # Auto-update Lun/Mie/Sab 00:30 UTC + daily backup
│   └── ci.yml                  # Lint (ruff/black/isort), tests, HTML/links validation
├── index.html                  # SPA principal semántica + SEO
├── package.json                # Node deps (serve, chartjs-plugin-annotation)
├── requirements.txt            # Python deps (pandas, scipy, statsmodels, etc.)
├── README.md                   # Este archivo
├── LICENSE                     # MIT
└── CHANGELOG.md                # Keep a Changelog format
```

## 🔄 Actualización Automática (GitHub Actions)

| Trigger | Frecuencia | Acción |
|---------|------------|--------|
| `schedule` | Lun/Mie/Sab 00:30 UTC | Descarga nuevos sorteos, recalcula análisis completo, despliega |
| `schedule` | Diario 06:00 UTC | Backup por si falla el principal |
| `workflow_dispatch` | Manual | Fuerza actualización completa (`force_update: true`) |
| `push` | Cada commit | Lint (ruff/black/isort), pytest, HTML validation, link check |

**Despliegue**: GitHub Pages automático tras actualización exitosa.  
**Notificaciones**: Workflow `notify` en cambios detectados.

## 📈 Metodología Estadística Detallada

### Datos
- **Fuentes**: Kaggle (jaforero/baloto-colombia 2017+, jforero/resultados-baloto 2021+)
- **Período**: Abril 2017 – presente (cambio formato 5/43 + 1/16 Superbalota)
- **Sorteos**: Lunes, Miércoles, Sábado · 23:00 COT · Canal RCN
- **Formato**: 5 números (1–43) + 1 Superbalota (1–16)
- **Premios**: 9 categorías · Odds jackpot 1:15.4M · Odds cualquier premio 1:19.34

### Análisis Descriptivo
- Frecuencias absolutas/relativas con **z-scores** (z > 1.5 caliente, z < -1.5 frío)
- Estadísticos por posición (media, mediana, desv. est. por bola 1–5)
- Sumas: media teórica 110, desv. teórica ~19.8, percentiles 25/50/75/90/95
- Paridad: 6 patrones (5-0 a 0-5) con % observado vs teórico
- Rango: Alto (23–43) vs Bajo (1–22), mismos 6 patrones
- Consecutivos: Distribución 0–3+ pares, probabilidad ≥1 par
- Gaps: Media, mediana, distribución de diferencias entre bolas adyacentes
- Repeticiones: Ventana 10 sorteos, números que reaparecen

### Inferencial Paramétrico
| Prueba | H₀ | Estadístico | Decisión |
|--------|-----|-------------|----------|
| Chi² bondad ajuste | Uniforme 1/43 | χ²(42) | p ≥ 0.05 → No rechazar |
| Ljung-Box (lags 1-10) | Independencia | Q(10) | p ≥ 0.05 → No rechazar |
| Binomial (cada número) | p = 5/43 | Exacto | Bonferroni α/43 |
| IC 95% media sumas | μ = 110 | t-Student | [105, 115] típico |
| IC 95% prop. números | p = 5/43 | Wald (Normal) | [0.095, 0.135] |
| Shapiro-Wilk (sumas) | Normalidad | W | p < 0.05 → No normal |
| Anderson-Darling | Normalidad | A² | A² > crítico 5% → No normal |

### Inferencial No Paramétrico
| Prueba | Comparación | Uso |
|--------|-------------|-----|
| Mann-Whitney U | Suma (impar-pesado vs par-pesado) | ¿Influye paridad en suma? |
| Kruskal-Wallis | Distribución por posición (1–5) | ¿Posiciones equivalentes? |
| Friedman | Consecutivos por trimestre | ¿Patrón estable en tiempo? |
| Wilcoxon signed-rank | Sumas 1ª mitad vs 2ª mitad | ¿Deriva temporal? |

### Modelado Predictivo (Solo Académico)

**Bayesiano (Beta-Binomial conjugado)**
```
Prior:     Beta(α = count_total + 1, β = total_draws×5 - count_total + 1)
Likelihood: Binomial(n = recent_draws×5, p)
Posterior: Beta(α + count_recent, β + recent_draws×5 - count_recent)
P(next) = E[Posterior] = (α + count_recent) / (α + β + recent_draws×5)
Normalizado a 5 números por sorteo
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