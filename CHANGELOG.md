# Baloto Oracle - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-18

Auditoría completa (estadística, frontend, CI/CD, seguridad, accesibilidad) y corrección
de los defectos encontrados. El detalle con archivo y línea vive en `AUDIT.md`.

### Fixed — pérdida de datos
- El scraper se detenía en la página 125 y **sobrescribía** el histórico: entre 2026-09-06
  y 2026-11-18 se perdieron 31 sorteos de 2021 de forma irreversible desde el sitio.
  Ahora recorre hasta el fin real del historial (el deduplicado corta en la última página)
  y **fusiona por fecha** con el JSON existente, con escritura atómica (`.tmp` + `replace`).
- Aborta si la fusión fuera a perder sorteos, si el scrape viene vacío, o si se agota el
  deadline de 15 minutos.
- Histórico restaurado: 655 sorteos desde 2021-05-01 hasta 2026-11-16.

### Fixed — corrección estadística
- **Kruskal-Wallis sobre posiciones** era una tautología (`pos1 < pos2 < … < pos5` por
  construcción): p = 0 siempre. Sustituido por un χ² de cada posición contra la
  distribución nula exacta del estadístico de orden, con Bonferroni.
- **ANOVA de posiciones** en la validación: eliminada por el mismo motivo.
- **χ² de uniformidad**: la referencia correcta es `(38/42)·χ²₄₂` (muestreo sin reemplazo).
  El p publicado (0.9756) era falso; el correcto es 0.942.
- **"Ljung-Box"**: mezclaba 43 autocorrelaciones de lag 1 como si fueran 10 lags de una
  serie. Ahora es un portmanteau `Q = n·Σrᵢ² ~ χ²₄₃`.
- **Hot/cold**: el test binomial se aplicaba solo a los números ya filtrados por |z| > 1.5 y
  se corregía con m = 2. Ahora se testean los 43 y el FDR usa m = 43 (ninguno sobrevive).
- **Monte Carlo**: el z dividía dos veces por √n (`p = 4.48e-12` para una diferencia nula) y
  comparaba dos cantidades con la misma esperanza. Bloque eliminado.
- **Tabla 2×2 de co-ocurrencia**: usaba la suma de fila de una matriz simétrica (4·count) en
  vez del conteo de apariciones, inflando las celdas ×4 y fabricando p de 1e-79. Corregida,
  con FDR sobre los 903 pares.
- **Tendencias por número**: ventanas deslizantes de 1 en 1 (n efectivo ≈ 2) declaraban 37 de
  43 números "significativos". Ahora ventanas no solapadas + FDR: 0 significativos.
- **Beta-Binomial**: el prior incluía la ventana reciente y la likelihood la volvía a sumar.
  Prior y likelihood ya no se solapan.
- **Dispersión de gaps**: comparaba un cociente de varianzas contra χ² (solo válido para
  datos normales). Sustituido por un GOF χ² contra la geométrica.
- **Fisher**: reportaba el p del par más extremo de 903 sin corregir. Ahora incluye el
  veredicto FDR.
- **KS / Cramér-von Mises**: p asintóticos sobre datos discretos y no iid. Recalibrados por
  Monte Carlo (500 réplicas de la nula real).
- `power_analysis` post-hoc eliminado (`λ = χ² observado`: no informa de la potencia).
- `theoretical_std` era 27.75 (con reemplazo); el correcto es 26.39.
- `number_frequency_ci` no era un IC: renombrado a `expected_range_under_h0`.
- `jackpot_statistics` publicaba medias de n=1; ahora devuelve una nota honesta.
- Etiquetas de tamaño del efecto: `r` y `W` de Kendall tenían los umbrales de η².
- La conclusión de la validación es literal e incondicional: ahora se deriva de los p-valores.

### Fixed — frontend
- **"Top 10 números más probables" mostraba 1, 2, 3… 10**: las claves de `probabilities`
  son strings numéricos y `Object.entries` las devuelve en orden de índice entero, no de
  probabilidad. Ahora se ordena por valor.
- La vista de **jackpots** del visualizador pintaba `NaN` (621 de 622 jackpots son null).
- Controles muertos: `#freq-period` no tenía listener (eliminado).
- `renderInterpretation`, `renderPredictiveModeling` y `renderValidation` vivían dentro del
  gate de Chart.js/d3 aunque son HTML puro: si el CDN fallaba, quedaban en "Cargando…".
- Chart.js recibía `var(--x)`, que el canvas no resuelve: todos los ejes, títulos y tooltips
  usaban colores por defecto. Ahora se leen los valores computados y se re-aplican al cambiar
  de tema.
