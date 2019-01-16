import requests
from pymongo import MongoClient
from bson import json_util
import datetime
import json

today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)

client = MongoClient()
db=client.dashboard

url = "http://182.23.61.67/api/getdatabase/"
info = {}
content = []
array = []
for data in range(1,12):
    filename = "tb_sla_" + str(data) + '_' + lastMonth.strftime('%Y')
    col = db[filename]
    for i in range(1,13):
        try:
            params = str(i) + '/' + lastMonth.strftime('%Y') + '/old/' + str(data)
            url_dashboard = url + params
            response = requests.post(url=url_dashboard)
            raw_data = json_util.loads(response.text)
            snmp = 0
            for d in raw_data:
                if d['snmp_before'] != 0:
                    array.extend([d['snmp_before'], d['snmp_after']])
                else:
                    array.append(d['snmp'])
            average_sla = sum(array)/len(array)
            average_sla = round(average_sla,2)
            info.update({'isp': data, 'bulan': i, 'sla': average_sla})
            content.append(info)
            info = {}
            snmp = 0
        except:
            info.update({'isp': data, 'bulan': i, 'sla': None})
            content.append(info)
            info = {}
    print(content)
    # try:
    #     x = col.insert_many(content)
    # except:
    #     pass
    content = []
