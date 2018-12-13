# app/__init__.py

from flask_api import FlaskAPI
from bson import json_util, ObjectId
import json
import requests
import calendar
import datetime
from time import sleep, strftime, time
from flask import jsonify, request
from flask_cors import CORS
from operator import itemgetter
from pymongo import MongoClient

# local import
from instance.config import app_config

client = MongoClient()
db=client.dashboard
collection = db.master
setting = db.settings

url_uptime1 = "https://202.43.73.155/api/table.json?content=sensors&columns=objid,device,sensor,lastvalue,status,message&sortby=lastvalue&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_uptime2 = "https://202.43.73.156/api/table.json?content=sensors&id=2487&columns=objid,device,sensor,lastvalue,status,message&sortby=-lastvalue&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_ping1 = "https://202.43.73.155/api/table.json?content=sensors&id=2477&columns=objid,sensor,lastvalue,status,message&sortby=lastvalue&filter_type=ping&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_ping2 = "https://202.43.73.156/api/table.json?content=sensors&id=2487&columns=objid,sensor,lastvalue,status,message&sortby=lastvalue&filter_type=ping&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_traffic1 = "https://202.43.73.155/api/table.json?content=sensors&columns=objid,sensor,lastvalue,status&sortby=-lastvalue&filter_type=snmptraffic&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_traffic2 = "https://202.43.73.156/api/table.json?content=sensors&columns=objid,sensor,lastvalue,status&sortby=-lastvalue&filter_type=snmptraffic&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_downtimesince1 = "https://202.43.73.155/api/table.json?content=sensors&columns=objid,sensor,lastvalue,status,message,downtimesince&sortby=downtimesince&filter_type=ping&username=prtguser&password=Bp3t1OK!&filter_status=5&filter_status=4&filter_status=10&filter_status=13&filter_status=14"
url_downtimesince2 = "https://202.43.73.156/api/table.json?content=sensors&columns=objid,sensor,lastvalue,status,message,downtimesince&sortby=downtimesince&filter_type=ping&username=prtguser&password=Bp3t1OK!&filter_status=5&filter_status=4&filter_status=10&filter_status=13&filter_status=14"
url_all1 = "https://202.43.73.155/api/table.json?content=sensors&id=2477&columns=objid,device,sensor,lastvalue,status,message,downtimesince&sortby=-lastvalue&filter_type=snmpuptime&filter_type=snmpcustom&username=prtguser&password=Bp3t1OK!"
url_all2 = "https://202.43.73.156/api/table.json?content=sensors&id=2487&columns=objid,device,sensor,lastvalue,status,message,downtimesince&sortby=-lastvalue&filter_type=snmpuptime&filter_type=snmpcustom&username=prtguser&password=Bp3t1OK!"
url_dashboard = "http://182.23.61.67/api/getdatabase/11/2018/old/7"

