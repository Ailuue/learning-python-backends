import math

def merge_sort(nums: list[int]) -> list[int]:
    if len(nums) < 2:
        return nums
    arr1 = nums[0:math.floor(len(nums)/2)]
    arr2 = nums[math.floor(len(nums)/2):]
    sorted_left = merge_sort(arr1)
    sorted_right = merge_sort(arr2)
    return merge(sorted_left, sorted_right)


def merge(first: list[int], second: list[int]) -> list[int]:
    merged = []
    i = j = 0
    while (i < len(first) and j < len(second)):
        if first[i] <= second[j]:
            merged.append(first[i])
            i += 1
        else:
            merged.append(second[j])
            j += 1   
    if i < len(first):
        merged = merged + first[i:]
    if j < len(second):
        merged = merged + second[j:]
    return merged