# app/__init__.py

from flask_api import FlaskAPI
from bson import json_util, ObjectId
import json
import requests
import calendar
import datetime
import os
import csv
from time import sleep, strftime, time
from flask import jsonify, request
from flask_cors import CORS
from operator import itemgetter
from pymongo import MongoClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# local import
from instance.config import app_config

client = MongoClient()
db=client.dashboard
collection = db.master
setting = db.settings

now = datetime.datetime.now()
last_month = now.month-1 if now.month > 1 else 12
last_year = now.year - 1

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
url_dashboard = "http://182.23.61.67/api/getdatabase/" + str(last_month) + "/" + str(last_year) + "/old/7"
#url_dashboard = "http://182.23.61.67/api/getdatabase/11/2018/old/7"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

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
                data.update({'sla':{'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla']}, 'tagihan':{'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new']}, 'harga': {'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']}})
                info.update(data)
          info.update({'status' : a[i]['status'], 'noID': i})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
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
                data.update({'sla':{'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla']}, 'tagihan': {'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new']}, 'harga': {'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']}})
                info.update(data)
          info.update({'downtimesince_raw' : a[i]['downtimesince_raw'], 'noID': i})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        if item['downtimesince_raw'] == "":
           item['downtimesince_raw'] = "0"
        x = float(item['downtimesince_raw'])
        item['loss'] = (x/float(secondInMonth)) * item['harga']['harga']

      sorted_content = sorted(content, key=itemgetter('loss'), reverse=True)
      return jsonify(sorted_content)

    @app.route("/api/v1/toploss")
    def topLoss():
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
                data.update({'sla':{'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla']}, 'tagihan': {'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new']}, 'harga': {'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']}})
                info.update(data)
          info.update({'downtimesince_raw' : a[i]['downtimesince_raw'], 'noID': i})
          content.append(info)
        info = {}
      for item in content:
        item['c_n'] = item['c_n'].replace('_', '.')
        item['longitude'] = item ['longitude'].replace('_', '.')
        item['latitude'] = item['latitude'].replace('_', '.')
        item['prtgsite'] = item ['prtgsite'].replace('-', '.')
        if item['downtimesince_raw'] == "":
           item['downtimesince_raw'] = "0"
        x = float(item['downtimesince_raw'])
        item['loss'] = (x/float(secondInMonth)) * item['harga']['harga']

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
      #print(content)
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

    @app.route("/api/v1/setlimit", methods=['POST'])
    def setLimit():
        limit = request.form['limit']
        print(limit)
        if limit != "":
          setting.update_one({'noID': 1},{ '$set': {'limit': limit}})
          return jsonify({'ok': True, 'message': 'Limit Updated'}), 200
        else:
          return jsonify({'ok': False, 'message': 'Value not valid!'}), 400

    @app.route("/api/v1/getlimit", methods=['GET'])
    def getLimit():
      x = setting.find_one({'noID': 1})
      data = json.loads(json_util.dumps(x))

      return jsonify(data['limit'])

    @app.route("/api/v1/upgrade", methods=['GET'])
    def upgradeBandwidth():
     today = datetime.date.today()
     first = today.replace(day=1)
     lastMonth = first - datetime.timedelta(days=1)
     lastMonth = lastMonth.replace(day=1)
     #last2Month = lastMonth - datetime.timedelta(days=1)
     #last2Month = last2Month.replace(day=1)
     #last3Month = last2Month - datetime.timedelta(days=1)
     #last3Month = last3Month.replace(day=1)
     daysinMonth =  calendar.monthrange(lastMonth.year, lastMonth.month)[1]
     param = '&sdate=' + lastMonth.strftime('%Y-%m-%d') + '-00-00-00' + '&edate=' + first.strftime('%Y-%m-%d') + '-00-00-00&avg=86400&usecaption=1&username=prtguser&password=Bp3t1OK!'
     url = 'http://122.248.39.155:5000/api/v1/status'
     response = requests.get(url, verify=False)
     raw_data = json.loads(response.text)
     for key in raw_data:
         try:
           traffic_id = key['trafficID']
           ip = key['prtgsite']
           url_volume = 'https://' + ip + '/api/historicdata.json?id='
           url_traffic = url_volume + str(traffic_id) + param
           #print(url_traffic)
           res = requests.get(url_traffic, verify=False)
           #print(res.text)
           data = json.loads(res.text)
           if data is not None:
               total = 0
               gb = 0
               for item in data['histdata']:
                 #print(item['Traffic Total (volume)'])
                 if item['Traffic Total (volume)'] == "":
                    item['Traffic Total (volume)'] = 0.0
                 total = total + float(item['Traffic Total (volume)'])
               gb = (total / 1073741824) / daysinMonth
               key['total_volume'] = gb
               print("Rata-rata Traffic Bulan ini = {} GBytes". format(gb))
         except (KeyError, ValueError) as e:
            key['total_volume'] = 0.0
            pass
     return jsonify(raw_data)

    @app.route("/api/v1/listupgrade/<int:year>/<int:month>", methods=['GET'])
    def listupgrade(year,month):
        info = {}
        content = []
        collection = "tb_traffic_" + str(year) + "_" + str(month)
        tb = db[collection]
        for x in tb.find():
            if x is not None:
                data = json.loads(json_util.dumps(x))
                info.update(data)
                content.append(info)
            info = {}
        return jsonify(content)

    @app.route("/api/v1/getsla/<int:year>", methods=['GET'])
    def getsla(year):
        info = {}
        content = []
        collection = "tb_sla_7_" + str(year)
        tb = db[collection]
        for x in tb.find():
            if x is not None:
                data = json.loads(json_util.dumps(x))
                info.update(data)
                content.append(info)
            info = {}
        return jsonify(content)

    @app.route("/api/v1/getsla/<int:year>/<int:sensor>", methods=['GET'])
    def getslalocation(year,sensor):
      today = datetime.date.today()
      first = today.replace(day=1)
      lastMonth = first - datetime.timedelta(days=1)
      lastMonth = lastMonth.replace(day=1)
      url = "http://182.23.61.67/api/getdatabase/"
      info = {}
      content = []
      for i in range(13):
          print(i)
          try:
              params = str(i) + '/' + str(year) + '/old/sensor/'+ str(sensor) +'/7'
              url_dashboard = url + params
              response = requests.post(url=url_dashboard)
              print('teset')
              raw_data = json_util.loads(response.text)
              snmp = 0
              if len(raw_data) > 1:
                  average_sla = float(sum(d['sla'] for d in raw_data) / len(raw_data))
              else:
                  average_sla = raw_data[0]['sla']
              average_sla = round(average_sla,2)
              info.update({'bulan': i, 'sla': average_sla})
              content.append(info)
              info = {}
              snmp = 0
          except:
              pass
      print(content)
      return jsonify(content)

    @app.route("/api/v1/upload", methods=['POST'])
    def upload():
      target = os.path.join(APP_ROOT, 'files/')
      print(target)

      if not os.path.isdir(target):
        os.mkdir(target)

      for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        print(destination)
        file.save(destination)
      return jsonify({'ok': True})

    @app.route("/api/v1/getsensor/<sensorid>/<int:year>/<int:month>")
    def getSensorPerMonth(sensorid,year,month):
      target = os.path.join(APP_ROOT, 'files/')
      content = []
      for i in range(32):
        #print(i)
        try:
          file = target + sensorid + '-' + str(year) + '-' + str(month) + '-' + str(i).zfill(2) + '.csv'
          csvfile = open(file, 'r')
          reader = csv.DictReader(csvfile)
          for row in reader:
            content.append(row)
        except IOError:
          print("Could not read file:", file)
          pass
      return jsonify(content)

    @app.route("/api/v1/getsensor/<sensorid>/<int:year>/<int:month>/<int:day>")
    def getSensorDetail(sensorid,year,month,day):
      content = []
      target = os.path.join(APP_ROOT, 'files/')
      csvfile = open(target + sensorid + '-' + str(year) + '-' + str(month) + '-' + str(day) + '.csv', 'r')
      reader = csv.DictReader(csvfile)
      for row in reader:
         content.append(row)
      return jsonify(content)

    return app
