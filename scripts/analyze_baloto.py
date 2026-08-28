#!/usr/bin/env python3
"""
Baloto Statistical Analysis Engine
Performs comprehensive descriptive and inferential statistical analysis
on Baloto lottery historical data.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from scipy.stats import chi2_contingency, norm, poisson
from collections import Counter
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        
        with open(self.data_dir / "baloto.json", "r") as f:
            baloto_data = json.load(f)
        with open(self.data_dir / "revancha.json", "r") as f:
            revancha_data = json.load(f)
        with open(self.data_dir / "metadata.json", "r") as f:
            self.metadata = json.load(f)
        
        self.baloto_df = pd.DataFrame(baloto_data)
        self.revancha_df = pd.DataFrame(revancha_data)
        
        # Ensure numbers are lists
        for df in [self.baloto_df, self.revancha_df]:
            if isinstance(df["numbers"].iloc[0], str):
                df["numbers"] = df["numbers"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        
        logger.info(f"Loaded {len(self.baloto_df)} Baloto draws and {len(self.revancha_df)} Revancha draws")
    
    # ==================== DESCRIPTIVE STATISTICS ====================
    
    def analyze_number_frequencies(self, df: pd.DataFrame, number_col: str = "numbers", 
                                    max_num: int = 43) -> Dict:
        """Analyze frequency of each number."""
        all_numbers = []
        for nums in df[number_col]:
            all_numbers.extend(nums)
        
        freq = Counter(all_numbers)
        total_draws = len(df)
        expected_freq = total_draws * 5 / max_num  # 5 numbers per draw
        
        frequencies = {}
        for i in range(1, max_num + 1):
            count = freq.get(i, 0)
            frequencies[i] = {
                "count": count,
                "percentage": round(count / total_draws * 100, 2),
                "expected": round(expected_freq, 2),
                "deviation": round(count - expected_freq, 2),
                "z_score": round((count - expected_freq) / np.sqrt(expected_freq), 3) if expected_freq > 0 else 0
            }
        
        # Sort by frequency
        sorted_freq = dict(sorted(frequencies.items(), key=lambda x: x[1]["count"], reverse=True))
        
        return {
            "frequencies": sorted_freq,
            "total_draws": total_draws,
            "total_numbers_drawn": len(all_numbers),
            "expected_per_number": round(expected_freq, 2),
            "hot_numbers": [k for k, v in sorted_freq.items() if v["z_score"] > 1.5],
            "cold_numbers": [k for k, v in sorted_freq.items() if v["z_score"] < -1.5],
            "chi2_statistic": sum((v["count"] - expected_freq)**2 / expected_freq for v in frequencies.values()),
            "chi2_p_value": 1 - stats.chi2.cdf(
                sum((v["count"] - expected_freq)**2 / expected_freq for v in frequencies.values()), 
                max_num - 1
            )
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
                "z_score": round((count - expected_freq) / np.sqrt(expected_freq), 3) if expected_freq > 0 else 0
            }
        
        sorted_freq = dict(sorted(frequencies.items(), key=lambda x: x[1]["count"], reverse=True))
        
        return {
            "frequencies": sorted_freq,
            "total_draws": total_draws,
            "hot_superbalotas": [k for k, v in sorted_freq.items() if v["z_score"] > 1],
            "cold_superbalotas": [k for k, v in sorted_freq.items() if v["z_score"] < -1],
            "chi2_p_value": 1 - stats.chi2.cdf(
                sum((v["count"] - expected_freq)**2 / expected_freq for v in frequencies.values()), 
                15
            )
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
            total = len(positions[pos])
            position_analysis[f"position_{pos+1}"] = {
                "frequencies": dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)),
                "most_common": freq.most_common(5),
                "least_common": freq.most_common()[-5:],
                "mean": round(np.mean(positions[pos]), 2),
                "std": round(np.std(positions[pos]), 2),
                "median": round(np.median(positions[pos]), 2)
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
                "95": round(np.percentile(sums, 95), 2)
            },
            "distribution": Counter(sums),
            "theoretical_mean": 5 * 22,  # 5 numbers * average of 1-43
            "theoretical_std": round(np.sqrt(5 * (43**2 - 1) / 12), 2)
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
            "distribution": {f"{o}-{e}": count for (o, e), count in distribution.items()},
            "percentages": {f"{o}-{e}": round(count/total*100, 2) for (o, e), count in distribution.items()},
            "avg_odd": round(np.mean([o for o, e in odd_even_counts]), 2),
            "avg_even": round(np.mean([e for o, e in odd_even_counts]), 2),
            "most_common_pattern": max(distribution, key=distribution.get)
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
            "distribution": {f"{h}-{l}": count for (h, l), count in distribution.items()},
            "percentages": {f"{h}-{l}": round(count/total*100, 2) for (h, l), count in distribution.items()},
            "avg_high": round(np.mean([h for h, l in high_low_counts]), 2),
            "avg_low": round(np.mean([l for h, l in high_low_counts]), 2)
        }
    
    def analyze_consecutive_numbers(self, df: pd.DataFrame) -> Dict:
        """Analyze consecutive number pairs."""
        consecutive_counts = []
        for nums in df["numbers"]:
            consec = sum(1 for i in range(4) if nums[i+1] == nums[i] + 1)
            consecutive_counts.append(consec)
        
        distribution = Counter(consecutive_counts)
        total = len(consecutive_counts)
        
        return {
            "distribution": dict(distribution),
            "percentages": {k: round(v/total*100, 2) for k, v in distribution.items()},
            "avg_consecutive": round(np.mean(consecutive_counts), 2),
            "probability_at_least_one": round(sum(1 for c in consecutive_counts if c > 0) / total * 100, 2)
        }
    
    def analyze_number_gaps(self, df: pd.DataFrame) -> Dict:
        """Analyze gaps between drawn numbers."""
        all_gaps = []
        for nums in df["numbers"]:
            for i in range(4):
                gap = nums[i+1] - nums[i]
                all_gaps.append(gap)
        
        return {
            "mean_gap": round(np.mean(all_gaps), 2),
            "median_gap": round(np.median(all_gaps), 2),
            "std_gap": round(np.std(all_gaps), 2),
            "min_gap": int(np.min(all_gaps)),
            "max_gap": int(np.max(all_gaps)),
            "gap_distribution": dict(Counter(all_gaps).most_common())
        }
    
    def analyze_repeating_numbers(self, df: pd.DataFrame, lookback: int = 10) -> Dict:
        """Analyze numbers that repeat from recent draws."""
        repeats = []
        for i in range(lookback, len(df)):
            current_nums = set(df.iloc[i]["numbers"])
            prev_nums = set()
            for j in range(max(0, i-lookback), i):
                prev_nums.update(df.iloc[j]["numbers"])
            repeat_count = len(current_nums & prev_nums)
            repeats.append(repeat_count)
        
        distribution = Counter(repeats)
        total = len(repeats)
        
        return {
            "distribution": dict(distribution),
            "percentages": {k: round(v/total*100, 2) for k, v in distribution.items()},
            "avg_repeats": round(np.mean(repeats), 2),
            "probability_at_least_one": round(sum(1 for r in repeats if r > 0) / total * 100, 2)
        }
    
    def analyze_jackpot_statistics(self, df: pd.DataFrame) -> Dict:
        """Analyze jackpot amounts and rollover patterns."""
        jackpots = df["jackpot"].tolist()
        
        # Calculate rollovers (jackpot increases)
        rollovers = []
        for i in range(1, len(jackpots)):
            if jackpots[i] > jackpots[i-1]:
                rollovers.append(jackpots[i] - jackpots[i-1])
            else:
                rollovers.append(0)
        
        return {
            "current_jackpot": jackpots[-1],
            "mean_jackpot": round(np.mean(jackpots), 2),
            "median_jackpot": round(np.median(jackpots), 2),
            "max_jackpot": max(jackpots),
            "min_jackpot": min(jackpots),
            "std_jackpot": round(np.std(jackpots), 2),
            "total_rollovers": sum(1 for r in rollovers if r > 0),
            "avg_rollover_amount": round(np.mean([r for r in rollovers if r > 0]), 2) if any(r > 0 for r in rollovers) else 0,
            "rollover_frequency": round(sum(1 for r in rollovers if r > 0) / len(rollovers) * 100, 2) if rollovers else 0
        }
    
    # ==================== INFERENTIAL STATISTICS ====================
    
    def _cramers_v(self, chi2_stat: float, n: int, min_dim: int) -> float:
        """Cramer's V effect size for chi-square tests."""
        if n == 0 or min_dim <= 1:
            return 0.0
        return float(np.sqrt(chi2_stat / (n * (min_dim - 1))))

    def _effect_size_label(self, v: float, kind: str = "v") -> str:
        """Label effect size magnitude per Cohen conventions."""
        if kind == "v":  # Cramer's V
            bounds = [(0.1, "pequeño"), (0.3, "mediano"), (float("inf"), "grande")]
        elif kind == "d":  # Cohen's d
            bounds = [(0.2, "pequeño"), (0.5, "mediano"), (float("inf"), "grande")]
        elif kind == "eta":  # Eta-squared / epsilon-squared
            bounds = [(0.01, "pequeño"), (0.06, "mediano"), (float("inf"), "grande")]
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

    def _power_chi2_gof(self, w: float, n: int, dof: int, alpha: float = 0.05) -> float:
        """Statistical power for chi-square GOF with effect size w (Cohen)."""
        if w <= 0 or n <= 0:
            return 0.0
        # Non-centrality parameter lambda = n * w^2
        lam = n * w * w
        crit = stats.chi2.ppf(1 - alpha, dof)
        return float(stats.ncx2.sf(crit, dof, lam))

    def test_uniformity(self, df: pd.DataFrame, max_num: int = 43) -> Dict:
        """Chi-square test for uniformity of number distribution."""
        freq_result = self.analyze_number_frequencies(df, max_num=max_num)
        observed = [v["count"] for v in freq_result["frequencies"].values()]
        expected_raw = [freq_result["expected_per_number"]] * max_num
        
        # Normalize expected to match observed sum (fix floating point precision)
        observed_sum = sum(observed)
        expected_sum = sum(expected_raw)
        expected = [e * observed_sum / expected_sum for e in expected_raw]
        
        chi2_stat, p_value = stats.chisquare(observed, expected)
        n = observed_sum
        dof = max_num - 1
        # Effect size: Cohen's W (chi2 / N) - reference-free, scales with sample
        w = float(np.sqrt(chi2_stat / n)) if n > 0 else 0.0
        cramers_v = self._cramers_v(chi2_stat, n, 2)
        power = self._power_chi2_gof(w, n, dof)
        
        return {
            "test": "Chi-square Goodness of Fit (Uniform Distribution)",
            "chi2_statistic": round(chi2_stat, 4),
            "p_value": round(p_value, 6),
            "degrees_of_freedom": dof,
            "sample_size": n,
            "significant_at_05": p_value < 0.05,
            "significant_at_01": p_value < 0.01,
            "interpretation": "Numbers follow uniform distribution" if p_value >= 0.05 else "Numbers deviate from uniform distribution",
            "effect_size": {
                "cohens_w": round(w, 4),
                "cramers_v": round(cramers_v, 4),
                "label": self._effect_size_label(cramers_v, "v")
            },
            "power_analysis": {
                "power_at_05": round(power, 4),
                "power_interpretation": "Adequate" if power >= 0.8 else "Insufficient to detect small deviations"
            }
        }
    
    def test_independence(self, df: pd.DataFrame) -> Dict:
        """Test independence between draws (autocorrelation)."""
        # Convert draws to binary matrix (number drawn or not)
        max_num = 43
        draws_matrix = np.zeros((len(df), max_num))
        for i, nums in enumerate(df["numbers"]):
            for n in nums:
                draws_matrix[i, n-1] = 1
        
        # Test lag-1 autocorrelation for each number
        autocorrelations = []
        for n in range(max_num):
            series = draws_matrix[:, n]
            if np.std(series) > 0:
                corr = np.corrcoef(series[:-1], series[1:])[0, 1]
                if not np.isnan(corr):
                    autocorrelations.append(corr)
        
        mean_autocorr = np.mean(autocorrelations) if autocorrelations else 0
        
        # Ljung-Box test approximation
        n = len(df)
        lb_stat = n * (n + 2) * sum(ac**2 / (n - k) for k, ac in enumerate(autocorrelations[:10], 1))
        lb_p = 1 - stats.chi2.cdf(lb_stat, 10) if autocorrelations else 1
        
        return {
            "test": "Ljung-Box Test for Autocorrelation (Independence of Draws)",
            "mean_autocorrelation": round(mean_autocorr, 6),
            "ljung_box_statistic": round(lb_stat, 4),
            "p_value": round(lb_p, 6),
            "significant_at_05": lb_p < 0.05,
            "interpretation": "Draws appear independent" if lb_p >= 0.05 else "Possible autocorrelation detected"
        }
    
    def test_hot_cold_significance(self, df: pd.DataFrame) -> Dict:
        """Test if hot/cold numbers are statistically significant."""
        freq_result = self.analyze_number_frequencies(df)
        
        hot_numbers = freq_result["hot_numbers"]
        cold_numbers = freq_result["cold_numbers"]
        
        # Binomial test for each hot number
        hot_significant = []
        cold_significant = []
        total_draws = freq_result["total_draws"]
        p_expected = 5 / 43  # Probability of any number being drawn
        
        for num in hot_numbers:
            count = freq_result["frequencies"][num]["count"]
            # Binomial test: P(X >= count) under null
            p_val = 1 - stats.binom.cdf(count - 1, total_draws, p_expected)
            hot_significant.append({"number": num, "count": count, "p_value": round(p_val, 6)})
        
        for num in cold_numbers:
            count = freq_result["frequencies"][num]["count"]
            p_val = stats.binom.cdf(count, total_draws, p_expected)
            cold_significant.append({"number": num, "count": count, "p_value": round(p_val, 6)})
        
        # Multiple-comparison corrections (all 43 numbers tested)
        all_details = hot_significant + cold_significant
        all_p = [h["p_value"] for h in all_details]
        bh_reject = self._fdr_bh(all_p, 0.05)
        bonferroni_threshold = 0.05 / 43
        for det, rej in zip(all_details, bh_reject):
            det["fdr_significant_at_05"] = bool(rej)
            det["bonferroni_significant_at_05"] = det["p_value"] < bonferroni_threshold
        
        hot_reject_count = sum(1 for h in hot_significant if h.get("fdr_significant_at_05", False))
        cold_reject_count = sum(1 for c in cold_significant if c.get("fdr_significant_at_05", False))
        
        return {
            "hot_numbers_tested": len(hot_significant),
            "cold_numbers_tested": len(cold_significant),
            "hot_significant_at_05": sum(1 for h in hot_significant if h["p_value"] < 0.05),
            "cold_significant_at_05": sum(1 for c in cold_significant if c["p_value"] < 0.05),
            "hot_fdr_significant_at_05": hot_reject_count,
            "cold_fdr_significant_at_05": cold_reject_count,
            "hot_details": hot_significant,
            "cold_details": cold_significant,
            "bonferroni_threshold": round(bonferroni_threshold, 6),  # Multiple comparison correction
            "fdr_method": "Benjamini-Hochberg (FDR ≤ 0.05)",  # Multiple comparison correction
            "interpretation": "Hot/cold patterns may be due to chance" if all(h["p_value"] > bonferroni_threshold for h in hot_significant) and all(c["p_value"] > bonferroni_threshold for c in cold_significant) else "Some numbers show significant deviation"
        }
    
    def predict_next_draw_probabilities(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """Calculate probabilities for next draw based on recent trends."""
        recent_df = df.tail(lookback)
        
        # Recent frequencies
        recent_freq = self.analyze_number_frequencies(recent_df)
        overall_freq = self.analyze_number_frequencies(df)
        
        # Bayesian update: combine prior (overall) with likelihood (recent)
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
        sorted_probs = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "probabilities": sorted_probs,
            "top_5_most_likely": list(sorted_probs.keys())[:5],
            "top_10_most_likely": list(sorted_probs.keys())[:10],
            "methodology": "Bayesian update with Beta-Binomial conjugate prior",
            "lookback_period": lookback,
            "confidence": "Low - lottery draws are independent random events"
        }
    
    def predict_superbalota_probabilities(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """Predict Superbalota probabilities."""
        recent_df = df.tail(lookback)
        
        recent_freq = self.analyze_superbalota_frequencies(recent_df)
        overall_freq = self.analyze_superbalota_frequencies(df)
        
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
        
        sorted_probs = dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "probabilities": sorted_probs,
            "most_likely": list(sorted_probs.keys())[:3],
            "methodology": "Bayesian update with Beta-Binomial conjugate prior"
        }
    
    def calculate_confidence_intervals(self, df: pd.DataFrame, confidence: float = 0.95) -> Dict:
        """Calculate confidence intervals for key statistics."""
        total_draws = len(df)
        
        # CI for mean sum
        sums = [sum(nums) for nums in df["numbers"]]
        mean_sum = np.mean(sums)
        se_sum = stats.sem(sums)
        ci_sum = stats.t.interval(confidence, len(sums)-1, loc=mean_sum, scale=se_sum)
        
        # CI for number frequency (using normal approximation)
        freq_result = self.analyze_number_frequencies(df)
        p_hat = 5/43  # Expected probability
        se_p = np.sqrt(p_hat * (1 - p_hat) / total_draws)
        z = stats.norm.ppf((1 + confidence) / 2)
        ci_freq = (p_hat - z * se_p, p_hat + z * se_p)
        
        return {
            "confidence_level": confidence,
            "mean_sum_ci": [round(ci_sum[0], 2), round(ci_sum[1], 2)],
            "number_frequency_ci": [round(ci_freq[0], 4), round(ci_freq[1], 4)],
            "interpretation": f"We are {confidence*100}% confident the true mean sum lies in the interval"
        }
    
    # ==================== NON-PARAMETRIC TESTS ====================
    
    def test_mann_whitney_odd_even(self, df: pd.DataFrame
    ) -> Dict:
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
            stat, p_val = stats.mannwhitneyu(odd_heavy_sums, even_heavy_sums, alternative='two-sided')
            # Effect size r = Z / sqrt(N) via normal approximation, or rank-biserial correlation
            mu = n1 * n2 / 2.0
            sigma = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
            z = (stat - mu) / sigma if sigma > 0 else 0.0
            r_effect = abs(z) / np.sqrt(n1 + n2) if (n1 + n2) > 0 else 0.0
            # Rank-biserial correlation (alternate effect size, signed)
            rank_biserial = 1.0 - (2.0 * stat) / (n1 * n2)
            return {
                "test": "Mann-Whitney U Test (Odd-heavy vs Even-heavy Draw Sums)",
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
                    "label": self._effect_size_label(r_effect, "r")
                },
                "interpretation": "No difference in sum distributions" if p_val >= 0.05 else "Significant difference in sums by parity composition"
            }
        return {"test": "Mann-Whitney U Test", "error": "Insufficient samples"}
    
    def test_kruskal_wallis_position(self, df: pd.DataFrame) -> Dict:
        """Kruskal-Wallis test: Compare number distributions across positions."""
        position_data = []
        for pos in range(5):
            position_data.append([nums[pos] for nums in df["numbers"]])
        
        stat, p_val = stats.kruskal(*position_data)
        n_total = sum(len(p) for p in position_data)
        k = 5
        # Eta-squared for Kruskal-Wallis: eta2_H = (H - k + 1) / (N - k)
        eta_sq = (stat - k + 1) / (n_total - k) if n_total > k else 0.0
        return {
            "test": "Kruskal-Wallis Test (Position Distribution Equality)",
            "statistic": round(stat, 4),
            "p_value": round(p_val, 6),
            "significant_at_05": p_val < 0.05,
            "n_total": n_total,
            "effect_size": {
                "eta_squared": round(max(eta_sq, 0.0), 4),
                "label": self._effect_size_label(eta_sq, "eta")
            },
            "interpretation": "All positions have same distribution" if p_val >= 0.05 else "At least one position differs in distribution"
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
                consec = sum(1 for i in range(4) if nums[i+1] == nums[i] + 1)
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
                "test": "Friedman Test (Consecutive Numbers Across Time Periods)",
                "statistic": round(stat, 4),
                "p_value": round(p_val, 6),
                "significant_at_05": p_val < 0.05,
                "sample_size_per_period": min_len,
                "effect_size": {
                    "kendalls_w": round(kendall_w, 4),
                    "label": self._effect_size_label(kendall_w, "w")
                },
                "interpretation": "Consecutive pattern stable over time" if p_val >= 0.05 else "Consecutive pattern changes over time"
            }
        return {"test": "Friedman Test", "error": "Insufficient data"}
    
    def test_wilcoxon_signed_rank_pairs(self, df: pd.DataFrame) -> Dict:
        """Wilcoxon signed-rank test: Compare first half vs second half draw sums."""
        mid = len(df) // 2
        first_half = [sum(nums) for nums in df.iloc[:mid]["numbers"]]
        second_half = [sum(nums) for nums in df.iloc[mid:]["numbers"]]
        
        # Pair by index
        min_len = min(len(first_half), len(second_half))
        if min_len > 10:
            stat, p_val = stats.wilcoxon(first_half[:min_len], second_half[:min_len], alternative='two-sided')
            return {
                "test": "Wilcoxon Signed-Rank Test (First vs Second Half Sums)",
                "statistic": round(stat, 4),
                "p_value": round(p_val, 6),
                "significant_at_05": p_val < 0.05,
                "median_first": round(np.median(first_half), 2),
                "median_second": round(np.median(second_half), 2),
                "interpretation": "No systematic change in sums over time" if p_val >= 0.05 else "Systematic shift in draw sums detected"
            }
        return {"test": "Wilcoxon Signed-Rank Test", "error": "Insufficient paired data"}
    
    def test_normality_shapiro(self, df: pd.DataFrame) -> Dict:
        """Shapiro-Wilk test for normality of draw sums."""
        sums = [sum(nums) for nums in df["numbers"]]
        # Sample for large datasets
        sample = np.random.choice(sums, min(5000, len(sums)), replace=False)
        stat, p_val = stats.shapiro(sample)
        return {
            "test": "Shapiro-Wilk Test (Normality of Draw Sums)",
            "statistic": round(stat, 4),
            "p_value": round(p_val, 6),
            "significant_at_05": p_val < 0.05,
            "sample_size": len(sample),
            "interpretation": "Sums follow normal distribution" if p_val >= 0.05 else "Sums deviate from normality"
        }
    
    def test_anderson_darling(self, df: pd.DataFrame) -> Dict:
        """Anderson-Darling test for normality."""
        sums = [sum(nums) for nums in df["numbers"]]
        sample = np.random.choice(sums, min(5000, len(sums)), replace=False)
        result = stats.anderson(sample, dist='norm')
        # Use 5% significance level (index 2)
        critical_5pct = result.critical_values[2]
        return {
            "test": "Anderson-Darling Test (Normality of Draw Sums)",
            "statistic": round(result.statistic, 4),
            "critical_value_5pct": round(critical_5pct, 4),
            "significant_at_05": result.statistic > critical_5pct,
            "interpretation": "Sums follow normal distribution" if result.statistic <= critical_5pct else "Sums deviate from normality"
        }
    
    # ==================== PREDICTIVE MODELING ====================
    
    def markov_chain_predictions(self, df: pd.DataFrame, order: int = 1) -> Dict:
        """Markov chain model for number transitions."""
        # Build transition matrix for numbers appearing in consecutive draws
        transitions = {i: Counter() for i in range(1, 44)}
        
        for i in range(1, len(df)):
            prev_nums = set(df.iloc[i-1]["numbers"])
            curr_nums = set(df.iloc[i]["numbers"])
            for prev in prev_nums:
                for curr in curr_nums:
                    transitions[prev][curr] += 1
        
        # Normalize to probabilities
        trans_probs = {}
        for prev in range(1, 44):
            total = sum(transitions[prev].values())
            if total > 0:
                trans_probs[prev] = {curr: count/total for curr, count in transitions[prev].items()}
        
        # Predict next draw based on last draw
        last_draw = set(df.iloc[-1]["numbers"])
        predictions = Counter()
        for num in last_draw:
            if num in trans_probs:
                for next_num, prob in trans_probs[num].items():
                    predictions[next_num] += prob
        
        # Normalize
        total_pred = sum(predictions.values())
        normalized = {k: v/total_pred*5 for k, v in predictions.items()} if total_pred > 0 else {}
        sorted_pred = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "model": f"Markov Chain (Order {order})",
            "transition_matrix_size": f"{43}x{43}",
            "predictions": sorted_pred,
            "top_5": list(sorted_pred.keys())[:5],
            "top_10": list(sorted_pred.keys())[:10],
            "confidence": "Very Low - Markov assumption violated in lottery"
        }
    
    def regression_trend_analysis(self, df: pd.DataFrame) -> Dict:
        """Linear regression for trend detection in sums and frequencies."""
        n = len(df)
        x = np.arange(n)
        
        # Trend in sums
        sums = np.array([sum(nums) for nums in df["numbers"]])
        slope_sum, intercept_sum, r_sum, p_sum, se_sum = stats.linregress(x, sums)
        
        # Trend in individual number frequencies over time (sliding window)
        window = min(100, n // 4)
        freq_trends = {}
        for num in range(1, 44):
            freq_over_time = []
            for i in range(window, n):
                window_draws = df.iloc[i-window:i]
                count = sum(1 for nums in window_draws["numbers"] if num in nums)
                freq_over_time.append(count)
            
            if len(freq_over_time) > 10:
                x_win = np.arange(len(freq_over_time))
                slope, _, _, p_val, _ = stats.linregress(x_win, freq_over_time)
                freq_trends[num] = {"slope": round(slope, 6), "p_value": round(p_val, 6)}
        
        # Numbers with significant trends
        trending_up = [n for n, t in freq_trends.items() if t["p_value"] < 0.05 and t["slope"] > 0]
        trending_down = [n for n, t in freq_trends.items() if t["p_value"] < 0.05 and t["slope"] < 0]
        
        return {
            "model": "Linear Regression Trend Analysis",
            "sum_trend": {
                "slope_per_draw": round(slope_sum, 6),
                "r_squared": round(r_sum**2, 6),
                "p_value": round(p_sum, 6),
                "significant": p_sum < 0.05,
                "interpretation": "No trend in sums" if p_sum >= 0.05 else ("Increasing trend" if slope_sum > 0 else "Decreasing trend")
            },
            "number_frequency_trends": {
                "trending_up": trending_up[:10],
                "trending_down": trending_down[:10],
                "total_significant": len(trending_up) + len(trending_down)
            },
            "confidence": "Low - Multiple testing not corrected"
        }
    
    def exponential_smoothing_forecast(self, df: pd.DataFrame, alpha: float = 0.3) -> Dict:
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
        normalized = {k: v/total*5 for k, v in predictions.items()}
        sorted_pred = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "model": f"Exponential Smoothing (α={alpha})",
            "predictions": sorted_pred,
            "top_5": list(sorted_pred.keys())[:5],
            "top_10": list(sorted_pred.keys())[:10],
            "confidence": "Very Low - No predictive power in random draws"
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
        normalized = {k: v/total*5 for k, v in ensemble.items()}
        sorted_ens = dict(sorted(normalized.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "model": "Ensemble (Bayesian 50% + Markov 25% + ExpSmoothing 25%)",
            "predictions": sorted_ens,
            "top_5": list(sorted_ens.keys())[:5],
            "top_10": list(sorted_ens.keys())[:10],
            "component_weights": weights,
            "confidence": "Very Low - All components have no predictive validity"
        }
    
    def run_full_analysis(self) -> Dict:
        """Run complete statistical analysis."""
        logger.info("Running full statistical analysis...")
        
        self.load_data()
        
        # Descriptive statistics
        logger.info("Computing descriptive statistics...")
        self.results["descriptive"] = {
            "number_frequencies": self.analyze_number_frequencies(self.baloto_df),
            "superbalota_frequencies": self.analyze_superbalota_frequencies(self.baloto_df),
            "position_frequencies": self.analyze_position_frequencies(self.baloto_df),
            "sum_statistics": self.analyze_sum_statistics(self.baloto_df),
            "odd_even_balance": self.analyze_odd_even_balance(self.baloto_df),
            "high_low_balance": self.analyze_high_low_balance(self.baloto_df),
            "consecutive_numbers": self.analyze_consecutive_numbers(self.baloto_df),
            "number_gaps": self.analyze_number_gaps(self.baloto_df),
            "repeating_numbers": self.analyze_repeating_numbers(self.baloto_df),
            "jackpot_statistics": self.analyze_jackpot_statistics(self.baloto_df),
            "revancha_number_frequencies": self.analyze_number_frequencies(self.revancha_df),
            "revancha_superbalota_frequencies": self.analyze_superbalota_frequencies(self.revancha_df)
        }
        
        # Inferential statistics
        logger.info("Computing inferential statistics...")
        self.results["inferential"] = {
            "parametric": {
                "uniformity_test": self.test_uniformity(self.baloto_df),
                "independence_test": self.test_independence(self.baloto_df),
                "hot_cold_significance": self.test_hot_cold_significance(self.baloto_df),
                "confidence_intervals": self.calculate_confidence_intervals(self.baloto_df),
                "normality_shapiro": self.test_normality_shapiro(self.baloto_df),
                "normality_anderson": self.test_anderson_darling(self.baloto_df)
            },
            "non_parametric": {
                "mann_whitney_odd_even": self.test_mann_whitney_odd_even(self.baloto_df),
                "kruskal_wallis_position": self.test_kruskal_wallis_position(self.baloto_df),
                "friedman_consecutive": self.test_friedman_consecutive(self.baloto_df),
                "wilcoxon_signed_rank": self.test_wilcoxon_signed_rank_pairs(self.baloto_df)
            }
        }
        
        # Predictive modeling
        logger.info("Generating predictive models...")
        self.results["predictive_modeling"] = {
            "bayesian": self.predict_next_draw_probabilities(self.baloto_df),
            "bayesian_superbalota": self.predict_superbalota_probabilities(self.baloto_df),
            "markov_chain": self.markov_chain_predictions(self.baloto_df),
            "regression_trends": self.regression_trend_analysis(self.baloto_df),
            "exponential_smoothing": self.exponential_smoothing_forecast(self.baloto_df),
            "ensemble": self.ensemble_prediction(self.baloto_df)
        }
        
        # Predictions (legacy format for frontend compatibility)
        logger.info("Generating predictions...")
        self.results["predictions"] = {
            "next_draw_numbers": self.predict_next_draw_probabilities(self.baloto_df),
            "next_superbalota": self.predict_superbalota_probabilities(self.baloto_df)
        }
        
        # Metadata
        self.results["metadata"] = {
            "analysis_date": datetime.now().isoformat(),
            "data_source": self.metadata,
            "total_draws_analyzed": len(self.baloto_df),
            "disclaimer": "Lottery draws are independent random events. Past performance does not predict future results. This analysis is for entertainment and educational purposes only."
        }
        
        # Save results
        output_path = self.data_dir / "analysis_results.json"
        with open(output_path, "w") as f:
            json.dump(_sanitize_json(convert_to_serializable(self.results)), f, indent=2, allow_nan=False)
        
        logger.info(f"Analysis complete! Results saved to {output_path}")
        return self.results

if __name__ == "__main__":
    analyzer = BalotoAnalyzer()
    analyzer.run_full_analysis()