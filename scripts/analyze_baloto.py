#!/usr/bin/env python3
"""
Baloto Statistical Analysis Engine
Performs comprehensive descriptive and inferential statistical analysis
on Baloto lottery historical data.
"""

import json
import logging
import math
import warnings
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")


def convert_to_serializable(obj):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        val = float(obj)
        return None if (np.isnan(val) or np.isinf(val)) else val
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [convert_to_serializable(v) for v in obj]
    return obj


def _sanitize_json(obj):
    """Recursively replace NaN/Infinity with None so the output is strict JSON."""
    if isinstance(obj, float):
        return None if (np.isnan(obj) or np.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_json(v) for v in obj]
    return obj


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BalotoAnalyzer:
    """Comprehensive statistical analyzer for Baloto lottery data."""

    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.baloto_df = None
        self.revancha_df = None
        self.metadata = None
        self.results = {}

    def load_data(self):
        """Load processed data."""
        logger.info("Loading data...")

        with open(self.data_dir / "baloto.json", "r", encoding="utf-8") as f:
            baloto_data = json.load(f)
        with open(self.data_dir / "revancha.json", "r", encoding="utf-8") as f:
            revancha_data = json.load(f)
        with open(self.data_dir / "metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.baloto_df = pd.DataFrame(baloto_data)
        self.revancha_df = pd.DataFrame(revancha_data)

        # Ensure numbers are lists
        for df in [self.baloto_df, self.revancha_df]:
            if isinstance(df["numbers"].iloc[0], str):
                df["numbers"] = df["numbers"].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )

        logger.info(
            f"Loaded {len(self.baloto_df)} Baloto draws and {len(self.revancha_df)} Revancha draws"
        )

    # ==================== DESCRIPTIVE STATISTICS ====================

    def analyze_number_frequencies(
        self, df: pd.DataFrame, number_col: str = "numbers", max_num: int = 43
    ) -> Dict:
        """Analyze frequency of each number."""
        all_numbers = []
        for nums in df[number_col]:
            all_numbers.extend(nums)

        freq = Counter(all_numbers)
        total_draws = len(df)
        expected_freq = total_draws * 5 / max_num  # 5 numbers per draw
        # Muestreo SIN reemplazo dentro del sorteo: Var(O) = n·p·(1-p)·(N-k)/(N-1)
        without_replacement = (max_num - 5) / (max_num - 1)
        sd_freq = np.sqrt(expected_freq * (1 - 5 / max_num) * without_replacement)

        frequencies = {}
        for i in range(1, max_num + 1):
            count = freq.get(i, 0)
            frequencies[i] = {
                "count": count,
                "percentage": round(count / total_draws * 100, 2),
                "expected": round(expected_freq, 2),
                "deviation": round(count - expected_freq, 2),
                "z_score": (
                    round((count - expected_freq) / sd_freq, 3) if sd_freq > 0 else 0
                ),
            }

        # Sort by frequency
        sorted_freq = dict(
            sorted(frequencies.items(), key=lambda x: x[1]["count"], reverse=True)
        )

        chi2_stat = sum(
            (v["count"] - expected_freq) ** 2 / expected_freq
            for v in frequencies.values()
        )

        return {
            "frequencies": sorted_freq,
            "total_draws": total_draws,
            "total_numbers_drawn": len(all_numbers),
            "expected_per_number": round(expected_freq, 2),
            "hot_numbers": [k for k, v in sorted_freq.items() if v["z_score"] > 1.5],
            "cold_numbers": [k for k, v in sorted_freq.items() if v["z_score"] < -1.5],
            "chi2_statistic": chi2_stat,
            # La referencia correcta no es chi2_(N-1) sino (38/42)·chi2_(N-1):
            # las celdas no son multinomiales porque se extraen 5 de 43 sin reemplazo.
            "chi2_p_value": float(
                stats.chi2.sf(chi2_stat / without_replacement, max_num - 1)
            ),
        }

    def analyze_superbalota_frequencies(self, df: pd.DataFrame) -> Dict:
        """Analyze Superbalota (bonus ball) frequencies."""
        superbalotas = df["superbalota"].tolist()
        freq = Counter(superbalotas)
        total_draws = len(df)
        expected_freq = total_draws / 16  # 16 possible superbalotas

        frequencies = {}
        for i in range(1, 17):
            count = freq.get(i, 0)
            frequencies[i] = {
                "count": count,
                "percentage": round(count / total_draws * 100, 2),
                "expected": round(expected_freq, 2),
                "deviation": round(count - expected_freq, 2),
                "z_score": (
                    round((count - expected_freq) / np.sqrt(expected_freq), 3)
                    if expected_freq > 0
                    else 0
                ),
            }

        sorted_freq = dict(
            sorted(frequencies.items(), key=lambda x: x[1]["count"], reverse=True)
        )

        return {
            "frequencies": sorted_freq,
            "total_draws": total_draws,
            "hot_superbalotas": [k for k, v in sorted_freq.items() if v["z_score"] > 1],
            "cold_superbalotas": [
                k for k, v in sorted_freq.items() if v["z_score"] < -1
            ],
            "chi2_p_value": 1
            - stats.chi2.cdf(
                sum(
                    (v["count"] - expected_freq) ** 2 / expected_freq
                    for v in frequencies.values()
                ),
                15,
            ),
        }

    def analyze_position_frequencies(self, df: pd.DataFrame) -> Dict:
        """Analyze frequency of numbers by position (1st, 2nd, 3rd, 4th, 5th ball)."""
        positions = {i: [] for i in range(5)}
        for nums in df["numbers"]:
            for pos, num in enumerate(nums):
                positions[pos].append(num)

        position_analysis = {}
        for pos in range(5):
            freq = Counter(positions[pos])
            position_analysis[f"position_{pos+1}"] = {
                "frequencies": dict(
                    sorted(freq.items(), key=lambda x: x[1], reverse=True)
                ),
                "most_common": freq.most_common(5),
                "least_common": freq.most_common()[-5:],
                "mean": round(np.mean(positions[pos]), 2),
                "std": round(np.std(positions[pos]), 2),
                "median": round(np.median(positions[pos]), 2),
            }

        return position_analysis

    def analyze_sum_statistics(self, df: pd.DataFrame) -> Dict:
        """Analyze sum of drawn numbers."""
        sums = [sum(nums) for nums in df["numbers"]]

        return {
            "mean": round(np.mean(sums), 2),
            "median": round(np.median(sums), 2),
            "std": round(np.std(sums), 2),
            "min": int(np.min(sums)),
            "max": int(np.max(sums)),
            "percentiles": {
                "25": round(np.percentile(sums, 25), 2),
                "50": round(np.percentile(sums, 50), 2),
                "75": round(np.percentile(sums, 75), 2),
                "90": round(np.percentile(sums, 90), 2),
                "95": round(np.percentile(sums, 95), 2),
            },
            "distribution": Counter(sums),
            "theoretical_mean": 5 * 22,  # 5 numbers * average of 1-43
            # Sin reemplazo: sqrt(k·(N+1)(N-k)/12) = sqrt(5·44·38/12) = 26.40
            "theoretical_std": round(np.sqrt(5 * (43 + 1) * (43 - 5) / 12), 2),
        }

    def analyze_odd_even_balance(self, df: pd.DataFrame) -> Dict:
        """Analyze odd/even number balance."""
        odd_even_counts = []
        for nums in df["numbers"]:
            odd = sum(1 for n in nums if n % 2 == 1)
            even = 5 - odd
            odd_even_counts.append((odd, even))

        distribution = Counter(odd_even_counts)
        total = len(odd_even_counts)

        return {
            "distribution": {
                f"{o}-{e}": count for (o, e), count in distribution.items()
            },
            "percentages": {
                f"{o}-{e}": round(count / total * 100, 2)
                for (o, e), count in distribution.items()
            },
            "avg_odd": round(np.mean([o for o, e in odd_even_counts]), 2),
            "avg_even": round(np.mean([e for o, e in odd_even_counts]), 2),
            "most_common_pattern": max(distribution, key=distribution.get),
        }

    def analyze_high_low_balance(self, df: pd.DataFrame, midpoint: int = 22) -> Dict:
        """Analyze high/low number balance (1-22 low, 23-43 high)."""
        high_low_counts = []
        for nums in df["numbers"]:
            low = sum(1 for n in nums if n <= midpoint)
            high = 5 - low
            high_low_counts.append((high, low))

        distribution = Counter(high_low_counts)
        total = len(high_low_counts)

        return {
            "distribution": {
                f"{h}-{lo}": count for (h, lo), count in distribution.items()
            },
            "percentages": {
                f"{h}-{lo}": round(count / total * 100, 2)
                for (h, lo), count in distribution.items()
            },
            "avg_high": round(np.mean([h for h, lo in high_low_counts]), 2),
            "avg_low": round(np.mean([lo for h, lo in high_low_counts]), 2),
        }

    def analyze_consecutive_numbers(self, df: pd.DataFrame) -> Dict:
        """Analyze consecutive number pairs."""
        consecutive_counts = []
        for nums in df["numbers"]:
            consec = sum(1 for i in range(4) if nums[i + 1] == nums[i] + 1)
            consecutive_counts.append(consec)

        distribution = Counter(consecutive_counts)
        total = len(consecutive_counts)

        return {
            "distribution": dict(distribution),
            "percentages": {
                k: round(v / total * 100, 2) for k, v in distribution.items()
            },
            "avg_consecutive": round(np.mean(consecutive_counts), 2),
            "probability_at_least_one": round(
                sum(1 for c in consecutive_counts if c > 0) / total * 100, 2
            ),
        }

    def analyze_number_gaps(self, df: pd.DataFrame) -> Dict:
        """Analyze gaps between drawn numbers."""
        all_gaps = []
        for nums in df["numbers"]:
            for i in range(4):
                gap = nums[i + 1] - nums[i]
                all_gaps.append(gap)

        return {
            "mean_gap": round(np.mean(all_gaps), 2),
            "median_gap": round(np.median(all_gaps), 2),
            "std_gap": round(np.std(all_gaps), 2),
            "min_gap": int(np.min(all_gaps)),
            "max_gap": int(np.max(all_gaps)),
            "gap_distribution": dict(Counter(all_gaps).most_common()),
        }

    def analyze_repeating_numbers(self, df: pd.DataFrame, lookback: int = 10) -> Dict:
        """Analyze numbers that repeat from recent draws."""
        repeats = []
        for i in range(lookback, len(df)):
            current_nums = set(df.iloc[i]["numbers"])
            prev_nums = set()
            for j in range(max(0, i - lookback), i):
                prev_nums.update(df.iloc[j]["numbers"])
            repeat_count = len(current_nums & prev_nums)
            repeats.append(repeat_count)

        distribution = Counter(repeats)
        total = len(repeats)
        # Línea base teórica: un sorteo de 5 de 43 repite en media
        # 5·(1-(38/43)^lookback) números de la unión de los `lookback` previos.
        expected_repeats = 5 * (1 - ((43 - 5) / 43) ** lookback)

        return {
            "distribution": dict(distribution),
            "percentages": {
                k: round(v / total * 100, 2) for k, v in distribution.items()
            },
            "avg_repeats": round(np.mean(repeats), 2),
            "expected_repeats_under_randomness": round(expected_repeats, 2),
            "probability_at_least_one": round(
                sum(1 for r in repeats if r > 0) / total * 100, 2
            ),
        }

    def analyze_jackpot_statistics(self, df: pd.DataFrame) -> Dict:
        """Analyze jackpot amounts and rollover patterns."""
        # Solo el sorteo más reciente trae jackpot del sitio oficial: con menos de
        # 2 observaciones no hay nada que resumir, y publicar medias de n=1 engaña.
        jackpots = df["jackpot"].dropna().tolist()
        current = jackpots[-1] if jackpots else None
        if len(jackpots) < 2:
            return {
                "current_jackpot": current,
                "available_observations": len(jackpots),
                "note": (
                    "El sitio oficial solo publica el acumulado del sorteo más "
                    "reciente; no hay serie histórica de jackpots."
                ),
            }

        # Calculate rollovers (jackpot increases)
        rollovers = []
        for i in range(1, len(jackpots)):
            if jackpots[i] > jackpots[i - 1]:
                rollovers.append(jackpots[i] - jackpots[i - 1])
            else:
                rollovers.append(0)

        return {
            "current_jackpot": current,
            "available_observations": len(jackpots),
            "mean_jackpot": round(float(np.mean(jackpots)), 2),
            "median_jackpot": round(float(np.median(jackpots)), 2),
            "max_jackpot": max(jackpots),
            "min_jackpot": min(jackpots),
            "std_jackpot": round(float(np.std(jackpots)), 2),
            "total_rollovers": sum(1 for r in rollovers if r > 0),
            "avg_rollover_amount": (
                round(float(np.mean([r for r in rollovers if r > 0])), 2)
                if any(r > 0 for r in rollovers)
                else 0
            ),
            "rollover_frequency": (
                round(sum(1 for r in rollovers if r > 0) / len(rollovers) * 100, 2)
                if rollovers
                else 0
            ),
        }

    # ==================== INFERENTIAL STATISTICS ====================

    def _effect_size_label(self, v: float, kind: str = "v") -> str:
        """Label effect size magnitude per Cohen conventions."""
        if kind == "v":  # Cramer's V / Cohen's w
            bounds = [(0.1, "pequeño"), (0.3, "mediano"), (float("inf"), "grande")]
        elif kind == "d":  # Cohen's d
            bounds = [(0.2, "pequeño"), (0.5, "mediano"), (float("inf"), "grande")]
        elif kind == "eta":  # Eta-squared / epsilon-squared
            bounds = [(0.01, "pequeño"), (0.06, "mediano"), (float("inf"), "grande")]
        elif kind in ("r", "w"):  # r de Pearson / W de Kendall
            bounds = [(0.1, "pequeño"), (0.3, "mediano"), (0.5, "grande")]
        else:
            bounds = [(0.01, "pequeño"), (0.1, "mediano"), (float("inf"), "grande")]
        v = abs(v)
        for threshold, label in bounds:
            if v < threshold:
                return label
        return "grande"

    def _fdr_bh(self, p_values: List[float], alpha: float = 0.05) -> List[bool]:
        """Benjamini-Hochberg FDR correction. Returns boolean vector rejecting H0."""
        p = np.array(p_values, dtype=float)
        n = len(p)
        order = np.argsort(p)
        ranked = p[order]
        # BH critical value: p_(i) <= (i/n) * alpha
        thresholds = (np.arange(1, n + 1) / n) * alpha
        # Largest i where p_(i) <= threshold; all smaller i rejected too
        reject = np.zeros(n, dtype=bool)
        passing = np.where(ranked <= thresholds)[0]
        if passing.size > 0:
            max_idx = passing.max()
            reject[: max_idx + 1] = True
        # Map back to original order
        out = np.zeros(n, dtype=bool)
        out[order] = reject
        return out.tolist()

    def test_uniformity(self, df: pd.DataFrame, max_num: int = 43) -> Dict:
        """Chi-square test for uniformity of number distribution."""
        freq_result = self.analyze_number_frequencies(df, max_num=max_num)
        observed = [v["count"] for v in freq_result["frequencies"].values()]
        expected_raw = [freq_result["expected_per_number"]] * max_num

        # Normalize expected to match observed sum (fix floating point precision)
        observed_sum = sum(observed)
        expected_sum = sum(expected_raw)
        expected = [e * observed_sum / expected_sum for e in expected_raw]

        chi2_stat, _ = stats.chisquare(observed, expected)
        n = observed_sum
        dof = max_num - 1
        # Las 5 balotas se extraen SIN reemplazo: Var(O_i) se reduce en (N-k)/(N-1),
        # así que el estadístico de Pearson se distribuye como (38/42)·chi2_42.
        without_replacement = (max_num - 5) / (max_num - 1)
        p_value = float(stats.chi2.sf(chi2_stat / without_replacement, dof))
        # Effect size: Cohen's w = sqrt(chi2 / N). Para una tabla 1×43 no hay V de
        # Cramér (min(r-1,c-1) = 0); se reporta solo w.
        w = float(np.sqrt(chi2_stat / n)) if n > 0 else 0.0

        return {
            "test": "Chi-cuadrado de bondad de ajuste (distribución uniforme)",
            "chi2_statistic": round(chi2_stat, 4),
            "p_value": round(p_value, 6),
            "degrees_of_freedom": dof,
            "sample_size": n,
            "significant_at_05": p_value < 0.05,
            "significant_at_01": p_value < 0.01,
            "interpretation": (
                "Los números siguen una distribución uniforme"
                if p_value >= 0.05
                else "Los números se desvían de la distribución uniforme"
            ),
            "null_distribution_note": (
                "Referencia corregida por muestreo sin reemplazo: "
                "(38/42)·chi2_42, no chi2_42."
            ),
            "effect_size": {
                "cohens_w": round(w, 4),
                "label": self._effect_size_label(w, "v"),
            },
        }

    def test_independence(self, df: pd.DataFrame) -> Dict:
        """Test independence between draws (autocorrelation)."""
        # Convert draws to binary matrix (number drawn or not)
        max_num = 43
        draws_matrix = np.zeros((len(df), max_num))
        for i, nums in enumerate(df["numbers"]):
            for n in nums:
                draws_matrix[i, n - 1] = 1

        # Lag-1 autocorrelation for each of the 43 binary series
        autocorrelations = []
        for n in range(max_num):
            series = draws_matrix[:, n]
            if np.std(series) > 0:
                corr = np.corrcoef(series[:-1], series[1:])[0, 1]
                if not np.isnan(corr):
                    autocorrelations.append(corr)

        mean_autocorr = np.mean(autocorrelations) if autocorrelations else 0

        # Portmanteau correcto para 43 series binarias independientes:
        # Q = n·Σ r_i² ~ chi2_43 (no es un Ljung-Box de lags 1..10 de una serie).
        n = len(df)
        q_stat = (
            float(n * np.sum(np.square(autocorrelations))) if autocorrelations else 0.0
        )
        dof = len(autocorrelations) or 1
        lb_p = float(stats.chi2.sf(q_stat, dof)) if autocorrelations else 1.0

        return {
            "test": "Portmanteau de autocorrelación lag-1 sobre las 43 series",
            "mean_autocorrelation": round(mean_autocorr, 6),
            "ljung_box_statistic": round(q_stat, 4),
            "degrees_of_freedom": dof,
            "p_value": round(lb_p, 6),
            "significant_at_05": lb_p < 0.05,
            "interpretation": (
                "Los sorteos parecen independientes"
                if lb_p >= 0.05
                else "Posible autocorrelación detectada"
            ),
        }

    def test_hot_cold_significance(self, df: pd.DataFrame) -> Dict:
        """Test if hot/cold numbers are statistically significant."""
        freq_result = self.analyze_number_frequencies(df)

        total_draws = freq_result["total_draws"]
        p_expected = 5 / 43  # Probability of any number being drawn

        # Se testean los 43 números: filtrar antes por |z|>1.5 es selección sobre
        # los datos, y corregir por multiplicidad con m=2 es anti-conservador.
        all_details = []
        for num in range(1, 44):
            count = freq_result["frequencies"][num]["count"]
            p_val = float(
                stats.binomtest(
                    count, total_draws, p_expected, alternative="two-sided"
                ).pvalue
            )
            all_details.append(
                {
                    "number": num,
                    "count": count,
                    "p_value": round(p_val, 6),
                    "expected": round(total_draws * p_expected, 2),
                }
            )

        # Multiple-comparison corrections (43 tests)
        bh_reject = self._fdr_bh([d["p_value"] for d in all_details], 0.05)
        bonferroni_threshold = 0.05 / 43
        for det, rej in zip(all_details, bh_reject):
            det["fdr_significant_at_05"] = bool(rej)
            det["bonferroni_significant_at_05"] = det["p_value"] < bonferroni_threshold
            det["direction"] = (
                "hot"
                if det["count"] > det["expected"]
                else ("cold" if det["count"] < det["expected"] else "neutral")
            )

        hot_details = [d for d in all_details if d["direction"] == "hot"]
        cold_details = [d for d in all_details if d["direction"] == "cold"]

        return {
            "hot_numbers_tested": len(hot_details),
            "cold_numbers_tested": len(cold_details),
            "hot_significant_at_05": sum(1 for h in hot_details if h["p_value"] < 0.05),
            "cold_significant_at_05": sum(
                1 for c in cold_details if c["p_value"] < 0.05
            ),
            "hot_fdr_significant_at_05": sum(
                1 for h in hot_details if h["fdr_significant_at_05"]
            ),
            "cold_fdr_significant_at_05": sum(
                1 for c in cold_details if c["fdr_significant_at_05"]
            ),
            "hot_details": hot_details,
            "cold_details": cold_details,
            "bonferroni_threshold": round(bonferroni_threshold, 6),
            "fdr_method": "Benjamini-Hochberg (FDR ≤ 0.05) sobre los 43 números",
            "interpretation": (
                "Ningún número se desvía de 5/43 tras corregir por 43 comparaciones"
                if not any(d["fdr_significant_at_05"] for d in all_details)
                else "Algún número sobrevive la corrección FDR"
            ),
        }

    def predict_next_draw_probabilities(
        self, df: pd.DataFrame, lookback: int = 50
    ) -> Dict:
        """Calculate probabilities for next draw based on recent trends."""
        # Prior y likelihood NO deben solaparse: si el prior incluye los últimos
        # `lookback` sorteos y la likelihood los vuelve a sumar, la recencia se
        # cuenta dos veces y el "posterior conjugado" deja de serlo.
        prior_df = df.iloc[:-lookback] if len(df) > lookback else df.iloc[:0]
        recent_df = df.tail(lookback)

        recent_freq = self.analyze_number_frequencies(recent_df)
        overall_freq = self.analyze_number_frequencies(
            prior_df if len(prior_df) else df
        )

        # Bayesian update: prior (histórico previo) + likelihood (ventana reciente)
        probabilities = {}
        for num in range(1, 44):
            prior_count = overall_freq["frequencies"][num]["count"]
            prior_total = overall_freq["total_draws"] * 5
            recent_count = recent_freq["frequencies"][num]["count"]
            recent_total = recent_freq["total_draws"] * 5

            # Beta-Binomial conjugate prior
            alpha_prior = prior_count + 1
            beta_prior = prior_total - prior_count + 1

            alpha_post = alpha_prior + recent_count
            beta_post = beta_prior + recent_total - recent_count

            # Posterior mean probability
            prob = alpha_post / (alpha_post + beta_post)
            probabilities[num] = prob

        # Normalize to sum to 5 (expected numbers per draw)
        total_prob = sum(probabilities.values())
        normalized = {k: v / total_prob * 5 for k, v in probabilities.items()}

        # Sort by probability
        sorted_probs = dict(
            sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "probabilities": sorted_probs,
            "top_5_most_likely": list(sorted_probs.keys())[:5],
            "top_10_most_likely": list(sorted_probs.keys())[:10],
            "methodology": (
                "Beta-Binomial: prior con todo el histórico previo a la ventana "
                "reciente, likelihood con la ventana reciente (sin solape)"
            ),
            "lookback_period": lookback,
            "confidence": "Low - lottery draws are independent random events",
        }

    def predict_superbalota_probabilities(
        self, df: pd.DataFrame, lookback: int = 50
    ) -> Dict:
        """Predict Superbalota probabilities."""
        prior_df = df.iloc[:-lookback] if len(df) > lookback else df.iloc[:0]
        recent_df = df.tail(lookback)

        recent_freq = self.analyze_superbalota_frequencies(recent_df)
        overall_freq = self.analyze_superbalota_frequencies(
            prior_df if len(prior_df) else df
        )

        probabilities = {}
        for num in range(1, 17):
            prior_count = overall_freq["frequencies"][num]["count"]
            prior_total = overall_freq["total_draws"]
            recent_count = recent_freq["frequencies"][num]["count"]
            recent_total = recent_freq["total_draws"]

            alpha_prior = prior_count + 1
            beta_prior = prior_total - prior_count + 1

            alpha_post = alpha_prior + recent_count
            beta_post = beta_prior + recent_total - recent_count

            prob = alpha_post / (alpha_post + beta_post)
            probabilities[num] = prob

        sorted_probs = dict(
            sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        )

        return {
            "probabilities": sorted_probs,
            "most_likely": list(sorted_probs.keys())[:3],
            "methodology": (
                "Beta-Binomial: prior con todo el histórico previo a la ventana "
                "reciente, likelihood con la ventana reciente (sin solape)"
            ),
        }

    def calculate_confidence_intervals(
        self, df: pd.DataFrame, confidence: float = 0.95
    ) -> Dict:
        """Calculate confidence intervals for key statistics."""
        total_draws = len(df)

        # CI for mean sum
        sums = [sum(nums) for nums in df["numbers"]]
        mean_sum = np.mean(sums)
        se_sum = stats.sem(sums)
        ci_sum = stats.t.interval(confidence, len(sums) - 1, loc=mean_sum, scale=se_sum)

        # Banda esperada bajo H0 para la proporción de un número (p = 5/43).
        # NO es el IC de la frecuencia observada de un número concreto: es la
        # región donde debe caer cada p̂ si el sorteo es justo.
        p_hat = 5 / 43
        se_p = np.sqrt(p_hat * (1 - p_hat) / total_draws)
        z = stats.norm.ppf((1 + confidence) / 2)
        ci_freq = (p_hat - z * se_p, p_hat + z * se_p)

        return {
            "confidence_level": confidence,
            "mean_sum_ci": [round(ci_sum[0], 2), round(ci_sum[1], 2)],
            "expected_range_under_h0": [round(ci_freq[0], 4), round(ci_freq[1], 4)],
            # Alias heredado para no romper consumidores antiguos.
            "number_frequency_ci": [round(ci_freq[0], 4), round(ci_freq[1], 4)],
            "interpretation": (
                f"IC {confidence*100:.0f}% de la media de las sumas; la banda "
                "esperada bajo H0 es el rango donde debe caer la frecuencia de "
                "cada número si el sorteo es uniforme (no es un IC por número)"
            ),
        }

    # ==================== NON-PARAMETRIC TESTS ====================

    def test_mann_whitney_odd_even(self, df: pd.DataFrame) -> Dict:
        """Mann-Whitney U test: Compare sums between odd-heavy and even-heavy draws."""
        odd_heavy_sums = []
        even_heavy_sums = []

        for nums in df["numbers"]:
            odd_count = sum(1 for n in nums if n % 2 == 1)
            total = sum(nums)
            if odd_count >= 3:
                odd_heavy_sums.append(total)
            elif odd_count <= 2:
                even_heavy_sums.append(total)

        if len(odd_heavy_sums) > 10 and len(even_heavy_sums) > 10:
            n1, n2 = len(odd_heavy_sums), len(even_heavy_sums)
            stat, p_val = stats.mannwhitneyu(
                odd_heavy_sums, even_heavy_sums, alternative="two-sided"
            )
            # Effect size r = Z / sqrt(N) via normal approximation, or rank-biserial correlation
            mu = n1 * n2 / 2.0
            sigma = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
            z = (stat - mu) / sigma if sigma > 0 else 0.0
            r_effect = abs(z) / np.sqrt(n1 + n2) if (n1 + n2) > 0 else 0.0
            # Rank-biserial correlation (alternate effect size, signed)
            rank_biserial = 1.0 - (2.0 * stat) / (n1 * n2)
            return {
                "test": "Mann-Whitney U (sumas impar-pesadas vs par-pesadas)",
                "statistic": round(stat, 4),
                "p_value": round(p_val, 6),
                "significant_at_05": p_val < 0.05,
                "median_odd_heavy": round(np.median(odd_heavy_sums), 2),
                "median_even_heavy": round(np.median(even_heavy_sums), 2),
                "n_odd_heavy": n1,
                "n_even_heavy": n2,
                "effect_size": {
                    "r": round(r_effect, 4),
                    "rank_biserial": round(rank_biserial, 4),
                    "label": self._effect_size_label(r_effect, "r"),
                },
                "interpretation": (
                    "Sin diferencia en la distribución de sumas"
                    if p_val >= 0.05
                    else "Diferencia significativa en las sumas según la paridad"
                ),
            }
        return {"test": "Mann-Whitney U Test", "error": "Muestras insuficientes"}

    def test_position_uniformity(self, df: pd.DataFrame) -> Dict:
        """¿Cada posición se comporta como el orden estadístico de un sorteo justo?

        Las 5 posiciones de un sorteo ya ordenado NO son muestras independientes:
        pos1 < pos2 < ... < pos5 por construcción, así que Kruskal-Wallis (o ANOVA)
        rechazan siempre por tautología. El test correcto compara cada posición
        contra su distribución nula EXACTA:

            P(X_(i) = v) = C(v-1, i-1)·C(N-v, k-i) / C(N, k)

        con N=43, k=5. Chi-cuadrado por posición sobre bins con esperado ≥ 5.
        """
        max_num, k = 43, 5
        n_draws = len(df)
        total_combos = math.comb(max_num, k)

        positions = [[nums[i] for nums in df["numbers"]] for i in range(k)]
        per_position = {}
        p_values = []

        for i in range(1, k + 1):
            observed = Counter(positions[i - 1])
            # Probabilidad exacta del i-ésimo orden estadístico
            probs = {}
            for v in range(1, max_num + 1):
                ways = math.comb(v - 1, i - 1) * math.comb(max_num - v, k - i)
                probs[v] = ways / total_combos

            # Agrupar bins contiguos hasta que el esperado llegue a 5
            bins_obs, bins_exp = [], []
            acc_o = acc_e = 0.0
            for v in range(1, max_num + 1):
                acc_o += observed.get(v, 0)
                acc_e += n_draws * probs[v]
                if acc_e >= 5:
                    bins_obs.append(acc_o)
                    bins_exp.append(acc_e)
                    acc_o = acc_e = 0.0
            if acc_e > 0:  # cola sobrante al último bin
                if bins_obs:
                    bins_obs[-1] += acc_o
                    bins_exp[-1] += acc_e
                else:
                    bins_obs.append(acc_o)
                    bins_exp.append(acc_e)

            chi2_stat, p_val = stats.chisquare(bins_obs, bins_exp)
            df_bins = len(bins_obs) - 1
            p_values.append(float(p_val))
            per_position[f"position_{i}"] = {
                "chi2_statistic": round(float(chi2_stat), 4),
                "degrees_of_freedom": df_bins,
                "p_value": round(float(p_val), 6),
                "observed_mean": round(float(np.mean(positions[i - 1])), 2),
                "expected_mean": round(i * (max_num + 1) / (k + 1), 2),
            }

        # Bonferroni sobre las 5 posiciones
        p_bonf = min(1.0, 5 * min(p_values)) if p_values else 1.0
        # Estadístico de cabecera: el de la posición con menor p (la más extrema)
        worst = min(per_position, key=lambda k: per_position[k]["p_value"])

        return {
            "test": "Chi-cuadrado por posición vs orden estadístico exacto",
            "chi2_statistic": per_position[worst]["chi2_statistic"],
            "degrees_of_freedom": per_position[worst]["degrees_of_freedom"],
            "worst_position": worst,
            "p_value": round(p_bonf, 6),
            "significant_at_05": p_bonf < 0.05,
            "n_total": n_draws,
            "per_position": per_position,
            "methodology": (
                "Cada posición se compara contra P(X_(i)=v) del orden estadístico "
                "de una 5-subconjunto uniforme de 1..43; p corregido por Bonferroni "
                "sobre 5 posiciones."
            ),
            "interpretation": (
                "Cada posición se ajusta a lo esperado en un sorteo uniforme"
                if p_bonf >= 0.05
                else "Alguna posición se desvía del orden estadístico esperado"
            ),
        }

    def test_friedman_consecutive(self, df: pd.DataFrame) -> Dict:
        """Friedman test: Repeated measures for consecutive numbers over time periods."""
        # Split into quarters
        n = len(df)
        quarter_size = n // 4
        periods = []
        for i in range(4):
            start = i * quarter_size
            end = start + quarter_size if i < 3 else n
            period_draws = df.iloc[start:end]
            consec_counts = []
            for nums in period_draws["numbers"]:
                consec = sum(1 for i in range(4) if nums[i + 1] == nums[i] + 1)
                consec_counts.append(consec)
            periods.append(consec_counts)

        # Friedman requires equal sample sizes - truncate to minimum
        min_len = min(len(p) for p in periods)
        if min_len > 5:
            periods_equal = [p[:min_len] for p in periods]
            k_periods = 4
            stat, p_val = stats.friedmanchisquare(*periods_equal)
            # Kendall's W for Friedman: W = Q / (k * (n - 1)) where n = subjects, k = conditions
            kendall_w = stat / (k_periods * (min_len - 1)) if min_len > 1 else 0.0
            return {
                "test": "Friedman (consecutivos por trimestre)",
                "statistic": round(stat, 4),
                "p_value": round(p_val, 6),
                "significant_at_05": p_val < 0.05,
                "sample_size_per_period": min_len,
                "effect_size": {
                    "kendalls_w": round(kendall_w, 4),
                    "label": self._effect_size_label(kendall_w, "w"),
                },
                "interpretation": (
                    "El patrón de consecutivos es estable en el tiempo"
                    if p_val >= 0.05
                    else "El patrón de consecutivos cambia en el tiempo"
                ),
            }
        return {"test": "Friedman Test", "error": "Datos insuficientes"}

    def test_wilcoxon_signed_rank_pairs(self, df: pd.DataFrame) -> Dict:
        """Wilcoxon signed-rank test: Compare first half vs second half draw sums."""
        mid = len(df) // 2
        first_half = [sum(nums) for nums in df.iloc[:mid]["numbers"]]
        second_half = [sum(nums) for nums in df.iloc[mid:]["numbers"]]

        # Pair by index
        min_len = min(len(first_half), len(second_half))
        if min_len > 10:
            stat, p_val = stats.wilcoxon(
                first_half[:min_len], second_half[:min_len], alternative="two-sided"
            )
            return {
                "test": "Wilcoxon signed-rank (sumas 1ª vs 2ª mitad)",
                "statistic": round(stat, 4),
                "p_value": round(p_val, 6),
                "significant_at_05": p_val < 0.05,
                "median_first": round(np.median(first_half), 2),
                "median_second": round(np.median(second_half), 2),
                "interpretation": (
                    "Sin cambio sistemático en las sumas a lo largo del tiempo"
                    if p_val >= 0.05
                    else "Se detecta un desplazamiento sistemático en las sumas"
                ),
            }
        return {
            "test": "Wilcoxon Signed-Rank Test",
            "error": "Insufficient paired data",
        }

    def test_normality_shapiro(self, df: pd.DataFrame) -> Dict:
        """Shapiro-Wilk test for normality of draw sums."""
        sums = [sum(nums) for nums in df["numbers"]]
        # Sample for large datasets
        sample = np.random.default_rng(42).choice(
            sums, min(5000, len(sums)), replace=False
        )
        stat, p_val = stats.shapiro(sample)
        return {
            "test": "Shapiro-Wilk (normalidad de las sumas)",
            "statistic": round(stat, 4),
            "p_value": round(p_val, 6),
            "significant_at_05": p_val < 0.05,
            "sample_size": len(sample),
            "skewness": round(float(stats.skew(sums)), 4),
            "kurtosis_excess": round(float(stats.kurtosis(sums)), 4),
            "interpretation": (
                "No se detecta desviación relevante de la normalidad (la suma es "
                "discreta y acotada por construcción: no puede ser normal)"
                if p_val >= 0.05
                else "Las sumas se desvían de la normalidad"
            ),
        }

    def test_anderson_darling(self, df: pd.DataFrame) -> Dict:
        """Anderson-Darling test for normality."""
        sums = [sum(nums) for nums in df["numbers"]]
        sample = np.random.default_rng(42).choice(
            sums, min(5000, len(sums)), replace=False
        )
        result = stats.anderson(sample, dist="norm")
        # Use 5% significance level (index 2)
        critical_5pct = result.critical_values[2]
        return {
            "test": "Anderson-Darling (normalidad de las sumas)",
            "statistic": round(result.statistic, 4),
            "critical_value_5pct": round(critical_5pct, 4),
            "significant_at_05": result.statistic > critical_5pct,
            "interpretation": (
                "No se detecta desviación relevante de la normalidad"
                if result.statistic <= critical_5pct
                else "Las sumas se desvían de la normalidad"
            ),
        }

    # ==================== PREDICTIVE MODELING ====================

    def markov_chain_predictions(self, df: pd.DataFrame, order: int = 1) -> Dict:
        """Markov chain model for number transitions."""
        # Build transition matrix for numbers appearing in consecutive draws
        transitions = {i: Counter() for i in range(1, 44)}

        for i in range(1, len(df)):
            prev_nums = set(df.iloc[i - 1]["numbers"])
            curr_nums = set(df.iloc[i]["numbers"])
            for prev in prev_nums:
                for curr in curr_nums:
                    transitions[prev][curr] += 1

        # Normalize to probabilities
        trans_probs = {}
        for prev in range(1, 44):
            total = sum(transitions[prev].values())
            if total > 0:
                trans_probs[prev] = {
                    curr: count / total for curr, count in transitions[prev].items()
                }

        # Predict next draw based on last draw
        last_draw = set(df.iloc[-1]["numbers"])
        predictions = Counter()
        for num in last_draw:
            if num in trans_probs:
                for next_num, prob in trans_probs[num].items():
                    predictions[next_num] += prob

        # Normalize
        total_pred = sum(predictions.values())
        normalized = (
            {k: v / total_pred * 5 for k, v in predictions.items()}
            if total_pred > 0
            else {}
        )
        sorted_pred = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))

        return {
            "model": f"Markov Chain (Order {order})",
            "transition_matrix_size": f"{43}x{43}",
            "predictions": sorted_pred,
            "top_5": list(sorted_pred.keys())[:5],
            "top_10": list(sorted_pred.keys())[:10],
            "confidence": "Very Low - Markov assumption violated in lottery",
        }

    def regression_trend_analysis(self, df: pd.DataFrame) -> Dict:
        """Linear regression for trend detection in sums and frequencies."""
        n = len(df)
        x = np.arange(n)

        # Trend in sums
        sums = np.array([sum(nums) for nums in df["numbers"]])
        slope_sum, intercept_sum, r_sum, p_sum, se_sum = stats.linregress(x, sums)

        # Trend in individual number frequencies over time (ventanas NO solapadas:
        # con ventanas deslizantes de 1 en 1 los puntos comparten 99/100 y el EE
        # del OLS es ficticio)
        window = min(100, n // 4)
        freq_trends = {}
        for num in range(1, 44):
            freq_over_time = []
            for i in range(window, n + 1, window):
                window_draws = df.iloc[i - window : i]
                count = sum(1 for nums in window_draws["numbers"] if num in nums)
                freq_over_time.append(count)

            if len(freq_over_time) > 10:
                x_win = np.arange(len(freq_over_time))
                slope, _, _, p_val, _ = stats.linregress(x_win, freq_over_time)
                freq_trends[num] = {
                    "slope": round(slope, 6),
                    "p_value": round(p_val, 6),
                }

        # FDR sobre los 43 números antes de declarar tendencias
        if freq_trends:
            nums_sorted = sorted(freq_trends)
            reject = self._fdr_bh([freq_trends[n]["p_value"] for n in nums_sorted])
            for n, rej in zip(nums_sorted, reject):
                freq_trends[n]["fdr_significant"] = bool(rej)
        else:
            reject = []

        # Numbers with significant trends (tras FDR)
        trending_up = [
            n
            for n, t in freq_trends.items()
            if t.get("fdr_significant") and t["slope"] > 0
        ]
        trending_down = [
            n
            for n, t in freq_trends.items()
            if t.get("fdr_significant") and t["slope"] < 0
        ]

        return {
            "model": "Linear Regression Trend Analysis (ventanas no solapadas)",
            "sum_trend": {
                "slope_per_draw": round(slope_sum, 6),
                "r_squared": round(r_sum**2, 6),
                "p_value": round(p_sum, 6),
                "significant": p_sum < 0.05,
                "interpretation": (
                    "Sin tendencia en las sumas"
                    if p_sum >= 0.05
                    else (
                        "Tendencia creciente"
                        if slope_sum > 0
                        else "Tendencia decreciente"
                    )
                ),
            },
            "number_frequency_trends": {
                "trending_up": trending_up[:10],
                "trending_down": trending_down[:10],
                "total_significant": len(trending_up) + len(trending_down),
                "fdr_method": "Benjamini-Hochberg sobre los 43 números",
            },
            "confidence": "Low - lottery draws are independent random events",
        }

    def exponential_smoothing_forecast(
        self, df: pd.DataFrame, alpha: float = 0.3
    ) -> Dict:
        """Simple exponential smoothing for number frequency forecasting."""
        # For each number, compute EWMA of appearance frequency
        predictions = {}
        for num in range(1, 44):
            # Binary series: 1 if drawn, 0 if not
            series = [1 if num in nums else 0 for nums in df["numbers"]]

            # Exponential smoothing
            ewma = series[0]
            for val in series[1:]:
                ewma = alpha * val + (1 - alpha) * ewma

            predictions[num] = ewma

        # Normalize to 5 numbers
        total = sum(predictions.values())
        normalized = {k: v / total * 5 for k, v in predictions.items()}
        sorted_pred = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))

        return {
            "model": f"Exponential Smoothing (α={alpha})",
            "predictions": sorted_pred,
            "top_5": list(sorted_pred.keys())[:5],
            "top_10": list(sorted_pred.keys())[:10],
            "confidence": "Very Low - No predictive power in random draws",
        }

    def ensemble_prediction(self, df: pd.DataFrame) -> Dict:
        """Combine multiple prediction methods with weights."""
        # Get predictions from different methods
        bayesian = self.predict_next_draw_probabilities(df)
        markov = self.markov_chain_predictions(df)
        exp_smooth = self.exponential_smoothing_forecast(df)

        # Weighted ensemble
        weights = {"bayesian": 0.5, "markov": 0.25, "exp_smooth": 0.25}
        ensemble = Counter()

        for num in range(1, 44):
            score = 0
            score += weights["bayesian"] * bayesian["probabilities"].get(num, 0)
            score += weights["markov"] * markov["predictions"].get(num, 0)
            score += weights["exp_smooth"] * exp_smooth["predictions"].get(num, 0)
            ensemble[num] = score

        # Normalize
        total = sum(ensemble.values())
        normalized = {k: v / total * 5 for k, v in ensemble.items()}
        sorted_ens = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))

        return {
            "model": "Ensemble (Bayesian 50% + Markov 25% + ExpSmoothing 25%)",
            "predictions": sorted_ens,
            "top_5": list(sorted_ens.keys())[:5],
            "top_10": list(sorted_ens.keys())[:10],
            "component_weights": weights,
            "confidence": "Very Low - All components have no predictive validity",
        }

    def run_full_analysis(self) -> Dict:
        """Run complete statistical analysis."""
        logger.info("Running full statistical analysis...")

        self.load_data()

        # Descriptive statistics
        logger.info("Computing descriptive statistics...")
        self.results["descriptive"] = {
            "number_frequencies": self.analyze_number_frequencies(self.baloto_df),
            "superbalota_frequencies": self.analyze_superbalota_frequencies(
                self.baloto_df
            ),
            "position_frequencies": self.analyze_position_frequencies(self.baloto_df),
            "sum_statistics": self.analyze_sum_statistics(self.baloto_df),
            "odd_even_balance": self.analyze_odd_even_balance(self.baloto_df),
            "high_low_balance": self.analyze_high_low_balance(self.baloto_df),
            "consecutive_numbers": self.analyze_consecutive_numbers(self.baloto_df),
            "number_gaps": self.analyze_number_gaps(self.baloto_df),
            "repeating_numbers": self.analyze_repeating_numbers(self.baloto_df),
            "jackpot_statistics": self.analyze_jackpot_statistics(self.baloto_df),
            "revancha_number_frequencies": self.analyze_number_frequencies(
                self.revancha_df
            ),
            "revancha_superbalota_frequencies": self.analyze_superbalota_frequencies(
                self.revancha_df
            ),
        }

        # Inferential statistics
        logger.info("Computing inferential statistics...")
        self.results["inferential"] = {
            "parametric": {
                "uniformity_test": self.test_uniformity(self.baloto_df),
                "independence_test": self.test_independence(self.baloto_df),
                "hot_cold_significance": self.test_hot_cold_significance(
                    self.baloto_df
                ),
                "confidence_intervals": self.calculate_confidence_intervals(
                    self.baloto_df
                ),
                "normality_shapiro": self.test_normality_shapiro(self.baloto_df),
                "normality_anderson": self.test_anderson_darling(self.baloto_df),
            },
            "non_parametric": {
                "mann_whitney_odd_even": self.test_mann_whitney_odd_even(
                    self.baloto_df
                ),
                "kruskal_wallis_position": self.test_position_uniformity(
                    self.baloto_df
                ),
                "friedman_consecutive": self.test_friedman_consecutive(self.baloto_df),
                "wilcoxon_signed_rank": self.test_wilcoxon_signed_rank_pairs(
                    self.baloto_df
                ),
            },
        }

        # Predictive modeling
        logger.info("Generating predictive models...")
        self.results["predictive_modeling"] = {
            "bayesian": self.predict_next_draw_probabilities(self.baloto_df),
            "bayesian_superbalota": self.predict_superbalota_probabilities(
                self.baloto_df
            ),
            "markov_chain": self.markov_chain_predictions(self.baloto_df),
            "regression_trends": self.regression_trend_analysis(self.baloto_df),
            "exponential_smoothing": self.exponential_smoothing_forecast(
                self.baloto_df
            ),
            "ensemble": self.ensemble_prediction(self.baloto_df),
        }

        # Predictions (legacy format for frontend compatibility)
        logger.info("Generating predictions...")
        self.results["predictions"] = {
            "next_draw_numbers": self.predict_next_draw_probabilities(self.baloto_df),
            "next_superbalota": self.predict_superbalota_probabilities(self.baloto_df),
        }

        # Metadata
        self.results["metadata"] = {
            # Determinista: derivado del dato, no del reloj (permite detectar
            # cambios reales en el artefacto commiteado).
            "analysis_date": self.metadata.get("date_range", {}).get("end")
            or datetime.now().date().isoformat(),
            "data_source": self.metadata,
            "total_draws_analyzed": len(self.baloto_df),
            "disclaimer": "Lottery draws are independent random events. Past performance does not predict future results. This analysis is for entertainment and educational purposes only.",
        }

        # Save results
        output_path = self.data_dir / "analysis_results.json"
        tmp_path = output_path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(
                _sanitize_json(convert_to_serializable(self.results)),
                f,
                indent=2,
                allow_nan=False,
            )
        tmp_path.replace(output_path)

        logger.info(f"Analysis complete! Results saved to {output_path}")
        return self.results


if __name__ == "__main__":
    analyzer = BalotoAnalyzer()
    analyzer.run_full_analysis()
