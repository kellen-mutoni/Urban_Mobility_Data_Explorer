"""
Custom Algorithm for NYC Taxi Data Explorer
--------------------------------------------
Implements a linear top-k selection without using built-in sort functions.

Used in /api/top-expensive to return the k highest-fare trips.
"""


def top_k_fares(trips, k=10):
    """
    Linear Top-K Selection
    -----------------------
    Finds the k most expensive trips by scanning the list once per result slot.

    How it works:
    1. Start with an empty result list
    2. For each of the k slots, scan all remaining trips and pick the highest fare
    3. Remove the picked trip so it is not selected again
    4. Repeat until k trips are collected

    Time Complexity:  O(n * k)  — n trips scanned for each of the k slots
    Space Complexity: O(n + k)  — copy of trips list + result list
    """
    remaining = list(trips)
    result = []

    for _ in range(min(k, len(remaining))):
        max_idx = 0
        for i in range(1, len(remaining)):
            if remaining[i]["fare_amount"] > remaining[max_idx]["fare_amount"]:
                max_idx = i
        result.append(remaining[max_idx])
        remaining.pop(max_idx)

    return result
