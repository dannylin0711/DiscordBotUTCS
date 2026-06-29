import json

import requests

download_path = './cogs/asset/img/mygo/'

base_url = 'https://drive.miyago9267.com/d/file/img/mygo/'
with open('./cogs/asset/image_map.json') as json_file:
    js = json.loads(json_file.read())
    
    for key in js:
        download_url = base_url + key["file_name"]
        print(download_url)
        req = requests.get(download_url)
        with open(download_path + key["file_name"], 'wb') as f:
            f.write(req.content)
            
            
        
        