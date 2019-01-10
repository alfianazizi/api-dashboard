import requests
from pymongo import MongoClient
from bson import json_util
import datetime
import json

today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)
filename = "tb_sla_7_" + lastMonth.strftime('%Y')

client = MongoClient()
db=client.dashboard
col=db[filename]

url = "http://182.23.61.67/api/getdatabase/"
info = {}
content = []
for i in range(13):
    print(i)
    try:
        params = str(i) + '/' + lastMonth.strftime('%Y') + '/old/7'
        url_dashboard = url + params
        response = requests.post(url=url_dashboard)
        raw_data = json_util.loads(response.text)
        average_sla = float(sum(d['snmp'] for d in raw_data) / len(raw_data))
        average_sla = round(average_sla,2)
        info.update({'bulan': i, 'sla': average_sla})
        try:
            x = col.insert_one(info)
        except:
            pass
        content.append(info)
        info = {}
    except:
        pass

print(content)