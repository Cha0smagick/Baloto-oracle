# Auditoría quirúrgica — Baloto Oracle

**Fecha:** 2026-11-18
**Alcance:** `baloto-oracle` completo — frontend (HTML/CSS/JS), pipeline Python (scrape → análisis → validación → generación), CI/CD, accesibilidad y cadena de suministro.
**Base auditada:** `origin/master` @ `4b36ef0` (2026-11-18). El working tree local estaba 114 commits por detrás; se sincronizó antes de auditar.
**Método:** cuatro auditores especializados en paralelo (corrección estadística, frontend, CI/CD, seguridad) + verificación propia con ejecución real: lint (`ruff`/`black`/`isort`), `node --check`, Playwright sobre `http://127.0.0.1:8765` (captura de errores de consola, inspección de DOM renderizado y screenshots), recálculo de los estadísticos con `numpy`/`scipy` sobre `data/processed/baloto.json`, y sondeo HTTP de `baloto.com/resultados` (páginas 1, 2, 125, 126, 130, 200, 203–220).

---

## Resumen ejecutivo

El proyecto está mejor construido de lo que sugiere su README, y peor de lo que sugiere su portada. Tres cosas se sostienen bien: el diseño visual, el aislamiento de fallos de `loadData` y la honestidad del mensaje ("los sorteos son aleatorios"). Tres cosas están rotas de forma grave:

1. **Pérdida de datos activa.** El scraper se detiene en la página 125 y sobrescribe el histórico. Entre 2026-09-06 y hoy se perdieron **31 sorteos** de 2021 de forma silenciosa e irreversible desde el sitio.
2. **La página miente en dos lugares visibles.** El "Top 10 números más probables" muestra 1, 2, 3… 10 porque las claves del objeto JSON se iteran en orden numérico, no por probabilidad. Y cuatro de las pruebas inferenciales publicadas (Kruskal-Wallis de posiciones, ANOVA de posiciones, dispersión de gaps, z de Monte Carlo) tienen nula mal especificada: reportan hallazgos que son tautologías o artefactos de fórmula.
3. **El pipeline publica JSON congelado.** `validate_baloto.py` no se invoca en ningún workflow, así que la sección "Validación Estadística" sirve datos del 2026-08-28 mientras los sorteos van al 2026-11-16.

Todo lo anterior es corregible con cambios pequeños y localizados. Ninguno requiere rediseño.

---

## Hallazgos

Severidad: **C** = crítico (dato perdido, afirmación falsa visible, pérdida de historia), **A** = alto (funcionalidad rota o resultado inválido en producción), **M** = medio (defecto real con impacto acotado), **B** = bajo (higiene, rendimiento, accesibilidad menor).

### C1. El scraper trunca el histórico en 625 sorteos y borra los antiguos — *pérdida de datos*
`scripts/fetch_baloto_data.py:49` (`MAX_PAGES = 125`) y `:189-220` (el loop escribe encima de los CSV/JSON existentes sin fusionar).
125 páginas × 5 sorteos = 625. El sitio oficial devuelve datos hasta la página ~202 (2021-05-01); el scraper nunca llega. Cada corrida gana 3 sorteos nuevos por la cabeza y pierde 3 por la cola.
**Verificado:** el dataset pasó de 1455 sorteos (2017) a 621 (2021-05) en un commit anterior, y entre 2026-09-06 y 2026-11-18 perdió 31 sorteos (`2021-05-01 → 2021-08-11`). Sonda HTTP: `page=200` sigue devolviendo `15 de Mayo de 2021`; `page=220` devuelve la misma página (el sitio clampea), así que el fin real del historial está en ~202 y el `new_rows == 0` ya lo detecta.
**Corrección:** subir el tope a 400 (el corte real lo da el dedup), y **fusionar por fecha** con el `baloto.json`/`revancha.json` existentes antes de escribir. Un scrape nunca debe poder reducir el histórico.

### C2. Un scrape parcial sobrescribe el histórico completo — *pérdida de datos*
`scripts/fetch_baloto_data.py:283-285`. La única validación es `if not baloto: sys.exit(1)`. Si la página 40 falla tres veces, `scrape_all` hace `break` y `run()` escribe 195 sorteos encima de 656.
**Corrección:** abortar si el resultado pierde sorteos respecto al archivo existente; escribir a `.tmp` y `replace()` atómico.

### C3. "Top 10 números con mayor probabilidad" muestra 1, 2, 3… 10
`src/js/main.js:1161` y `:1178`. `Object.entries(probabilities)` sobre claves `"1".."43"` las enumera en orden de índice entero ascendente, no en el orden del JSON (que sí viene ordenado por probabilidad).
**Verificado en navegador:** el bloque renderiza `1,2,3,4,5,6,7,8,9,10` con porcentajes no monótonos (11.17 %, 11.90 %, 11.17 %, 11.46 %, 12.93 %, 9.40 %…). `top_10_most_likely` real es `[9,14,32,5,25,35,43,21,8,42]`.
**Corrección:** ordenar por valor antes de cortar (`sort((a,b) => b[1]-a[1])`), o usar el array `top_10_most_likely` que ya existe.

