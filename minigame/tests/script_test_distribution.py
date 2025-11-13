"""
Test script to verify discount distribution meets requirements:
- ~70% chance: discount < 30%
- ~95% chance: discount <= 35%
- 100% chance: discount <= 40% (hard cap)
"""

import numpy as np
from collections import Counter


def calculate_discount_percentage(carrot_count: int, coin_count: int) -> int:
    """Same function as in views.py"""
    if carrot_count == 0 and coin_count == 0:
        return 10
    
    carrot_normalized = min(carrot_count / 200, 1.0)
    coin_normalized = min(coin_count / 15, 1.0)
    
    performance = (carrot_normalized * 0.4 + coin_normalized * 0.6)
    
    base_mean = 20 + (performance * 10)
    
    alpha = 3.0 + (performance * 1.5)
    beta = 8.0 - (performance * 2.5)
    
    random_factor = np.random.beta(alpha, beta)
    
    discount = base_mean + (random_factor * 10)
    
    discount = max(10, min(40, int(discount)))
    
    return discount


def test_distribution(carrot_count, coin_count, num_samples=10000):
    """Test the distribution for given carrot and coin counts"""
    results = [calculate_discount_percentage(carrot_count, coin_count) for _ in range(num_samples)]
    
    counter = Counter(results)
    
    below_30 = sum(1 for r in results if r < 30)
    below_35 = sum(1 for r in results if r <= 35)
    below_40 = sum(1 for r in results if r <= 40)
    above_35 = sum(1 for r in results if r > 35)
    
    print(f"\n{'='*60}")
    print(f"Testing with carrot={carrot_count}, coin={coin_count}")
    print(f"{'='*60}")
    print(f"Total samples: {num_samples}")
    print(f"Min: {min(results)}%, Max: {max(results)}%, Mean: {np.mean(results):.1f}%")
    print(f"\nDistribution:")
    print(f"  < 30%:  {below_30/num_samples*100:.1f}% (target: ~70%)")
    print(f"  <= 35%: {below_35/num_samples*100:.1f}% (target: ~95%)")
    print(f"  > 35%:  {above_35/num_samples*100:.1f}% (target: ~5%)")
    print(f"  <= 40%: {below_40/num_samples*100:.1f}% (target: 100%)")
    
    print(f"\nDetailed breakdown:")
    for discount in sorted(counter.keys()):
        percentage = counter[discount] / num_samples * 100
        bar = '█' * int(percentage)
        print(f"  {discount:2d}%: {bar} {percentage:.1f}%")


if __name__ == "__main__":
    print("Testing Minigame Discount Distribution")
    print("="*60)
    
    # Test various scenarios
    scenarios = [
        (0, 0, "Worst performance"),
        (50, 3, "Poor performance"),
        (100, 7, "Average performance"),
        (150, 10, "Good performance"),
        (200, 15, "Excellent performance"),
    ]
    
    for carrot, coin, description in scenarios:
        print(f"\n\n{description.upper()}")
        test_distribution(carrot, coin)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("All scenarios should meet:")
    print("  ✓ ~70% of results < 30%")
    print("  ✓ ~95% of results <= 35%")
    print("  ✓ ~5% of results > 35%")
    print("  ✓ 100% of results <= 40%")
