# Baloto Oracle - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Kaggle: jaforero/baloto-colombia (2017-present)
- Kaggle: jforero/resultados-baloto (2021-present)
- Official Baloto results structure

[1.0.0]: https://github.com/USER/baloto-oracle/releases/tag/v1.0.0