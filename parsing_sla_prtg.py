import requests
from pymongo import MongoClient
from bson import json_util
import datetime
import json
import xmltodict
from xml.etree import ElementTree
from pprint import pprint
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = MongoClient()
db = client.dashboard
today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
lastMonth = lastMonth.replace(day=1)
last2Month = lastMonth - datetime.timedelta(days=1)
last2Month = last2Month.replace(day=1)
last3Month = last2Month - datetime.timedelta(days=1)
last3Month = last3Month.replace(day=1)
url = 'http://localhost:5000/api/v1/5c3852c93b86ef351c82bbbe/status'
response = requests.get(url, verify=False)
raw_data = json.loads(response.text)
for i in range(6, 13):
    info = {}
    content = []
    filename = 'tb_sla_sensor_{}_2018_6'.format(i)
    col = db[filename]
    for key in raw_data:
        try:
            sensorID = key['sensorID']
            ip = key['prtgsite']
            if i < 12:
                param = '&sdate=2018-{}-01-00-00-00&edate=2018-{}-01-00-00-00&avg=0&username=prtguser&password=Bp3t1OK!'.format(str(i).zfill(2), str(i+1).zfill(2))
            elif i == 12:
                param = '&sdate=2018-{}-01-00-00-00&edate=2019-01-01-00-00-00&avg=0&username=prtguser&password=Bp3t1OK!'.format(
                    str(i))
            url_summary = 'https://{}/api/historicdata_totals.xml?id={}{}'.format(ip, str(sensorID), param)
            url_dashboard = 'http://182.23.61.67/api/getdatabase/{}/2018/old/sensor/{}/6'.format(str(i), str(sensorID))
            print(url_summary)
            res = requests.get(url_summary, verify=False)
            res_tree = ElementTree.fromstring(res.content)
            tree = ElementTree.tostring(res_tree, encoding='utf8').decode('utf8')
            data = json.dumps(xmltodict.parse(tree))
            data = json.loads(data)
            res1 = requests.post(url=url_dashboard)
            dash = json_util.loads(res1.text)
            pprint(dash)
            sla_prtg = 0
            if dash[0]['snmpUptime'] is not None:
                average_sla = dash[0]['snmpUptime']
            #     if len(raw_data) > 1:
            #         average_sla = float(sum(d['sla'] for d in raw_data) / len(raw_data))
            #     else:
            #         average_sla = raw_data[0]['sla']
            #     average_sla = round(average_sla, 2)
            else:
                 average_sla = 0
            if data is not None:
                sla_prtg = data['historicdata']['uptimepercent'].replace(",", ".")
                sla_prtg = float(sla_prtg.split(" %")[0])
            info.update({"sensorID": sensorID, "sla_itb": average_sla, "sla_prtg": sla_prtg, "bulan": i})
            print(info)
            content.append(info)
            info = {}
        except (KeyError, ValueError):
            sla_prtg = None
            average_sla = None
            pass
    pprint(content)
    print("testing")
    insert = col.insert_many(content)