### C4. Kruskal-Wallis sobre posiciones: tautología publicada como hallazgo
`scripts/analyze_baloto.py:746-772`. Las 5 "posiciones" son las 5 balotas de un sorteo **ya ordenado**: `pos1 < pos2 < … < pos5` en toda fila. La nula "las 5 distribuciones son idénticas" es falsa con probabilidad 1 bajo el modelo correcto.
**Verificado:** `statistic = 2174.36`, `p_value = 0.0`, y la web lo imprime en "Conclusiones Principales" bajo *Posición* como "At least one position differs in distribution". El η² = 0.699 mide el `sorted()`, no la lotería.
**Corrección:** sustituir por un test con nula correcta — χ² de bondad de ajuste de cada posición contra su distribución nula exacta (estadístico de orden *i*-ésimo de una 5-subconjunto de 1..43, calculable en forma cerrada con combinatoria).

### C5. ANOVA de posiciones en la sección de validación: mismo defecto
`scripts/validate_baloto.py:516-525`. `F = 1799`, `p = 0.00e+00`, renderizado como badge **"NO PASADA"** en el tablero. Es el mismo ordenamiento estructural.
**Corrección:** eliminar el bloque y su `addTest`.

### C6. Tabla 2×2 de co-ocurrencia construida con la suma de fila de una matriz simétrica
`scripts/validate_baloto.py:368-370`. `cooc[a].sum()` sobre una matriz simétrica cuenta **pares**, no apariciones: da `4·count(a)`. Las celdas de discordancia salen infladas ×4 y el χ² resultante es basura.
**Verificado con el par (1,3):** tabla del código `[[6,278],[262,76]]` → `p = 3.9e-79`; tabla correcta `[[6,65],[61,490]]` → `p = 0.64`. El JSON publicado trae `pvalue: 1.8e-79` con `fdr_significant: true` y una conclusión "Posible estructura débil" que es falsa.
**Corrección:** contar apariciones por número una vez y derivar las celdas; recalcular FDR sobre los 903 pares (no sobre los 652 que sobreviven al filtro de celda).

### C7. z de Monte Carlo dividido dos veces por √n
`scripts/validate_baloto.py:182-186`. `mc_hits` ya es una media por sorteo (cada simulación divide por 150); dividir otra vez por `√150` infla z ×12.2.
**Verificado por el auditor:** reportado `z = -6.921, p = 4.48e-12`; correcto `z ≈ -0.565, p ≈ 0.572`. La web lo muestra como "Monte Carlo z-score: -6.921 (p=4.48e-12)" y como test "NO PASADA".
Además la línea base MC mide `|aleatorio ∩ top10|` y el modelo `|real ∩ top10|`: **misma esperanza** (5·10/43). El test no puede detectar nada por diseño.
**Corrección:** usar el binomial exacto que ya existe y eliminar el bloque MC, o corregir el denominador. Se elimina: no aporta y confunde.

### C8. Ljung-Box mezcla 43 series distintas como si fueran 10 lags
`scripts/analyze_baloto.py:499-506`. `autocorrelations` son las 43 autocorrelaciones de **lag 1 de 43 series binarias**; `enumerate(...,1)` las etiqueta como lags 1..10 de una sola serie. El estadístico no tiene distribución conocida; el `p = 0.5038` publicado no significa nada.
**Verificado:** el portmanteau correcto `Q = n·Σr_i² ~ χ²_43` da `Q = 37.09, p = 0.7246`.
**Corrección:** `Q = n·Σr²` con `χ²_43` (una línea), y `chi2.sf` en vez de `1-cdf` para evitar subflujo.

### C9. χ² de uniformidad con nula incorrecta (ignora muestreo sin reemplazo)
`scripts/analyze_baloto.py:432-449`. Los grados de libertad y los esperados están bien, pero bajo muestreo de 5 de 43 las celdas no son multinomiales: `Var(O_i) = n·p(1-p)·38/42`, así que la referencia correcta es `(38/42)·χ²_42`.
**Verificado:** `X² = 25.9305`; publicado `p = 0.9756`, correcto `p = 0.942`. La conclusión no cambia, pero el test es sistemáticamente conservador y el p publicado es falso.
**Corrección:** `p = chi2.sf(X² / (38/42), 42)`. Renombrar `cramers_v` → `cohens_w` (para una tabla 1×43 el denominador de V de Cramér es 0).

