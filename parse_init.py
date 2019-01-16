import requests
from pymongo import MongoClient
from bson import json_util
import datetime

today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)
#print(lastMonth.strftime('%Y_%m'))
filename = "tb_traffic_" + lastMonth.strftime('%Y_%m')
#filename = "tb_traffic_2018_11"
client = MongoClient()
db = client.dashboard
col = db[filename]
users = db.users
cursor = users.find({})
for x in cursor:
    objectid = str(x['_id'])
    url = "http://122.248.39.155:5000/api/v1/" + objectid + "/upgrade"
    response = requests.get(url)
    data = json_util.loads(response.text)
    print(data)
    data = {}
    # insert = col.insert_many(data)




