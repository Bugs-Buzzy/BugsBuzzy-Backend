"""
Test overall distribution assuming realistic player performance spread
"""

import numpy as np
from collections import Counter


def calculate_discount_percentage(carrot_count: int, coin_count: int) -> int:
    """Same function as in views.py"""
    if carrot_count == 0 and coin_count == 0:
        return 10

    carrot_normalized = min(carrot_count / 200, 1.0)
    coin_normalized = min(coin_count / 15, 1.0)

    performance = carrot_normalized * 0.4 + coin_normalized * 0.6

    base_mean = 20 + (performance * 10)

    alpha = 3.0 + (performance * 1.5)
    beta = 8.0 - (performance * 2.5)

    random_factor = np.random.beta(alpha, beta)

    discount = base_mean + (random_factor * 10)

    discount = max(10, min(40, int(discount)))

    return discount


def simulate_realistic_gameplay(num_players=10000):
    """
    Simulate realistic player performance distribution:
    - Most players will get average scores
    - Few will get very high scores
    - Some will get low scores
    """
    results = []

    for _ in range(num_players):
        # Simulate realistic score distribution
        # Using normal distribution centered around average performance
        carrot_mean = 100
        carrot_std = 50
        coin_mean = 7
        coin_std = 3

        carrot = max(0, min(200, int(np.random.normal(carrot_mean, carrot_std))))
        coin = max(0, min(15, int(np.random.normal(coin_mean, coin_std))))

        discount = calculate_discount_percentage(carrot, coin)
        results.append(discount)

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("REALISTIC OVERALL DISTRIBUTION SIMULATION")
    print("=" * 60)
    print("Simulating 10,000 players with realistic score distribution")
    print("Carrot: mean=100, std=50 (capped 0-200)")
    print("Coin: mean=7, std=3 (capped 0-15)")
    print("=" * 60)

    results = simulate_realistic_gameplay()

    counter = Counter(results)

    below_30 = sum(1 for r in results if r < 30)
    below_35 = sum(1 for r in results if r <= 35)
    above_35 = sum(1 for r in results if r > 35)

    print(f"\nTotal players: {len(results)}")
    print(f"Min: {min(results)}%, Max: {max(results)}%, Mean: {np.mean(results):.1f}%")
    print(f"\n{'='*60}")
    print("OVERALL DISTRIBUTION RESULTS")
    print(f"{'='*60}")
    print(
        f"< 30%:  {below_30/len(results)*100:.1f}% (target: ~70%) {'✓' if below_30/len(results)*100 >= 65 else '✗'}"
    )
    print(
        f"<= 35%: {below_35/len(results)*100:.1f}% (target: ~95%) {'✓' if below_35/len(results)*100 >= 93 else '✗'}"
    )
    print(
        f"> 35%:  {above_35/len(results)*100:.1f}% (target: ~5%) {'✓' if above_35/len(results)*100 <= 7 else '✗'}"
    )

    print(f"\n{'='*60}")
    print("DETAILED BREAKDOWN")
    print(f"{'='*60}")
    for discount in sorted(counter.keys()):
        percentage = counter[discount] / len(results) * 100
        bar = "█" * int(percentage / 2)
        print(f"{discount:2d}%: {bar} {percentage:.1f}%")

    print(f"\n{'='*60}")
    print("VERDICT")
    print(f"{'='*60}")
    meets_requirements = (
        below_30 / len(results) * 100 >= 65
        and below_35 / len(results) * 100 >= 93
        and above_35 / len(results) * 100 <= 7
    )

    if meets_requirements:
        print("✓ Distribution meets all requirements!")
    else:
        print("✗ Distribution does NOT meet requirements")
