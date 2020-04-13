listB = ["s0001","s0002","s0003","s0004","s0005"]
listA = ["蒙其·D·魯夫","羅羅亞·索隆","娜美","騙人布","多尼多尼·喬巴"]




a = input()
printFlag = True
for i in range(len(listB)):
    if a == listB[i]:
        printFlag = False
        print(listA[i])
if(printFlag):
    print("Not Found")
  





flag = True
printFlag = False
key = int(len(listB)/2)
while(flag):
    if a == listB[key]:
        flag = False
        print(listA[key])
    elif key >= len(listB):
        printFlag = True
        break
    elif key <= 0:
        printFlag = True
        break
    elif a > listB[key]:
        key = int((key + len(listB))/2)
    elif a < listB[key]:
        key = int((key)/2)

if(printFlag):
    print("Not Found")

        