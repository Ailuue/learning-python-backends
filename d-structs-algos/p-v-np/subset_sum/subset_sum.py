def subset_sum(nums, target):
    return find_subset_sum(nums, target, 0)


def find_subset_sum(nums, target, index):
    if target == 0:
        return True
    if index >= len(nums):
        return False
    if nums[index] > target:
        return find_subset_sum(nums, target, index + 1)
    return find_subset_sum(nums, target - nums[index], index + 1) or find_subset_sum(nums, target, index + 1)
