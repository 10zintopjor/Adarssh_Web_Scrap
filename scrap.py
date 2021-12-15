import requests
import json
from bs4 import BeautifulSoup
li=[]

def call_api():
    url = "https://adarsha.dharma-treasure.org/kdbs/degekangyur"

    r = requests.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    results = soup.find("script", {"data-reactid": "23"}).text.strip()[14:-1]

    results = json.loads(results)["sidebar"]["data"]

    with open("s.json","w") as f:
        f.write(json.dumps(results))

def get_leaf_value(results,pbid):
    val = None
    global li
    for n,result in enumerate(results):
        if "nodes" in result:
            val = get_leaf_value(result["nodes"],pbid)
            if val != None:
                li.append(result["text"])
                return val
        elif n<len(results)-1:
            if pbid >= result["PbId"] and pbid < results[n+1]["PbId"]:
                li.append(result["text"])
                return result["text"]
        elif n == len(results)-1:
            if pbid == result["PbId"]:
                li.append(result["text"])
                return result["text"]
        
    return val

def load_json():
    with open("s.json") as f:
        data = json.load(f)
    return data

def start_work(pbid):
    li.clear
    results = call_api()
    data = load_json()
    val = get_leaf_value(data,pbid)
    print(li)

if __name__ == "__main__":
    start_work(2977845)
   