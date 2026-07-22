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