### C10. Benjamini-Hochberg aplicado con m = 2 en vez de m = 43
`scripts/analyze_baloto.py:549-556`. Los p-valores se calculan **solo** para los números que ya pasaron el filtro `|z| > 1.5`, y luego se corrige con `m = 2`. Selección sobre los datos + corrección con el tamaño del subconjunto: anti-conservador por construcción.
**Verificado:** con m = 43, el umbral BH del rango 1 es 0.00116 y **nada sobrevive** (p mínimo bilateral de los 43 números = 0.036). El "Calientes Sig. FDR 1/1" que muestra la web es un artefacto.
**Corrección:** test binomial de los 43 números, `_fdr_bh` sobre los 43, filtrar después. `_fdr_bh` ya está bien implementado.

### C11. Tendencias por número sobre ventanas solapadas
`scripts/analyze_baloto.py:942-966`. Ventana de 100 desplazada de uno en uno: cada punto comparte 99/100 con el anterior (n efectivo ≈ 2-3) y el OLS asume independencia.
**Verificado por el auditor:** `total_significant: 37` de 43. Bajo H0 se esperan 2.15 ± 1.4; la probabilidad de 37 es indistinguible de cero. El test está roto, no hay tendencias.
**Corrección:** ventanas no solapadas + FDR sobre los 43 p-valores.

### C12. `validate_baloto.py` no se ejecuta en ningún workflow
`.github/workflows/update-data.yml`. `generate_data_js.py:61-64` embebe `validation_results.json` si existe, así que la sección Validación sirve datos del **2026-08-28** mientras los sorteos van al **2026-11-16**. En producción convive con la tabla de co-ocurrencia de C6: muestra `fdr_significant: true` en 5 pares mientras la conclusión dice "sin asociación".
**Corrección:** añadir el step `python scripts/validate_baloto.py` antes de `generate_data_js.py`.

### C13. Nada valida `data.js` antes de publicarlo, y el push del bot no dispara CI
`update-data.yml:59-68` (el "verify" solo imprime), `:76` (push con `GITHUB_TOKEN`, que **no** genera runs de workflow). Un `data.js` corrupto se publica sin gate.
**Corrección:** script de verificación con `assert` (parsea `data.js`, compara conteo y fecha final con `baloto.json`) que corre antes del commit y del upload.

### A1. La vista "Jackpots" del visualizador pinta `NaN`
`src/js/main.js:1747`. `d3.max(sortedData, d => d.jackpot) * 1.1` con 621/622 jackpots `null` → `domain([0, NaN])`.
**Verificado en navegador:** el `path` renderizado es `M60,NaNC60.884,NaN,...`.
**Corrección:** filtrar puntos con jackpot, y si quedan menos de 2 mostrar un mensaje honesto (solo se guarda el jackpot del último sorteo).

### A2. Control muerto `#freq-period`
`index.html:147-154`. El `<select>` "Todo el historial / Últimos 50/20/10" no tiene listener en ningún archivo: `createFrequencyHeatmap` siempre usa el análisis completo. Además es el único control sin `<label>`.
**Corrección:** eliminar el control (deletar es mejor que cablear una funcionalidad a medias).

### A3. `initializeCharts()` no aísla fallos
`src/js/main.js:340-356`. 15 llamadas en un solo `try`. Un throw en cualquier chart se lleva por delante `renderInterpretation`, `renderPredictiveModeling` y `renderValidation`, que son HTML puro y no necesitan Chart ni d3.
**Corrección:** sacar las tres últimas a su propio `try` en `loadData`.

### A4. Validación y Tablero quedan en "Cargando…" si falla el CDN
`src/js/main.js:209` (gate `typeof Chart/d3`), `:1287-1289` (`return` si falta `blind_test`). Ambas secciones son HTML puro pero viven dentro del gate; el tablero además se corta aunque `analysis.predictions` esté completo.
**Corrección:** moverlas fuera del gate y relajar la guarda.

### A5. Chart.js recibe `var(--x)`: canvas no resuelve variables CSS
`src/js/main.js:913-916, 943, 945-948, 959, 962-963, 985`. Todos los títulos, ticks, grid, leyendas y tooltips de los 11 gráficos usan colores literales inválidos.
**Verificado en navegador:** `chart.options.scales.y.ticks.color === "var(--text-muted)"`; el canvas conserva el color anterior (negro por defecto). El toggle de tema no arregla nada porque el valor nunca fue válido.
**Corrección:** helper `cssVar()` que lea `getComputedStyle` una vez, y re-aplicar en el toggle.

### A6. Dataset vacío → SVG con `NaN`
`src/js/main.js:1610, 1614, 1693, 1743`. El filtro de período usa `new Date()` real: hoy (2026-11-18) el último sorteo es 2026-08-29, así que "Último mes" devuelve 0 sorteos y `d3.extent([])` es `[undefined, undefined]`.
**Corrección:** guarda temprana con mensaje si el filtro deja el dataset vacío.

