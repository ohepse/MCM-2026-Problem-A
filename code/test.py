import math
e=math.e
print(e)
def func(N):
    return 93.5*e**(-16.13/23.5-195/(N+36.38))+35.38
for i in range(1,10001,1000):
    print(i,func(i),'\n')
