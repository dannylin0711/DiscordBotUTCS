import json
f = open("topax.txt",'r',encoding="utf-8")
topax = f.readlines()
tempjsonbase = []

for idx,line in enumerate(topax):
    tempjson = {}
    tempjson["id"] = idx+1
    tempjson["text"] = line.strip()
    tempjsonbase.append(tempjson)
tempjsonre = {}
tempjsonre['data'] = tempjsonbase
t = open("topax.json",'w',encoding="utf-8")
t.write(json.dumps(tempjsonre,ensure_ascii=False,indent=4))
print(tempjsonre)