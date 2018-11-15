
# -*- coding: utf-8 -*-
from functools import reduce

def str2float(s):
    DIGITS = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}
    if s.count('.') == 1: 
        left = s.split('.')[0]  
        right=s.split('.')[1] 
        reright=right[::-1] 
        def fn1(x,y):
            return x*10+y
        def fn2(x,y):
            return x/10+y
        def char2num(s):
            return DIGITS[s]
        return reduce(fn1, map(char2num,left))+reduce(fn2, map(char2num,reright))/10

print('str2float(\'123.456\') =', str2float('123.456'))
if abs(str2float('123.456') - 123.456) < 0.00001:
    print('测试成功!')
else:
    print('测试失败!')