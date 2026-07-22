# A/B Testing Project
A small, self-contained A/B test in Python to learn the experiment workflow end-to-end: Design → Simulate → Analyze. The script generates its own data, so no external dataset is needed.

# What an A/B test actually is
> You have a version A (the "control" — what exists today) and a version B (the "treatment" — a change you're considering, say a new checkout button). You split users randomly: half see A, half see B. You measure who converts (buys, signs up, clicks — whatever counts as success). Then you ask one question: is B actually better, or did it just look better by luck?

# What we need to perform test - Three steps, which is the standard shape of any real A/B test:

1. Design — decide how many users you need before you start (the section I just walked through).

2. Simulate — generate fake users so you have data to practice on (a real test would collect this from live traffic instead).

3. Analyze — run the stats, get a verdict: ship the change or don't.

# What we get
'''
\bash
Sample size / power — why you size a test before running it
What a p-value is (and, more importantly, what it is not)
What a confidence interval tells you
Why you'd decide to ship or not ship
'''

# Section - 1
##  Design — how many users do we need?

**Purpose:** Decide the size of the test *before* running it, so it's neither too small to trust nor wastefully large.

**Why it matters:** Too few users and you'll either miss a real improvement or get fooled by noise. This step computes the required sample size up front to prevent that.

**The four design inputs:**

| Input | Value | Meaning |
|-------|-------|---------|
| `baseline_rate` | 0.10 | Current conversion rate (10 of every 100 convert) |
| `mde` | 0.02 | Minimum lift worth shipping (+2 points, i.e. 10% → 12%) |
| `alpha` | 0.05 | Tolerance for a **false positive** — calling a useless change a winner (5%) |
| `power` | 0.80 | Chance of **catching a real effect** when it exists (80%); we miss it the other 20% |

**Two errors, two dials:**

- `alpha` guards against shipping a dud (false alarm).
- `power` guards against missing a genuine winner (blindness).
- You can't set both errors to zero — shrinking both requires more users. Your tolerance for being wrong determines the sample size.

**How it's computed:**

- `proportion_effectsize(0.12, 0.10)` translates the two conversion rates into a standardized "effect size" (Cohen's h) — a difficulty score the sample-size formula understands. The same 2-point gap is harder to detect near 50% than near 10%, so raw percentages aren't enough.
- `NormalIndPower().solve_power(...)` uses that effect size plus the error tolerances to solve for the required sample size.

**Result:** **3,021 users per group** (~6,000 total).

**Key takeaway:** Smaller effects need much bigger tests — halving the effect you want to detect roughly quadruples the sample size. "How small an effect do I care about vs. how much traffic do I have" is the entire design trade-off.


## Section 2: Simulate — making fake users to practice on

**Purpose:** Manufacture the test data. In a real experiment this comes from live traffic; here we generate it, so the project needs no external dataset.

**The setup — we secretly decide the truth:**

```python
true_control   = 0.10   # version A converts 10% of the time
true_treatment = 0.12   # version B is genuinely better, by 2 points
```

Setting `true_treatment = 0.12` serves two purposes:

1. **Mechanical necessity** — the data generator needs a conversion weight to produce fake users. No number, no data.
2. **Grading the method** — because *we* plant the truth ("B really is 2 points better"), Section 3 can be checked: did the statistics actually detect the effect we hid? Like hiding an object, then testing whether a metal detector finds it.

**Generating the users:**

```python
control   = np.random.binomial(1, 0.10, 3021)
treatment = np.random.binomial(1, 0.12, 3021)
```

`np.random.binomial(1, p, n)` = "flip a weighted coin n times." Each user is one flip: `1` = converted, `0` = didn't. The weight `p` sets how often the coin lands on "converted."

**Subtle point:** the observed rates won't exactly equal the true rates — random luck blurs them. We set 0.10 / 0.12 but the data came out 0.099 / 0.114. That gap between "the truth we planted" and "what the data shows" is exactly what the analysis step must see through.

**Key takeaway:** Fabricate two groups of users as coin flips, with B secretly better, so there's data to analyze and a way to grade whether the method catches the planted difference.

> Note: In a real A/B test you never set the true rate — it's the unknown you're trying to uncover. Setting it here is only possible because this is a simulation.



If it were pure luck, a gap this big would appear 2.76% of the time" → probability about the data, given luck with p = 0.0276 and a high Ztest score


## Section 3: Analyze — is the difference real?

**Purpose:** Take the raw data and produce a verdict: ship the change or not. Flow: **count → test → describe → quantify uncertainty → decide.**

### Step 1: Count the successes

```python
conv = np.array([control.sum(), treatment.sum()])   # [299, 345]
obs  = np.array([n_per_group, n_per_group])          # [3021, 3021]
```

Boil each group down to conversions vs. total: 299/3021 (control) vs. 345/3021 (treatment).

### Step 2: The z-test and p-value

```python
zstat, pval = proportions_ztest(conv, obs, alternative='smaller')   # p = 0.0276
```

The **z-test** measures the observed gap in units of "normal random jitter" (standard error). The **z-score** is how many jitters from zero the gap sits; a bigger z maps to a smaller p-value. The bar for "significant" at alpha = 0.05 is |z| ≥ 1.96.

**Reading the p-value correctly:** *"If there were no real difference, a gap this big would appear only 2.76% of the time by chance."*

Common trap — p = 0.0276 does **NOT** mean:
- ❌ "97% chance the treatment works"
- ❌ "2.76% chance the result is a fluke"
- ✅ "If no real effect existed, data this extreme would show up 2.76% of the time"

The p-value measures how surprising the data is *assuming no effect* — it never gives the probability that the hypothesis is true. (`alternative='smaller'` = one-sided test: "is treatment better?", not "is it different either way?")

### Step 3: Describe in plain numbers

```python
c_rate, t_rate = control.mean(), treatment.mean()   # 0.099, 0.114
lift = (t_rate - c_rate) / c_rate                    # 15.4%
```

`.mean()` of 0s and 1s = the conversion rate. **Lift** is the *relative* improvement (15.4%), vs. the *absolute* gap of ~1.5 points. Distinguishing absolute (+1.5 pts) from relative (+15%) matters — the relative number looks big only because the base is small.

### Step 4: Confidence interval

```python
se = np.sqrt(c_rate*(1-c_rate)/n_per_group + t_rate*(1-t_rate)/n_per_group)
diff = t_rate - c_rate                               # 0.015
ci_low, ci_high = diff - 1.96*se, diff + 1.96*se     # [-0.000, 0.031]
```

The CI is the plausible range for the *true* gap: about −0.03 to +3.1 points. **It includes zero (barely)**, so "the change did nothing" is still a plausible truth.

- Interval **includes zero** → can't rule out "no effect" → hesitate.
- Interval **sits fully above zero** → even the worst case is an improvement → confident ship.

### Step 5: The decision

```python
print("Decision:", "SHIP" if pval < alpha else "DO NOT SHIP")   # SHIP
```

Mechanically, p (0.0276) < alpha (0.05) → prints SHIP. But this is a **borderline** result: significant p, yet the CI grazes zero and z is near the 1.96 threshold. The real call is a business judgment — cheap/low-risk change: ship; expensive/risky: gather more data first.

> Why p-value and CI seem to disagree: the p-value here is *one-sided* ("is B better?") while the CI is *two-sided* ("how different, either direction?"). Different questions, so in borderline cases they can land on opposite sides of the line.

## Results (seed = 42)

| Metric | Value |
|--------|-------|
| Samples needed per group | 3,021 |
| Control conversion | 0.099 |
| Treatment conversion | 0.114 |
| Relative lift | 15.4% |
| p-value | 0.0276 |
| 95% CI on difference | [−0.000, 0.031] |
| Decision | SHIP (borderline) |

## Four things I can now explain

1. **Sample size / power** — why you size a test *before* running it, and the two errors (false positive via alpha, false negative via power) that drive the number.
2. **The p-value** — a measure of how surprising the data is *if there were no effect*, not the probability the hypothesis is true.
3. **The confidence interval** — the plausible range for the true effect; whether it includes zero is what decides confidence.
4. **Ship or not** — a business judgment, not a blind `p < 0.05`; a borderline CI means the evidence is thin.

## Possible extensions

- **Peeking:** check for significance repeatedly as data arrives (with no real effect) and watch the false-positive rate climb past 5% — shows why you don't stop a test early.
- **Empirical power:** rerun the whole experiment ~1,000 times with a real effect and confirm you catch it ~80% of the time — makes "80% power" concrete.

## How to run

```bash
pip install numpy pandas scipy statsmodels
python ab_test.py
```

No data required — the script simulates its own. Runs in seconds.