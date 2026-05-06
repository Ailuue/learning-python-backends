def binary_search(target: int, arr: list) -> bool:
    low = 0
    high = len(arr)-1
    while low <= high:
        median = (low + high) // 2
        if arr[median] == target:
            return True
        elif arr[median] < target:
            low = median + 1
        else:
            high = median-1
    return False