def create_app(config_name):
    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    CORS(app)

    def getAPIData(url1, url2):
      response1 = requests.get(url1, verify=False)
      response2 = requests.get(url2, verify=False)
      json_data1 = json.loads(response1.text)
      json_data2 = json.loads(response2.text)
      data = json_data1["sensors"] + json_data2["sensors"]

      return data

    def getAPIDashboard(x):
      r = requests.post(url=x)
      json_data = json.loads(r.text)

      return json_data


    @app.route("/api/v1/longuptime")
    def topUptime():
      global url_uptime1
      global url_uptime2
      uptime = getAPIData(url_uptime1, url_uptime2)
      for x in uptime:
         if x['lastvalue_raw'] == "":
            x['lastvalue_raw'] = 0
         x['lastvalue'] = x['lastvalue'].replace(' ', '')
      sorted_uptime = sorted(uptime, key=itemgetter('lastvalue_raw'), reverse=True)

      return jsonify(sorted_uptime[:10])

    @app.route("/api/v1/shortuptime")
    def topDowntime():
      global url_uptime1
      global url_uptime2
      downtime = getAPIData(url_uptime1, url_uptime2)
      for x in downtime:
         if x['lastvalue_raw'] == "":
            x['lastvalue_raw'] = 0
         x['lastvalue'] = x['lastvalue'].replace(' ', '')
      sorted_downtime = sorted(downtime, key=itemgetter('lastvalue_raw'))

      return jsonify(sorted_downtime[:10])

    @app.route("/api/v1/fastestping")
    def fastestPing():
      global url_ping1
      global url_ping2
      ping = getAPIData(url_ping1, url_ping2)
      sorted_ping = sorted(ping, key=itemgetter('lastvalue_raw'))
      return jsonify(sorted_ping[:10])

    @app.route("/api/v1/slowestping")
    def slowestPing():
      global url_ping1
      global url_ping2
      ping = getAPIData(url_ping1, url_ping2)
      sorted_ping = sorted(ping, key=itemgetter('lastvalue_raw'), reverse=True)

      return jsonify(sorted_ping[:10])

    @app.route("/api/v1/status")
    def statusSensor():
      global url_all1
      global url_all2
      global url_dashboard
      status_all = getAPIData(url_all1, url_all2)
      status_dashboard = getAPIDashboard(url_dashboard)
      info = {}
      content = []
      a = [{"id": str(d['objid']), "status": d['status']} for d in status_all if 'objid' and 'status' in d]
      b = [{"id": str(d['sensorPing']), "tagihan": d['tagihan'], "tagihan_new": d['tagihan_after'], "tagihan_old": d['tagihan_before'], \
      "sla": d['snmp'], "old_sla": d['snmp_before'], "new_sla": d['snmp_after'], "harga": d['harga'], "old_harga": d['old_harga'], \
      "new_harga": d['new_harga'], } for d in status_dashboard if 'sensorPing' and 'snmp' and 'tagihan' and 'tagihan_after' and 'tagihan_before' and \
      'snmp_before' and 'snmp_after' and 'harga' and 'old_harga' and 'new_harga' in d]
      for i in range(len(a)):
        x = collection.find_one({"sensorID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          for indx in b:
             if (indx['id'] == data['pingID']):
                data.update({'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla'], 'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new'], 'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']})
                info.update(data)
          info.update({'status' : a[i]['status'], 'noID': i})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['harga'] = int(item['harga'])
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
      return jsonify(content)

    @app.route("/api/v1/sla")
    def statusSLA():
      global url_dashboard
      status_dashboard = getAPIDashboard(url_dashboard)
      info = {}
      content = []
      a = [{"id": str(d['sensorID_new']), "sla": d['snmp'], "tagihan": d['tagihan'], "harga_new": d['harga']} for d in status_dashboard if 'sensorID_new' and 'snmp' and 'tagihan' and 'harga' in d]
      for i in range(len(a)):
        x = collection.find_one({"sensorID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          info.update(data)
          info.update({'sla' : a[i]['sla'], 'tagihan': a[i]['tagihan'], 'harga_new': a[i]['harga_new'], 'noID': i})
          content.append(info)
        info = {}
        for item in content:
          item['c_n'] = item['c_n'].replace('_', '.')
          item['longitude'] = item ['longitude'].replace('_', '.')
          item['latitude'] = item['latitude'].replace('_', '.')
          item['harga'] = int(item['harga'])
          item['prtgsite'] = item ['prtgsite'].replace('-', '.')
      return jsonify(content)

    @app.route("/api/v1/topsla")
    def topSLA():
       global url_dashboard
       status_dashboard = getAPIDashboard(url_dashboard)
       sorted_sla = sorted(status_dashboard, key=itemgetter('snmp'), reverse=True)
       return jsonify(sorted_sla[:10])

    @app.route("/api/v1/topdowntime")
    def longestDowntime():
      global url_downtimesince1
      global url_downtimesince2
      ping = getAPIData(url_downtimesince1, url_downtimesince2)
      for x in ping:
         if x['downtimesince_raw'] == "":
            x['downtimesince_raw'] = 0
      sorted_ping = sorted(ping, key=itemgetter('downtimesince_raw'), reverse=True)

      return jsonify(sorted_ping[97:107])

    @app.route("/api/v1/down")
    def Down():
      global url_downtimesince1
      global url_downtimesince2
      global url_dashboard
      loss = getAPIData(url_downtimesince1, url_downtimesince2)
      loss_dashboard = getAPIDashboard(url_dashboard)
      now = datetime.datetime.now()
      daysofMonth = calendar.monthrange(now.year, now.month)[1]
      secondInMonth = daysofMonth * 86400
      info = {}
      content = []
      a = [{"id": str(d['objid']), "downtimesince_raw": d['downtimesince_raw'], "status": d['status']} \
      for d in loss if 'objid' and 'downtimesince_raw' and 'status' in d]
      b = [{"id": str(d['sensorPing']), "tagihan": d['tagihan'], "tagihan_new": d['tagihan_after'], "tagihan_old": d['tagihan_before'], \
      "sla": d['snmp'], "old_sla": d['snmp_before'], "new_sla": d['snmp_after'], "harga": d['harga'], "old_harga": d['old_harga'], \
      "new_harga": d['new_harga'], } for d in loss_dashboard if 'sensorPing' and 'snmp' and 'tagihan' and 'tagihan_after' and 'tagihan_before' and \
      'snmp_before' and 'snmp_after' and 'harga' and 'old_harga' and 'new_harga' in d]
      for i in range(len(a)):
        x = collection.find_one({"pingID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          for indx in b:
             if (indx['id'] == data['pingID']):
                data.update({'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla'], 'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new'], 'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']})
                info.update(data)
          info.update({'downtimesince_raw' : a[i]['downtimesince_raw'], 'noID': i})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['harga'] = int(item['harga'])
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        if item['downtimesince_raw'] == "":
           item['downtimesince_raw'] = "0"
        x = float(item['downtimesince_raw'])
        item['loss'] = (x/float(secondInMonth)) * item['harga']

      sorted_content = sorted(content, key=itemgetter('loss'), reverse=True)
      return jsonify(sorted_content)

    @app.route("/api/v1/toploss")
    def topLoss():
      global url_downtimesince1
      global url_downtimesince2
      loss = getAPIData(url_downtimesince1, url_downtimesince2)
      now = datetime.datetime.now()
      daysofMonth = calendar.monthrange(now.year, now.month)[1]
      millisInMonth = daysofMonth * 86400000
      info = {}
      content = []
      a = [{"id": str(d['objid']), "downtimesince_raw": d['downtimesince_raw']} for d in loss if 'objid' and 'downtimesince_raw' in d]
      for i in range(len(a)):
        x = collection.find_one({"pingID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          info.update(data)
          info.update({'downtimesince_raw' : a[i]['downtimesince_raw']})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['harga'] = int(item['harga'])
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        if item['downtimesince_raw'] == "":
           item['downtimesince_raw'] = "0"
        x = float(item['downtimesince_raw'])
        item['loss'] = (x/float(millisInMonth)) * item['harga']

      sorted_content = sorted(content, key=itemgetter('loss'), reverse=True)
      return jsonify(sorted_content[:10])

    @app.route("/api/v1/highutil")
    def highUtil():
      global url_traffic1
      global url_traffic2
      status_all = getAPIData(url_traffic1, url_traffic2)
      info = {}
      content = []
      a = [{"id": str(d['objid']), "traffic": d['lastvalue']} for d in status_all if 'objid' and 'lastvalue' in d]
      for i in range(len(a)):
        x = collection.find_one({"trafficID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          info.update(data)
          info.update({'traffic' : a[i]['traffic']})
          content.append(info)
        info = {}
      print(content)
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['harga'] = int(item['harga'])
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        traffic_raw = float(item['traffic'].replace(' kbit/s',"").replace(',','.'))
        item['traffic_raw'] = traffic_raw
        capacitylink_raw = float(item['capacitylink'].replace(' Mbps',"")) * 1000
        item['capacitylink_raw'] = capacitylink_raw
        utility = (traffic_raw/capacitylink_raw) * 100
        item['utility'] = utility
      sorted_content = sorted(content, key=itemgetter('utility'), reverse=True)
      return jsonify(sorted_content[:10])

    @app.route("/api/v1/lowutil")
    def lowUtil():
      global url_traffic1
      global url_traffic2
      status_all = getAPIData(url_traffic1, url_traffic2)
      info = {}
      content = []
      a = [{"id": str(d['objid']), "traffic": d['lastvalue']} for d in status_all if 'objid' and 'lastvalue' in d]
      for i in range(len(a)):
        x = collection.find_one({"trafficID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          info.update(data)
          info.update({'traffic' : a[i]['traffic']})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['harga'] = int(item['harga'])
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        traffic_raw = float(item['traffic'].replace(' kbit/s',"").replace(',','.'))
        item['traffic_raw'] = traffic_raw
        capacitylink_raw = float(item['capacitylink'].replace(' Mbps',"")) * 1000
        item['capacitylink_raw'] = capacitylink_raw
        utility = (traffic_raw/capacitylink_raw) * 100
        item['utility'] = utility
      sorted_content = sorted(content, key=itemgetter('utility'))
      return jsonify(sorted_content[:10])

      @app.route('/limitsetting', methods=['POST'])
      def limit():
        limit = requests.get('limit')
        if limit is not None:
          setting.update({"limit": limit})
          return jsonify({'ok': True, 'message': 'Limit Updated'}), 200
        else:
          return jsonify({'ok': False, 'message': 'Value not valid!'}), 400

    return app
