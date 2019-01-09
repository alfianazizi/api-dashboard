import requests
from pymongo import MongoClient
from bson import json_util
import datetime

today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)
last2Month = lastMonth - datetime.timedelta(days=1)
last2Month = last2Month.replace(day=1)
last3Month = last2Month - datetime.timedelta(days=1)
last3Month = last3Month.replace(day=1)
print(last3Month.strftime('%Y_%m'))
filename = "tb_traffic_" + last3Month.strftime('%Y_%m')

client = MongoClient()
db=client.dashboard
col=db[filename]

url = "http://122.248.39.155:5000/api/v1/upgrade"
response = requests.get(url)
data = json_util.loads(response.text)

x = col.insert_many(data)
