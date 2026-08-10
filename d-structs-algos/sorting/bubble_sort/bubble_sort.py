def bubble_sort(nums: list[int]) -> list[int]:
    swapping = True
    end = len(nums)
    while swapping:
        swapping = False
        for i in range(1, end):
            if nums[i-1] > nums[i]:
                higher = nums[i-1]
                nums[i-1] = nums[i]
                nums[i] = higher
                swapping = True
        end -= 1
    return nums