- Dataset vacío en el visualizador → `d3.extent([])` → paths con `NaN`.
- Tooltips d3 imprimían "Esperado: undefined" cuando el llamador no pasaba esos campos.
- La combinación sugerida mostraba un "probabilidad conjunta" que era el producto de
  marginales normalizadas, no una probabilidad. Ahora informa el odds real (1 entre 15.401.568).
- Superbalota: conteos rotulados como porcentajes y "caliente/frío" decidido por índice.
- La tarjeta del modelo bayesiano salía vacía (`top_5_most_likely` no estaba contemplado).
- Listeners duplicados al reintentar la carga.
- `api.countapi.xyz` está muerto (DNS inexistente): petición eliminada, contador local.

### Fixed — accesibilidad
- Contraste WCAG AA: `--text-muted` fallaba en ambos temas (3.37:1 y 3.40:1); tokens `*-ink`
  para los acentos usados como texto (amarillo sobre blanco era 1.24:1).
- `.btn-primary` con texto blanco sobre gradiente rojo→amarillo: 1.24:1 en el extremo.
- `.test-status.pass` se pintaba con el rojo de marca, indistinguible de un error.
- Skip link, `role="img"` + `aria-label` en los 10 canvas, `<caption>` y `scope="col"` en la
  tabla, `aria-hidden` en el canvas de fondo, `@media (prefers-reduced-motion)`.
- `.stat-mini` y `.no-data` no tenían CSS.

### Fixed — pipeline y CI
- `validate_baloto.py` no se invocaba en ningún workflow: la sección Validación servía JSON
  de meses atrás.
- `data.js` se publicaba sin validar, y el push del bot no dispara CI (GITHUB_TOKEN). Nuevo
  `scripts/verify_output.py` con asserts sobre el contrato, ejecutado antes del commit.
- Detección de cambios por `git diff`: `last_updated` cambiaba en cada corrida, así que el
  commit y el deploy corrían 1-2 veces al día sin datos nuevos.
- `upload-pages-artifact@v3` no tiene input `exclude`: se publicaba todo el repo. Ahora un
  staging `_site/`.
- Permisos por job (antes los tres jobs tenían `contents: write`).
- `concurrency` + reintento de push (un push rechazado perdía la actualización del día).
- El job de tests no podía fallar (`|| echo`): eliminado, y ahora hay 12 tests reales.
- `.gitignore` con reglas muertas que apuntaban a `baloto-oracle/` dentro del propio repo.
- `requirements.txt` con cotas superiores por major.
- `json.dumps` no escapaba `</` en el JSON embebido.
- Timestamps deterministas y cache-buster `?v=` derivado de la fecha del último sorteo.
- CDN con SRI y d3 fijado por versión (antes `d3.v7` era un alias móvil) + CSP por meta.

### Removed
- `jest` como dependencia (no había tests JS; `npm test` ahora verifica la sintaxis).
- Dependencias de `matplotlib`/`seaborn`/`plotly`/`kaleido` siguen declaradas pero ningún
  script las importa; se mantienen por compatibilidad con cuadernos externos.

## [1.0.0] - 2024-08-08

### Added
- 🎉 Initial release of Baloto Oracle
- Complete statistical analysis engine (descriptive + inferential)
- Interactive web frontend with Chart.js and D3.js visualizations
- Bayesian prediction system for next draw numbers
- Automated GitHub Actions for data updates and deployment
- GitHub Pages deployment configuration

### Statistics Implemented
- Number frequency heatmaps (1-43) with z-score detection
- Superbalota frequency analysis (1-16)
- Position analysis (1st-5th ball)
- Sum distribution with theoretical comparisons
- Odd/Even and High/Low balance charts
- Consecutive numbers and gap analysis
- Repeating numbers from recent draws
- Jackpot evolution tracking
- Baloto vs Revancha comparative analysis

### Inferential Tests
- Chi-square goodness-of-fit (uniformity test)
- Ljung-Box test (independence/autocorrelation)
- Binomial significance tests for hot/cold numbers
- Bonferroni correction for multiple comparisons
- 95% confidence intervals for key statistics

### Predictions
- Bayesian Beta-Binomial posterior probabilities
- Top 10 most likely numbers
- Top Superbalota predictions
- Suggested combination with joint probability

### Frontend Features
- Dark/Light theme with persistence
- Responsive design (mobile-first)
- Particle background animation
- Interactive visualizer with filters
- Latest draws table with visual balls
- Accessible navigation and ARIA labels

### Automation
- Scheduled updates (Mon/Wed/Sat after draws)
- Daily backup update
- CI pipeline (lint, test, HTML validation, link checking)
- Automatic GitHub Pages deployment

### Data Sources
- Official Baloto results (baloto.com/resultados), scraped desde 2021-05-01

[1.1.0]: https://github.com/Cha0smagick/Baloto-oracle/releases/tag/v1.1.0
[1.0.0]: https://github.com/Cha0smagick/Baloto-oracle/releases/tag/v1.0.0