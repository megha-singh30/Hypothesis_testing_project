import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportions_ztest, proportion_effectsize

np.random.seed(42)

# ---------- 1. DESIGN: how many samples do we need? ----------
baseline_rate = 0.10        # control conversion rate (10%)
# right now: 10 out of 100 convert
mde = 0.02                  # minimum effect worth detecting (+2 points -> 12%)
# smallest improvement you'd bother shipping: +2 points → 12%
alpha = 0.05               # significance level (5% false-positive risk) 
# I'll tolerate making this mistake 5% of the time.
power = 0.80               # 80% chance of detecting a real effect
# When it really works, I want to catch it 80% of the time

effect = proportion_effectsize(baseline_rate + mde, baseline_rate)
n_needed = NormalIndPower().solve_power(effect_size=effect, alpha=alpha, power=power, alternative='larger')
n_per_group = int(np.ceil(n_needed))
print(f"Samples needed per group: {n_per_group}")

# ---------- 2. SIMULATE the experiment ----------
true_control = 0.10
true_treatment = 0.12       # treatment truly better
control = np.random.binomial(1, true_control, n_per_group)
treatment = np.random.binomial(1, true_treatment, n_per_group)

# ---------- 3. ANALYZE: is the difference significant? ----------
conv = np.array([control.sum(), treatment.sum()])
obs = np.array([n_per_group, n_per_group])
zstat, pval = proportions_ztest(conv, obs, alternative='smaller')

c_rate, t_rate = control.mean(), treatment.mean()
lift = (t_rate - c_rate) / c_rate

# 95% confidence interval on the difference
se = np.sqrt(c_rate*(1-c_rate)/n_per_group + t_rate*(1-t_rate)/n_per_group)
diff = t_rate - c_rate
ci_low, ci_high = diff - 1.96*se, diff + 1.96*se

print(f"Control: {c_rate:.3f}  Treatment: {t_rate:.3f}")
print(f"Relative lift: {lift:.1%}")
print(f"p-value: {pval:.4f}")
print(f"95% CI on difference: [{ci_low:.3f}, {ci_high:.3f}]")
print("Decision:", "SHIP" if pval < alpha else "DO NOT SHIP")