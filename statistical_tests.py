import math
from rng import SecureRNG


# --------------------------------------------------
# Sample generation
# --------------------------------------------------

def generate_samples(n_bytes: int):
    rng = SecureRNG.new()
    data = rng.next_bytes(n_bytes)
    return list(data)


# --------------------------------------------------
# 1) Chi-Square Test
# --------------------------------------------------

def chi_square_test(samples):
    n = len(samples)
    expected = n / 256
    freq = [0] * 256

    for x in samples:
        freq[x] += 1

    chi2 = 0.0
    for f in freq:
        chi2 += (f - expected) ** 2 / expected

    return chi2


# --------------------------------------------------
# 2) Runs Test (Wald–Wolfowitz)
# --------------------------------------------------

def runs_test(samples):
    bits = []
    for byte in samples:
        for i in range(8):
            bits.append((byte >> i) & 1)

    n1 = bits.count(1)
    n0 = bits.count(0)

    if n0 == 0 or n1 == 0:
        return 0.0

    runs = 1
    for i in range(1, len(bits)):
        if bits[i] != bits[i - 1]:
            runs += 1

    expected = (2 * n0 * n1) / (n0 + n1) + 1
    variance = (
        2 * n0 * n1 * (2 * n0 * n1 - n0 - n1)
        / (((n0 + n1) ** 2) * (n0 + n1 - 1))
    )

    z = (runs - expected) / math.sqrt(variance)
    return z


# --------------------------------------------------
# 3) Kolmogorov–Smirnov Test
# --------------------------------------------------

def kolmogorov_smirnov_test(samples):
    n = len(samples)
    normalized = sorted(x / 255 for x in samples)

    d_max = 0.0
    for i, x in enumerate(normalized, start=1):
        d_plus = abs(i / n - x)
        d_minus = abs(x - (i - 1) / n)
        d_max = max(d_max, d_plus, d_minus)

    return d_max


# --------------------------------------------------
# Main runner
# --------------------------------------------------

def main():
    N_BYTES = 200_000   # rapor için yeterli, istersen artırabilirsin

    print("🔬 SecureRNG Statistical Test Suite")
    print(f"Sample size: {N_BYTES} bytes\n")

    samples = generate_samples(N_BYTES)

    chi2 = chi_square_test(samples)
    runs_z = runs_test(samples)
    ks_d = kolmogorov_smirnov_test(samples)

    print("Chi-Square Test")
    print(f"  Chi² statistic : {chi2:.2f}")
    print("  df = 255 (uniformity not rejected if within expected range)\n")

    print("Runs Test (Wald–Wolfowitz)")
    print(f"  Z-score        : {runs_z:.3f}")
    print("  |Z| < 1.96  → independence not rejected (95%)\n")

    print("Kolmogorov–Smirnov Test")
    print(f"  D statistic    : {ks_d:.5f}")
    print(f"  Critical value : {1.36 / math.sqrt(N_BYTES):.5f}")
    print("  D < critical → uniformity not rejected\n")

    print("✅ Statistical tests completed.")


if __name__ == "__main__":
    main()
