import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportions_ztest, proportion_effectsize

np.random.seed(42)

# ---------- 1. DESIGN: how many samples do we need? ----------
###############################################################

baseline_rate = 0.10        # control conversion rate (10%)
# right now: 10 out of 100 convert
mde = 0.02                  # minimum effect worth detecting (+2 points -> 12%)
# smallest improvement you'd bother shipping: +2 points → 12%
alpha = 0.05               # significance level (5% false-positive risk) 
# I'll tolerate making this mistake 5% of the time.
power = 0.80               # 80% chance of detecting a real effect
# When it really works, I want to catch it 80% of the time

effect = proportion_effectsize(baseline_rate + mde, baseline_rate)
# turns "10% vs 12%" into a standardized "gap size"

n_needed = NormalIndPower().solve_power(effect_size=effect, alpha=alpha, power=power, alternative='larger')
# This function will help to solve for the sample size needed to detect that gap with the desired power and significance level.
n_per_group = int(np.ceil(n_needed))

print(f"Samples needed per group: {n_per_group}")




# ---------- 2. SIMULATE the experiment ----------
##################################################

true_control = 0.10 # version A users convert 10% of the time
true_treatment = 0.12 # treatment truly better  # version B users convert 12% of the time — B is genuinely better

control = np.random.binomial(1, true_control, n_per_group)
# will generate a random sample of 0s and 1s, where 1 represents a conversion, for the control group, i.e. 10% would be 1.
treatment = np.random.binomial(1, true_treatment, n_per_group)
# will generate a random sample of 0s and 1s, where 1 represents a conversion, for the treatment group, i.e. 12% would be 1.




# ---------- 3. ANALYZE: is the difference significant? ----------
##################################################################

# Here the purpose is whether the gap between the two groups is real or just luck.
# how many converted and how many total
conv = np.array([control.sum(), treatment.sum()])
obs = np.array([n_per_group, n_per_group])

# This is the significant test
zstat, pval = proportions_ztest(conv, obs, alternative='smaller')
# It will show "is this gap bigger than luck would normally produce?"
# It will return a z-statistic and a p-value. 
# The p-value is the probability of seeing a gap this big (or bigger) if the two groups were actually the same.
# if there was luck or there were no real effect, there is only 2.76% chance that the gap would be this big. 


#  Computing the conversion rates and the relative lift
c_rate, t_rate = control.mean(), treatment.mean()
lift = (t_rate - c_rate) / c_rate
# lift will say treatment is 15.4% better than control

# Build the confidence interval
# 95% confidence interval on the difference
se = np.sqrt(c_rate*(1-c_rate)/n_per_group + t_rate*(1-t_rate)/n_per_group)
# Standard error of the difference between two proportions, how much gap would wobble around if we repeated the experiment many times.
diff = t_rate - c_rate
ci_low, ci_high = diff - 1.96*se, diff + 1.96*se

print(f"Control: {c_rate:.3f}  Treatment: {t_rate:.3f}")
print(f"Relative lift: {lift:.1%}")
print(f"p-value: {pval:.4f}")
print(f"95% CI on difference: [{ci_low:.3f}, {ci_high:.3f}]")

# The decision
print("Decision:", "SHIP" if pval < alpha else "DO NOT SHIP")

# with CI
# Zero gap = B and A convert at the same rate = the change did nothing.
# That interval excludes zero, so "B is no better" is not on the board