### A7. Contraste WCAG insuficiente (calculado con la fórmula WCAG 2.2)
| Combinación | Ratio | Umbral | Estado |
|---|---|---|---|
| `--text-muted` #6a6a7a / `--bg-card` #161624 (dark) | **3.37** | 4.5 | falla |
| `--text-muted` #8a8a9a / `--bg-card` #ffffff (light) | **3.40** | 4.5 | falla |
| `--accent-primary` #ED1C24 / `--bg-card` #161624 | **4.08** | 4.5 | falla |
| blanco / `--accent-primary` (botón) | **4.38** | 4.5 | falla |
| `--accent-secondary` #FFE903 / blanco (light, texto) | **1.24** | 4.5 | falla |
| `--accent-tertiary` #FFB900 / blanco (light, texto) | **1.72** | 4.5 | falla |

`--text-muted` se usa en 15 reglas (labels de ejes, subtítulos, `.stat-label`). Los acentos en tema claro son ilegibles como texto.
**Corrección:** subir `--text-muted` en ambos temas y añadir tokens `*-ink` para los acentos usados como texto, con valores por tema. No tocar los acentos de fondo (identidad de marca).

### A8. `.btn-primary` con texto blanco sobre gradiente rojo→amarillo (tema claro)
`src/css/main.css:476-480` + `:60` (`--text-inverse: #ffffff`). Blanco sobre #FFE903 = **1.24:1**.
**Corrección:** gradiente rojo oscuro→rojo con texto blanco, en ambos temas.

### A9. `.test-status.pass` se pinta como error
`src/css/main.css:613-616` y `:638-641`: el estado "pasada" usa el rojo de marca (`rgba(237,28,36,.1)` y fondo `--accent-primary`). En pantalla, una prueba superada se ve idéntica a una alerta.
**Corrección:** verde para `.pass`.

### A10. Regresión logística / RF / AUC no verificables, pero `power_analysis` es un número inventado
`scripts/analyze_baloto.py:423-430, 469-476`. `λ = n·w² = χ² observado`, así que "power_at_05" es una transformación monótona del p-valor: no informa de la potencia del estudio. Y `n` debería ser 622 sorteos, no 3110 balotas.
**Corrección:** eliminar `power_analysis` y `_power_chi2_gof` (el frontend ya lo trata como opcional).

### A11. `number_frequency_ci` no es un intervalo de confianza
`scripts/analyze_baloto.py:684-688`. Se centra en el valor **teórico** `5/43` y no usa ninguna estimación: es una banda de aceptación bajo H0, idéntica para los 43 números, publicada como "IC 95 % de la frecuencia de un número".
**Corrección:** renombrar a `expected_range_under_h0` y rotularlo como tal en la UI.

### A12. Beta-Binomial: la ventana reciente se cuenta dos veces
`scripts/analyze_baloto.py:600-617` y `scripts/validate_baloto.py:84-104`. El prior usa el conteo de **todos** los sorteos (incluidos los últimos 50) y luego se suman otra vez los últimos 50. En `validate` además `alpha + beta = total + 2` con los aciertos inflados.
No es un posterior conjugado; es un shrinkage con la recencia sobreponderada ×2, etiquetado "conjugate prior".
**Corrección:** prior sobre `draws[:-lookback]`, likelihood sobre `draws[-lookback:]`.

### A13. `z_score` de frecuencia usa √E en vez de √(n·p·(1-p))
`scripts/analyze_baloto.py:117-121, 166`. Infla cada z en `1/√0.8837 = 6.4 %`. Con los datos: max |z| publicado 2.078, correcto 2.211.

### A14. Fisher exacto sobre el par de **máxima** co-ocurrencia, sin corregir por 903 comparaciones
`scripts/validate_baloto.py:536-548`. El p de un máximo seleccionado no es un p-valor (`P(min p ≤ α) ≈ 1-(1-α)^903`).
**Corrección:** reportar el par más fuerte con su p ajustado por BH sobre los 903 pares.

### A15. La conclusión de `inferential_exact` es un string literal
`scripts/validate_baloto.py:602-605`. Afirma "todos los tests son consistentes" de forma incondicional, aunque en el mismo diccionario viaje un test con p = 0.
**Corrección:** derivarla de los p-valores.

### A16. CDN sin SRI y d3 en versión flotante
`index.html:16-25`. Cuatro scripts de terceros ejecutan en el origen. `d3.v7.min.js` es un alias móvil: una release futura entra sin cambiar nada. Sin SRI ni CSP no hay detección.
**Corrección:** mover d3 a jsDelivr con versión exacta, añadir `integrity` + `crossorigin` a los cuatro, y una CSP por `<meta>`.

### A17. `api.countapi.xyz` está muerto
`src/js/main.js:1982`. DNS inexistente (`ERR_NAME_NOT_RESOLVED` en cada carga, confirmado en consola del navegador). El contador mostrado es en realidad `localStorage` por navegador. El namespace público era escribible de todos modos.
**Corrección:** eliminar la petición y rotular el contador como local.

### M1. `.stat-mini` sin CSS
`main.js:635-640` genera 4 `.stat-mini`; no existe la regla. Se apilan verticalmente sin separación (102 px de alto, verificado).

