import requests
from pymongo import MongoClient
from bson import json_util
import datetime

today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)
filename = "tb_traffic_" + lastMonth.strftime('%Y_%m')

client = MongoClient()
db=client.dashboard
col=db[filename]

url = "http://122.248.39.155:5000/api/v1/upgrade"
response = requests.get(url)
data = json_util.loads(response.text)

x = col.insert_many(data)