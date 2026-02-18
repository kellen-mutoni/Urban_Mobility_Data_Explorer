"""
Custom Sorting Algorithms for NYC Taxi Data Explorer
-----------------------------------------------------
Implements bucket sort and insertion sort without using built-in sort functions.

Used for ordering fare distribution buckets and sorting search results.
"""


def custom_bucket_sort(data, key_func, num_buckets=10):
    """
    Custom Bucket Sort Implementation
    ----------------------------------
    Sorts a list of dictionaries by a numeric key using bucket sort.

    How it works:
    1. Find the min and max values
    2. Create 'num_buckets' empty buckets
    3. Distribute items into buckets based on their value range
    4. Sort each bucket using insertion sort (also custom, no built-in)
    5. Concatenate all buckets

    Time Complexity: O(n + k) average case, O(n^2) worst case
    Space Complexity: O(n + k) where k = number of buckets


    """
    if not data:
        return []

    # Find min and max
    min_val = key_func(data[0])
    max_val = key_func(data[0])
    for item in data:
        val = key_func(item)
        if val < min_val:
            min_val = val
        if val > max_val:
            max_val = val

    # Edge case: all values are the same
    if min_val == max_val:
        return data

    # Create buckets
    bucket_range = (max_val - min_val + 0.001) / num_buckets
    buckets = []
    for i in range(num_buckets):
        buckets.append([])

    # Distribute into buckets
    for item in data:
        val = key_func(item)
        index = int((val - min_val) / bucket_range)
        if index >= num_buckets:
            index = num_buckets - 1
        buckets[index].append(item)

    # Sort each bucket using insertion sort (custom, no built-in)
    for bucket in buckets:
        custom_insertion_sort(bucket, key_func)

    # Concatenate
    result = []
    for bucket in buckets:
        for item in bucket:
            result.append(item)

    return result