### M2. Las 5 series del gráfico de posición son del mismo rojo
`main.js:586`. `gradients.primary[idx % 2]` alterna `#ED1C24` y `#E30613`: indistinguibles en pantalla.

### M3. Tooltips d3 muestran `undefined`
`main.js:519-525` imprime siempre `Esperado`, `Desviación`, `Z-score`; el visualizador le pasa `{count, percentage}` o `{sum, numbers, superbalota}`.

### M4. Superbalota: conteos rotulados como porcentajes y "caliente/frío" por índice
`main.js:544-545, 555-563, 569`. `showPercent=true` sobre conteos; el color resalta 1,2,3 y 14,15,16 por posición, no por frecuencia (el JSON ya trae `hot_superbalotas`).

### M5. Tarjeta "Modelo Bayesiano" vacía
`main.js:1246-1253`. `getTopNumbers` no busca `top_5_most_likely`, que es la clave real.

### M6. `toFixed` sobre valores que pueden ser string
`main.js:1046, 1052, 1058, 1063`. Hoy `analysis_results.json` trae números, pero `validation_results.json` del mismo pipeline emite strings (`"binom_pvalue_top10": "0.7234"`). Un `"0.72".toFixed()` es `TypeError` y, por A3, se lleva 4 secciones.

### M7. Listeners duplicados al reintentar
`main.js:1474-1491` invocado desde `loadData:220`; el botón de reintento vuelve a llamar `loadData` y añade otro `change` a los 3 selects y otro `click` al refresh.

### M8. Sin `defer` en los 4 scripts CDN
`index.html:16-25`: ~480 KB render-blocking en `<head>`.

### M9. Gráficos d3 no se redimensionan
`main.js:399-403, 1510-1519`: el ancho se congela al renderizar; solo las partículas escuchan `resize`.

### M10. El bucle de partículas no se pausa por código
`main.js:1932, 2074-2077`: `visibilitychange` solo oculta el canvas; no hay `cancelAnimationFrame`. El README afirma que pausa. Además `main.css:1324` usa `.bg-canvas` (clase) cuando el elemento es `#bg-canvas` (id), y falta `aria-hidden`.

### M11. `rgba(var(--bg-secondary), 0.9)` es CSS inválido
`main.css:238`: `var()` expande a `#12121e`, y `rgba(#12121e, .9)` no es válido → la navbar queda sin fondo declarado.

### M12. `upload-pages-artifact@v3` no tiene input `exclude`
`update-data.yml:92-102`: se ignora con warning y publica `scripts/`, `requirements.txt`, `pyproject.toml`, `data/raw/*.csv`, README y CHANGELOG.
**Corrección:** staging `_site/`.

### M13. Detección de cambios siempre `true`
`update-data.yml:46`. `git diff --quiet data/` nunca está limpio porque `write_metadata` escribe `last_updated = now()` en un archivo trackeado. Resultado: commit + deploy 1-2 veces al día sin datos nuevos, y `force_update` decorativo.
**Corrección:** comparar `total_draws`/`date_range.end` antes y después.

### M14. El job `test` no puede fallar
`ci.yml:47`: `pytest ... || echo "No tests found"`. `pytest` sin tests devuelve exit 5 y el `||` lo tapa. No existe ningún test en el repo.

### M15. `permissions` a nivel de workflow
`update-data.yml:15-18`: los tres jobs reciben `contents: write` + `pages: write` + `id-token: write`. `notify` solo hace `echo`.
**Corrección:** permisos por job.

### M16. `git push` sin `concurrency` ni reintento
`update-data.yml:76`: dos crons + dispatch pueden chocar con un push humano; el push se rechaza y la actualización del día se pierde en silencio.

### M17. `requirements.txt` con `>=` abiertos
Sin lock ni hashes, en un job con `contents: write` que commitea JavaScript ejecutable. Un major nuevo entra solo.

### M18. `.gitignore` con reglas muertas
`:159-161`: `baloto-oracle/data/raw/*.csv` — el repo root **es** `baloto-oracle`, así que no matchea nada (verificado: `git check-ignore data/processed/baloto.json` → exit 1). Y si alguien "arregla" el prefijo, rompe el deploy.

### M19. README con datos falsos
`README.md:94, 129, 138`: "1455+ sorteos desde 2017", "Abril 2017 – presente", "desv. teórica ~19.8", "Genera datos históricos sintéticos + reales", "skip links", "600+ líneas". Real: 656 sorteos desde 2021-05-01, desv. teórica 26.40, sin datos sintéticos (se eliminaron), sin skip links (hasta ahora).

### M20. `json.dumps` no escapa `</`
`generate_data_js.py:78-84`: si un día un campo de texto libre llega al JSON con `</script>`, cierra el tag. Hoy no es explotable (todos los campos son numéricos o literales validados) pero el invariante vive solo en la cabeza de quien escriba el próximo script.

