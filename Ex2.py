import random

# 1~1000 까지 100 개 랜덤 숫자 생성 

nums = [random.randint(1,100) for _ in range(1000)]
print("정렬전:", nums[:100])

def quick_sort_rec(arr):
    if len(arr) <= 1:
        return arr
    
    i = len(arr) // 2
    pivoit = arr[i] # //는 몫 연산자. 정수부만 남아요. 
    left = [x for x in arr if x < pivoit]   # 피벗보다 작은 요소들
    middle = [x for x in arr if x == pivoit] # 피벗과 같은 요소들
    right = [x for x in arr if x > pivoit] #피벗 보다 큰 요소들 
    
    return quick_sort_rec(left) + middle + quick_sort_rec(right)

#퀵 소트를 한번 해 볼까? 

sorted_nums = quick_sort_rec(nums)
print("정렬후:", sorted_nums[:1000])


    