### M21. Timestamps no deterministas en el artefacto
`generate_data_js.py:73`, `analyze_baloto.py:1133`, `metadata.last_updated`: mismo input, bytes distintos en cada corrida. Es la causa raíz de M13.

### M22. Falta `@media (prefers-reduced-motion)`
Solo existe la clase `.reduce-motion` aplicada por JS; las animaciones CSS (keyframes, transitions) no respetan la preferencia del sistema.

### M23. Accesibilidad estructural
- 10 `<canvas>` sin `role="img"` ni `aria-label`.
- `#latest-draws-table` sin `<caption>` ni `scope="col"`.
- Sin skip link (el README lo prometía).
- `#predictive` y `#prediction-dashboard` existen pero no están en la navegación.
- Celdas del mapa de calor d3 solo accesibles con ratón.

### B1. isort no parsea 3 de 4 archivos en Windows
Encoding cp1252 al leer archivos con `≤`, `→`. En CI (UTF-8) pasa. Añadir `encoding="utf-8"` a los `open()` del pipeline lo hace determinista en ambas plataformas.

### B2. Cuatro `open()` sin `encoding="utf-8"`
`analyze_baloto.py:74-78, 1141` y otros: dependen del locale.

### B3. `_effect_size_label` no tiene rama para `r`
`analyze_baloto.py:388-402`: un `r = 0.0451` sale etiquetado "mediano" porque cae en el `else` con umbrales de η².

### B4. `jackpot_statistics` calculado sobre 1 observación
`analyze_baloto.py:348-378`: con 621 NaN, `mean/median/max/min/std` salen `null` y `total_rollovers = 0`. No crashea, pero publica estadísticos de una muestra.
**Corrección:** guarda `if notna().sum() < 2`.

### B5. Shapiro sobre una suma discreta y acotada
`analyze_baloto.py:846-882`: la suma de 5 enteros de 1..43 tiene soporte finito [15, 215]; no puede ser normal. "No rechazar" es lo esperado, no un hallazgo. Falta asimetría y curtosis.

### B6. `probability_at_least_one: 100.0` sin línea base
`analyze_baloto.py:323-346`: "repite al menos un número de los últimos 10 sorteos" es 100 % por construcción (la unión de 10 sorteos cubre ~72 % del espacio). Falta el valor esperado al lado (3.61 repeticiones).

### B7. Cache-buster fijo
`index.html:598-599`: `?v=20260827` nunca se actualiza; tras un update de datos el navegador puede servir `data.js` viejo.

### B8. `np.random.choice` sin semilla
`analyze_baloto.py:850, 868`: hoy muestrea la población completa (invariante), pero con >5000 sorteos se vuelve no determinista.

---

## Plan atómico de corrección

Cada paso es independiente y verificable. El orden respeta dependencias: datos antes que análisis, análisis antes que frontend (el frontend consume el JSON regenerado).

### Fase 1 — Integridad de datos (bloquea todo lo demás)
- [x] **1.1** `fetch_baloto_data.py`: `MAX_PAGES` 125 → 400 (el corte real lo da el dedup de filas).
- [x] **1.2** `fetch_baloto_data.py`: fusionar por fecha con el JSON existente antes de escribir (unión, los nuevos ganan en conflicto).
- [x] **1.3** `fetch_baloto_data.py`: abortar si el resultado pierde sorteos respecto al archivo previo; escritura atómica vía `.tmp` + `replace()`.
- [x] **1.4** `fetch_baloto_data.py`: `encoding="utf-8"` en todos los `open()`; deadline global para no colgar el job.
- [x] **1.5** Restaurar el histórico perdido: ejecutar el scraper corregido y verificar que recupera 2021-05-01 → hoy (≥ 656 sorteos).

### Fase 2 — Corrección estadística (`analyze_baloto.py`)
- [x] **2.1** χ² de uniformidad: `p = chi2.sf(X²/(38/42), 42)`; renombrar `cramers_v` → `cohens_w`.
- [x] **2.2** Ljung-Box: `Q = n·Σr_i²` sobre las 43 series, `χ²_43`, `chi2.sf`.
- [x] **2.3** `z_score`: `√(E·(1-p))` en vez de `√E`.
- [x] **2.4** Hot/cold: binomial de los 43 números, `_fdr_bh` con m = 43, filtrar después.
- [x] **2.5** Eliminar `power_analysis` y `_power_chi2_gof`.
- [x] **2.6** `theoretical_std` → `sqrt(5·44·38/12) = 26.40`.
- [x] **2.7** Beta-Binomial: prior sobre `df[:-lookback]`, likelihood sobre `df[-lookback:]`.
- [x] **2.8** `number_frequency_ci` → `expected_range_under_h0` con interpretación honesta.
- [x] **2.9** Tendencias: ventanas no solapadas + FDR sobre los 43 p.
- [x] **2.10** Sustituir Kruskal-Wallis de posiciones por χ² de bondad de ajuste contra la distribución nula exacta del estadístico de orden (combinatoria en forma cerrada).
- [x] **2.11** `_effect_size_label`: ramas para `r` y `w`.
- [x] **2.12** `jackpot_statistics`: guarda si hay < 2 observaciones.
- [x] **2.13** Shapiro: texto correcto + asimetría/curtosis.
- [x] **2.14** `repeating_numbers`: añadir línea base teórica.
- [x] **2.15** `encoding="utf-8"` + `np.random.default_rng(42)`.
- [x] **2.16** `analysis_date` derivado del dato (determinismo).

### Fase 3 — Corrección estadística (`validate_baloto.py`)
- [x] **3.1** Tabla 2×2 de co-ocurrencia con conteos reales; FDR sobre los 903 pares.
- [x] **3.2** Eliminar ANOVA de posiciones y su `addTest`.
- [x] **3.3** Eliminar el bloque Monte Carlo (misma esperanza que el modelo; denominador roto).
- [x] **3.4** Fisher: par más fuerte con p ajustado por BH.
- [x] **3.5** KS y CvM: recalibrar el p por simulación de la nula (622 sorteos uniformes, 500 réplicas).
- [x] **3.6** Gaps: χ² de bondad de ajuste geométrico por bins; eliminar `mean_dispersion_pvalue`.
- [x] **3.7** Beta-Binomial sin doble conteo.
- [x] **3.8** Markov: normalizar por fila antes de rankear.
- [x] **3.9** Conclusión derivada de los resultados, no literal.
- [x] **3.10** `validation["data"]` coherente con el dataset actual.

### Fase 4 — Frontend (`main.js`, `index.html`, `main.css`)
- [x] **4.1** Ordenar top-10 por probabilidad (C3).
- [x] **4.2** Jackpots: filtrar nulls y mensaje si no hay datos (A1).
- [x] **4.3** Eliminar `#freq-period` (A2).
- [x] **4.4** Sacar `renderInterpretation`/`renderPredictiveModeling`/`renderValidation` del gate Chart+d3 y aislar cada una en su `try` (A3, A4).
- [x] **4.5** `cssVar()` + re-aplicar colores en el toggle de tema (A5).
- [x] **4.6** Guarda de dataset vacío en el visualizador (A6).
- [x] **4.7** Contraste: `--text-muted` y tokens `*-ink` (A7).
- [x] **4.8** `.btn-primary` legible en ambos temas (A8).
- [x] **4.9** `.test-status.pass` en verde (A9).
- [x] **4.10** `.stat-mini` con CSS (M1).
- [x] **4.11** Paleta de 5 colores para posiciones (M2).
- [x] **4.12** Tooltips d3 genéricos (M3).
- [x] **4.13** Superbalota: porcentajes reales y hot/cold por frecuencia (M4).
- [x] **4.14** `getTopNumbers` con `top_5_most_likely` (M5).
- [x] **4.15** `Number()` antes de `toFixed` (M6).
- [x] **4.16** Guarda anti-listeners duplicados (M7).
- [x] **4.17** `defer` en los CDN + SRI + d3 exacto (A16, M8).
- [x] **4.18** Redimensionado debounced de los SVG d3 (M9).
- [x] **4.19** Partículas: `cancelAnimationFrame`, `aria-hidden`, regla de impresión (M10).
- [x] **4.20** Nav: enlaces a `#predictive` y `#prediction-dashboard` (M23).
- [x] **4.21** A11y: `role="img"`+`aria-label` en canvas, `caption`+`scope` en tabla, skip link (M23).
- [x] **4.22** Eliminar `api.countapi.xyz` (A17).
- [x] **4.23** `rgba(var(...))` inválido → fondo de navbar válido (M11).
- [x] **4.24** `@media (prefers-reduced-motion)` global (M22).
- [x] **4.25** CSP por `<meta>` (A16).

### Fase 5 — Pipeline y CI
- [x] **5.1** Añadir `validate_baloto.py` al workflow (C12).
- [x] **5.2** `generate_data_js.py`: escapar `</`, timestamps derivados del dato, cache-buster `?v=` con `date_range.end` (M20, M21, B7).
- [x] **5.3** Script `scripts/verify_output.py` con asserts (data.js parsea, conteo y fecha final coinciden con baloto.json) y llamarlo antes del commit (C13).
- [x] **5.4** Detección de cambios por `total_draws`/`date_range.end` (M13).
- [x] **5.5** Staging `_site/` para el artefacto de Pages (M12).
- [x] **5.6** Permisos por job (M15).
- [x] **5.7** `concurrency` + reintento de push (M16).
- [x] **5.8** `ci.yml`: quitar `|| echo`, `permissions: contents: read`, `cache: pip`, `node --check` sobre `main.js`.
- [x] **5.9** `requirements.txt`: cotas superiores por major (M17).
- [x] **5.10** `.gitignore`: borrar las 3 reglas muertas (M18).
- [x] **5.11** Tests reales: `scripts/test_pipeline.py` (parsers, integridad del JSON, coherencia de data.js).

### Fase 6 — Documentación y cierre
- [x] **6.1** README: cifras reales, sin Kaggle ni datos sintéticos, metodología corregida (M19).
- [x] **6.2** CHANGELOG con la entrada de la auditoría.
- [x] **6.3** Verificación final: `ruff`, `black --check`, `isort --check`, `pytest`, `node --check`, pipeline completo, Playwright en tema oscuro y claro, 375 px de ancho.
- [ ] **6.4** Commit + push.

---

## Criterio de aceptación

1. `pytest scripts/` pasa y falla si el pipeline rompe el contrato de datos.
2. `ruff`, `black --check`, `isort --check-only` y `node --check` pasan.
3. El pipeline completo corre de punta a punta y `data/processed/baloto.json` tiene ≥ 656 sorteos desde 2021-05-01 sin huecos > 7 días ni duplicados.
4. Playwright: cero `pageerror`, cero `console.error`, el top-10 de predicciones en orden descendente de probabilidad, la vista de jackpots sin `NaN`, y las secciones Validación y Tablero renderizadas.
5. Contraste ≥ 4.5:1 en las combinaciones de texto listadas en A7, en ambos temas.

---

## Hallazgos aparecidos durante la implementación

No estaban en el informe inicial; los detecté al ejecutar el pipeline y abrir la página.

- **La línea de "probabilidad teórica" del gráfico de probabilidades estaba 5× abajo**
  (`main.js:861`). Las probabilidades se normalizan para sumar 5 (5 números por sorteo), así
  que la línea base es `500/43 = 11.63 %`, no `100/43 = 2.33 %`. La línea roja caía por
  debajo de todas las barras con una etiqueta falsa. Corregido.
- **`parse_spanish_date` era sensible a mayúsculas y no validaba el día**: "1 de mayo de
  2021" devolvía `None` (fila perdida en silencio) y "32 de Agosto de 2026" producía
  `2026-08-32`. Ahora normaliza la capitalización y valida con `datetime`.
- **La navegación se desbordaba** al añadir los enlaces a Modelos y Tablero: el logo caía a
  dos líneas. Etiquetas acortadas ("Descriptiva", "Inferencial") y el top-10 en rejilla de
  5 columnas para evitar el huérfano de la décima tarjeta.
- **Textos mezclados inglés/español** en las interpretaciones de los tests (venían de
  `analyze_baloto.py`). Traducidos los 21 literales visibles.
- **"Calientes Sig. 1 / 21" era el conteo sin corregir** y se leía como un hallazgo. Ahora la
  etiqueta dice `p<0.05` y el FDR va aparte.
- **El 2026-07-20 no aparece en el sitio oficial** aunque sí estaba en el snapshot del
  2026-08-31. El scrape actual devuelve 131 páginas × 10 filas exactas (5 Baloto + 5
  Revancha), así que no es un artefacto de paginación: el sitio ya no lista ese sorteo. Se
  respeta la fuente y se documenta aquí en lugar de reintroducir un dato no verificable.

---

## Verificación ejecutada

Todo lo que sigue se ejecutó sobre el árbol final, no se infiere.

```
ruff check scripts/                     All checks passed!
black --check scripts/                  6 files would be left unchanged.
isort --check-only scripts/             sin cambios
python -m pytest scripts/ -q            12 passed
node --check src/js/main.js             OK
node --check src/js/data.js             OK
python scripts/verify_output.py         OK: 655 sorteos (2021-05-01 -> 2026-11-16)
```

Pipeline completo (fetch → analyze → validate → generate → verify):

```
fetch   : 131 páginas, 655 sorteos, 2021-05-01 -> 2026-11-16, sin huecos > 7 días
analyze : uniformidad p=0.916 (corregido), portmanteau Q=48.11 p=0.274,
          posiciones p=0.977/0.600/0.747/0.993/0.343, FDR 0/43,
          tendencias 0 significativas (antes 37)
validate: KS p=0.924, CvM p=0.968, gaps GOF p=0.565, Fisher p=4.75e-04 (no sobrevive BH),
          "Ningún test rechaza al 5%"
```

Playwright (Chromium 1440×900 y 375×800, tema oscuro y claro):

```
pageerror: 0        console error/warn: 0        requests fallidos: 0
Chart: function     d3: object      annotation registrada: true
top-10: 9,25,5,14,42,43,11,21,32,41 -> descendente: true
tick color: #8b8b9e (dark) / #6e6e7e (light)
jackpots: 0 paths con NaN + mensaje explicativo
tablero: 9 pruebas, 9 PASADA
scrollWidth móvil: 375 (sin overflow horizontal)
```

Contraste recalculado tras el cambio: `--text-muted` 5.35:1 (dark) y 5.01:1 (light);
acentos como texto 5.86:1 / 6.09:1; botón primario 6.96:1 → 5.18:1 sobre el gradiente.
