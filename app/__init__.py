# app/__init__.py

from flask_api import FlaskAPI
from bson import json_util
from bson.objectid import ObjectId
from pprint import pprint
from io import BytesIO
import json
import requests
import calendar
import datetime
import os
import csv
from time import sleep, strftime, time
from flask import jsonify, request, send_file
from flask_cors import CORS
from operator import itemgetter
from pymongo import MongoClient
import urllib3
import hashlib
import xmltodict
from xml.etree import ElementTree
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from PIL import Image
from flask_mail import Mail, Message
from celery import Celery

# local import
from instance.config import app_config
from flask_mail import Mail, Message


client = MongoClient()
db=client.dashboard
setting = db.settings

now = datetime.datetime.now()
last_month = now.month - 1 if now.month > 1 else 12
last_year = now.year

prefix = "/api/table.json?content=sensors&id="
url_uptime = "&columns=objid,device,sensor,lastvalue,status,message&sortby=-lastvalue&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_ping = "&columns=objid,sensor,lastvalue,status,message&sortby=lastvalue&filter_type=ping&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_traffic = "&columns=objid,sensor,lastvalue,status&sortby=-lastvalue&filter_type=snmptraffic&username=prtguser&password=Bp3t1OK!&filter_status=3"
url_downtimesince = "&columns=objid,sensor,lastvalue,status,message,downtimesince&sortby=downtimesince&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!&filter_status=5&filter_status=4&filter_status=10&filter_status=13&filter_status=14"
url_all = "&columns=objid,device,sensor,lastvalue,status,message,downtimesince&sortby=-lastvalue&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!"
url_unknown = "&columns=objid,sensor,lastvalue,status,message,downtimesince&sortby=downtimesince&filter_type=snmpuptime&username=prtguser&password=Bp3t1OK!&filter_status=1"
url_dashboard = "http://182.23.61.67/api/getdatabase/" + str(last_month) + "/" + str(last_year) + "/old/"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def create_app(config_name):
    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER']='localhost'
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USE_TLS'] = False
    app.config['CELERY_BROKER_URL'] = 'amqp://kirei:apollo@localhost:5672/apollo'

    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    CORS(app)
    mail = Mail(app)

    def getAPIData(url):
      response = requests.get(url, verify=False)
      json_data = json.loads(response.text)
      data = json_data["sensors"]

      return data

    def filterAPI(objectID):
       data = {}
       users = db.users
       exist = users.find_one({"_id": ObjectId(objectID)})
       if exist is not None:
          data = json.loads(json_util.dumps(exist))
       return data

    def getCollection(objectID):
      data = filterAPI(objectID)
      collection = data['data']
      return collection

    def getAPIDashboard(url, objectID):
      data = filterAPI(objectID)
      x = url + data['ispID']
      try:
        r = requests.post(url=x)
        json_data = json.loads(r.text)
      except:
       json_data = {'response': 'no data'}

      return json_data

    def getFilterData(url, objectID):
        data = filterAPI(objectID)
        if data['prtgsite_2'] is not None:
            url_1 = "https://" + data['prtgsite_1'] + prefix + data['prtgsensorid_1'] + url
            url_2 = "https://" + data['prtgsite_2'] + prefix + data['prtgsensorid_2'] + url
            json_data = getAPIData(url_1) + getAPIData(url_2)
        else:
            url_1 = "https://" + data['prtgsite_1'] + prefix + data['prtgsensorid_1'] + url
            json_data = getAPIData(url_1)
        return json_data

    def getXMLfromAPI(url):
        res = requests.get(url, verify=False)
        res_tree = ElementTree.fromstring(res.content)
        tree = ElementTree.tostring(res_tree, encoding='utf8').decode('utf8')
        data = json.dumps(xmltodict.parse(tree))
        data = json.loads(data)
        return data

    def serve_image(img):
       img_io = BytesIO()
       img.save(img_io, 'PNG', quality=70)
       img_io.seek(0)
       return send_file(img_io, mimetype='images/png')

    @app.route("/api/v1/<objectID>/top10/<cluster>/uptime/<type>")
    def topTenUptime(objectID, cluster, type):
        global url_uptime
        uptime = getFilterData(url_uptime, objectID)
        collection = db[getCollection(objectID)]
        info = {}
        content = []
        for key in uptime:
            x = collection.find_one({'sensorID': key['objid']})
            if x is not None:
                data = json.loads(json_util.dumps(x))
                if cluster != 'total':
                    if data['cluster'] == cluster:
                        info.update(data)
                        if key['lastvalue_raw'] == "":
                            key['lastvalue_raw'] = 0
                        key['lastvalue'] = key['lastvalue'].replace(' ', '')
                        info.update({'lastvalue_raw': key['lastvalue_raw'], 'lastvalue': key['lastvalue']})
                        content.append(info)
                        info = {}
                elif cluster == 'total':
                    info.update(data)
                    if key['lastvalue_raw'] == "":
                        key['lastvalue_raw'] = 0
                    key['lastvalue'] = key['lastvalue'].replace(' ', '')
                    info.update({'lastvalue_raw': key['lastvalue_raw'], 'lastvalue': key['lastvalue']})
                    content.append(info)
                    info = {}
        if type == 'long':
            sorted_uptime = sorted(content, key=itemgetter('lastvalue_raw'), reverse=True)
        elif type == 'short':
            sorted_uptime = sorted(content, key=itemgetter('lastvalue_raw'))
        else:
            return "Not Valid"
        return jsonify(sorted_uptime[:10])

    @app.route("/api/v1/<objectID>/top10/<cluster>/ping/<type>")
    def topTenPing(objectID, cluster, type):
        global url_ping
        ping = getFilterData(url_ping, objectID)
        collection = db[getCollection(objectID)]
        info = {}
        content = []
        for key in ping:
            x = collection.find_one({'pingID': key['objid']})
            if x is not None:
                data = json.loads(json_util.dumps(x))
                if cluster != 'total':
                    if data['cluster'] == cluster:
                        info.update(data)
                        info.update({'lastvalue_raw': key['lastvalue_raw']})
                        content.append(info)
                elif cluster == 'total':
                    info.update(data)
                    info.update({'lastvalue_raw': key['lastvalue_raw']})
                    content.append(info)
            info = {}
        if type == 'fast':
            sorted_ping = sorted(content, key=itemgetter('lastvalue_raw'))
        elif type == 'slow':
            sorted_ping = sorted(content, key=itemgetter('lastvalue_raw'), reverse=True)
        else:
            return "Not Valid"
        return jsonify(sorted_ping[:10])

    @app.route("/api/v1/<objectID>/status")
    def statusSensor(objectID):
      global url_all
      global url_dashboard
      status_all = getFilterData(url_all, objectID)
      status_dashboard = getAPIDashboard(url_dashboard, objectID)
      collection = db[getCollection(objectID)]
      info = {}
      content = []
      a = [{"id": d['objid'], "status": d['status']} for d in status_all if 'objid' and 'status' in d]
      b = [{"id": d['sensorID_new'], "tagihan": d['tagihan'], "tagihan_new": d['tagihan_after'], "tagihan_old": d['tagihan_before'],
      "sla": d['snmp'], "old_sla": d['snmp_before'], "new_sla": d['snmp_after'], "harga": d['harga'], "old_harga": d['old_harga'],
      "new_harga": d['new_harga'], } for d in status_dashboard if 'sensorPing' and 'snmp' and 'tagihan' and 'tagihan_after' and 'tagihan_before' and
      'snmp_before' and 'snmp_after' and 'harga' and 'old_harga' and 'new_harga' in d]
      #print(b)
      for i in range(len(a)):
        x = collection.find_one({"sensorID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          for indx in b:
             if (indx['id'] == data['sensorID']):
                data.update({'sla':{'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla']}, 'tagihan':{'tagihan': indx['tagihan'], \
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new']}, 'harga': {'harga': indx['harga'], 'old_harga': indx['old_harga'], 'new_harga': indx['new_harga']}})
                info.update(data)
          info.update({'status' : a[i]['status'], 'noID': i})
          content.append(info)
        info = {}
      return jsonify(content)

    @app.route("/api/v1/<objectID>/top10/<cluster>/sla")
    def topTenSLA(objectID, cluster):
       global url_dashboard
       status_dashboard = getAPIDashboard(url_dashboard, objectID)
       info = {}
       content = []
       collection = db[getCollection(objectID)]
       for key in status_dashboard:
           x = collection.find_one({'sensorID': key['sensorID_new']})
           if x is not None:
               data = json.loads(json_util.dumps(x))
               if cluster != 'total':
                   if data['cluster'] == cluster:
                       info.update(data)
                       info.update({'snmp': key['snmp']})
                       content.append(info)
               elif cluster == 'total':
                   info.update(data)
                   info.update({'snmp': key['snmp']})
                   content.append(info)
           info = {}
       sorted_sla = sorted(content, key=itemgetter('snmp'), reverse=True)
       return jsonify(sorted_sla[:10])

    @app.route("/api/v1/<objectID>/top10/<cluster>/downtime")
    def topTenLongDowntime(objectID, cluster):
      global url_downtimesince
      ping = getFilterData(url_downtimesince, objectID)
      info = {}
      content = []
      collection = db[getCollection(objectID)]
      for key in ping:
        x = collection.find_one({"sensorID": key['objid']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          if cluster != 'total':
             if data['cluster'] == cluster:
                 info.update(data)
                 info.update(
                     {'downtimesince': key['downtimesince'], 'downtimesince_raw': key['downtimesince_raw']}
                 )
                 content.append(info)
          elif cluster == 'total':
             info.update(data)
             info.update(
                 {'downtimesince': key['downtimesince'], 'downtimesince_raw': key['downtimesince_raw']}
             )
             content.append(info)
        info = {}
      for item in content:
        if item['downtimesince_raw'] == "":
           item['downtimesince_raw'] = 0

      sorted_ping = sorted(content, key=itemgetter('downtimesince_raw'), reverse=True)

      return jsonify(sorted_ping[:10])


    @app.route("/api/v1/<objectID>/down")
    def Down(objectID):
      global url_downtimesince
      global url_dashboard
      #print(url_dashboard)
      loss = getFilterData(url_downtimesince, objectID)
      loss_dashboard = getAPIDashboard(url_dashboard, objectID)
      #print(loss_dashboard)
      hari = datetime.date.today()
      first = hari.replace(day=1)
      lastMonth = first - datetime.timedelta(days=1)
      hariBulanKemarin = calendar.monthrange(lastMonth.year, lastMonth.month)[1]
      jumlahDetikBlnKemarin = hariBulanKemarin * 86400
      now = datetime.datetime.now()
      daysofMonth = calendar.monthrange(now.year, now.month)[1]
      secondInMonth = daysofMonth * 86400
      today = now.day * 86400
      jumlah = today + jumlahDetikBlnKemarin - 600
      collection = db[getCollection(objectID)]
      info = {}
      content = []
      a = [{"id": d['objid'], "downtimesince_raw": d['downtimesince_raw'], "status": d['status']}
      for d in loss if 'objid' and 'downtimesince_raw' and 'status' in d]
      b = [{"id": d['sensorID_new'], "tagihan": d['tagihan'], "tagihan_new": d['tagihan_after'], "tagihan_old": d['tagihan_before'],
      "sla": d['snmp'], "old_sla": d['snmp_before'], "new_sla": d['snmp_after'], "harga": d['harga'], "old_harga": d['old_harga'],
      "new_harga": d['new_harga'], } for d in loss_dashboard if 'sensorPing' and 'snmp' and 'tagihan' and 'tagihan_after' and 'tagihan_before' and
      'snmp_before' and 'snmp_after' and 'harga' and 'old_harga' and 'new_harga' in d]
      #print(loss_dashboard)
      for i in range(len(a)):
        x = collection.find_one({"sensorID": a[i]['id']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          #print(data)
          for indx in b:
             if (indx['id'] == data['sensorID']):
                data.update({'sla': {'sla': indx['sla'], 'old_sla': indx['old_sla'], 'new_sla': indx['new_sla']},
                             'tagihan': {'tagihan': indx['tagihan'],
                  'old_tagihan': indx['tagihan_old'], 'new_tagihan': indx['tagihan_new']},
                             'harga': {'harga': indx['harga'], 'old_harga': indx['old_harga'],
                                       'new_harga': indx['new_harga']}})
                info.update(data)
          info.update({'downtimesince_raw' : a[i]['downtimesince_raw'], 'noID': i})
          content.append(info)
        info = {}
      #print(content)
      for item in content:
        if item['downtimesince_raw'] == "":
          item['downtimesince_raw'] = 0
        x = float(item['downtimesince_raw'])
        if x > 0 and x < float(jumlah):
          if x > float(today):
            loss_kemarin = x - float(today)
            item['loss'] = (loss_kemarin/float(jumlahDetikBlnKemarin) + (x - loss_kemarin)/float(secondInMonth)) * item['harga']['harga']
          else:
            item['loss'] = (x/float(secondInMonth)) * item['harga']['harga']
        else:
          item['loss'] = 0

      sorted_content = sorted(content, key=itemgetter('loss'), reverse=True)
      return jsonify(sorted_content)

    @app.route("/api/v1/<objectID>/top10/<cluster>/loss")
    def topTenLoss(objectID, cluster):
        global url_downtimesince
        global url_dashboard
        loss = getFilterData(url_downtimesince, objectID)
        loss_dashboard = getAPIDashboard(url_dashboard, objectID)
        hari = datetime.date.today()
        first = hari.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        hariBulanKemarin = calendar.monthrange(lastMonth.year, lastMonth.month)[1]
        jumlahDetikBlnKemarin = hariBulanKemarin * 86400
        now = datetime.datetime.now()
        daysofMonth = calendar.monthrange(now.year, now.month)[1]
        secondInMonth = daysofMonth * 86400
        today = now.day * 86400
        jumlah = today + jumlahDetikBlnKemarin - 600
        collection = db[getCollection(objectID)]
        info = {}
        content = []
        for key in loss:
            x = collection.find_one({"sensorID": key['objid']})
            if x is not None:
                data = json.loads(json_util.dumps(x))
                for dash in loss_dashboard:
                    if (dash['sensorID_new'] == data['sensorID']):
                        if cluster != 'total':
                            if data['cluster'] == cluster:
                                data.update(
                                    {'sla': {'sla': dash['snmp'], 'old_sla': dash['snmp_before'],
                                             'new_sla': dash['snmp_after']},
                                     'tagihan': {'tagihan': dash['tagihan'],
                                                 'old_tagihan': dash['tagihan_before'],
                                                 'new_tagihan': dash['tagihan_after']},
                                     'harga': {'harga': dash['harga'], 'old_harga': dash['old_harga'],
                                               'new_harga': dash['new_harga']}})
                                info.update(data)
                                info.update({'downtimesince_raw': key['downtimesince_raw']})
                                content.append(info)
                        elif cluster == 'total':
                            data.update(
                                {'sla': {'sla': dash['snmp'], 'old_sla': dash['snmp_before'], 'new_sla': dash['snmp_after']},
                                 'tagihan': {'tagihan': dash['tagihan'],
                                             'old_tagihan': dash['tagihan_before'], 'new_tagihan': dash['tagihan_after']},
                                 'harga': {'harga': dash['harga'], 'old_harga': dash['old_harga'],
                                           'new_harga': dash['new_harga']}})
                            info.update(data)
                            info.update({'downtimesince_raw': key['downtimesince_raw']})
                            content.append(info)
            info = {}
        for item in content:
            if item['downtimesince_raw'] == "":
                item['downtimesince_raw'] = 0
            x = float(item['downtimesince_raw'])
            if 0 < x < float(jumlah):
                if x > float(today):
                    loss_kemarin = x - float(today)
                    item['loss'] = (loss_kemarin / float(jumlahDetikBlnKemarin) + (x - loss_kemarin) / float(
                        secondInMonth)) * item['harga']['harga']
                else:
                    item['loss'] = (x / float(secondInMonth)) * item['harga']['harga']
            else:
                item['loss'] = 0

        sorted_content = sorted(content, key=itemgetter('loss'), reverse=True)
        return jsonify(sorted_content[:10])

    @app.route("/api/v1/<objectID>/top10/<cluster>/util/<type>")
    def topTenUtil(objectID, cluster, type):
      global url_traffic
      status_all = getFilterData(url_traffic, objectID)
      collection = db[getCollection(objectID)]
      info = {}
      content = []
      for key in status_all:
        x = collection.find_one({"trafficID": key['objid']})
        if x is not None:
          data = json.loads(json_util.dumps(x))
          if cluster != 'total':
              if data['cluster'] == cluster:
                  info.update(data)
                  info.update({'traffic': key['lastvalue']})
                  content.append(info)
          elif cluster == 'total':
              info.update(data)
              info.update({'traffic': key['lastvalue']})
              content.append(info)
        info = {}
      for item in content:
        item['harga'] = int(item['harga'])
        traffic_raw = float(item['traffic'].replace(' kbit/s', "").replace(',', '.'))
        item['traffic_raw'] = traffic_raw
        capacitylink_raw = float(item['capacitylink'].replace(' Mbps', "")) * 1000
        item['capacitylink_raw'] = capacitylink_raw
        utility = (traffic_raw/capacitylink_raw) * 100
        item['utility'] = utility
      if type == 'low':
          sorted_content = sorted(content, key=itemgetter('utility'))
      elif type == 'high':
          sorted_content = sorted(content, key=itemgetter('utility'), reverse=True)
      else:
          return "Not Valid"

      return jsonify(sorted_content[:10])

    @app.route("/api/v1/<objectID>/setlimit", methods=['POST'])
    def setLimit(objectID):
        limit = request.form['limit']
        #print(limit)
        data = filterAPI(objectID)
        users = db.users
        if limit != "":
          users.update_one({'isp': data['isp']},{ '$set': {'limit': limit}})
          return jsonify({'ok': True, 'message': 'Limit Updated'}), 200
        else:
          return jsonify({'ok': False, 'message': 'Value not valid!'}), 400

    @app.route("/api/v1/<objectID>/settimeemail", methods=['POST'])
    def setEmailTime(objectID):
        tipe = request.form['tipe']
        value = request.form['value']
        data = filterAPI(objectID)
        users = db.users
        if value != "":
            users.update_one({'isp': data['isp']}, {'$set': {'tipe': tipe, 'value': value}})
            return jsonify({'ok': True, 'message': 'Email Time Updated'}), 200
        else:
            return jsonify({'ok': False, 'message': 'Value not valid!'}), 400

    @app.route("/api/v1/<objectID>/gettimeemail", methods=['GET'])
    def getEmailTime(objectID):
        data = filterAPI(objectID)
        return jsonify({'tipe': data['tipe'], 'value': data['value']})

    @app.route("/api/v1/<objectID>/setemail", methods=['POST'])
    def setEmail(objectID):
        subject = request.form['subject']
        body = request.form['body']
        data = filterAPI(objectID)
        users = db.users
        if body is not None:
            users.update_one({'isp': data['isp']}, {'$set': {'subject': subject, 'body': body}})
            return jsonify({'ok': True, 'message': 'Email Body and Subject Updated'}), 200
        else:
            return jsonify({'ok': False, 'message': 'Value not valid!'}), 400

    @app.route("/api/v1/<objectID>/getemail")
    def getEmail(objectID):
        data = filterAPI(objectID)
        return jsonify({'subject': data['subject'], 'body': data['body']})

    @app.route("/api/v1/<objectID>/getlimit", methods=['GET'])
    def getLimit(objectID):
      data = filterAPI(objectID)
      return jsonify(data['limit'])

    @app.route("/api/v1/<objectID>/upgrade", methods=['GET'])
    def upgradeBandwidth(objectID):
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
     url = 'http://122.248.39.155:5000/api/v1/' + objectID + '/status'
     response = requests.get(url, verify=False)
     raw_data = json.loads(response.text)
     for key in raw_data:
         try:
           traffic_id = key['trafficID']
           ip = key['prtgsite']
           url_volume = 'https://' + ip + '/api/historicdata.json?id='
           url_traffic = url_volume + str(traffic_id) + param
           res = requests.get(url_traffic, verify=False)
           data = json.loads(res.text)
           if data is not None:
               total = 0
               gb = 0
               for item in data['histdata']:
                 if item['Traffic Total (volume)'] == "":
                    item['Traffic Total (volume)'] = 0.0
                 total = total + float(item['Traffic Total (volume)'])
               gb = (total / 1073741824) / daysinMonth
               key['total_volume'] = gb
         except (KeyError, ValueError):
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

    @app.route("/api/v1/<objectID>/getsla/<int:year>", methods=['GET'])
    def getsla(objectID, year):
        info = {}
        content = []
        data = filterAPI(objectID)
        collection = "tb_sla_" + data['ispID'] + "_" + str(year)
        tb = db[collection]
        for x in tb.find():
            if x is not None:
                data = json.loads(json_util.dumps(x))
                info.update(data)
                content.append(info)
            info = {}
        return jsonify(content)

    @app.route("/api/v1/<objectID>/getsla/<int:year>/<int:sensor>", methods=['GET'])
    def getslalocation(objectID,year,sensor):
      today = datetime.date.today()
      first = today.replace(day=1)
      lastMonth = first - datetime.timedelta(days=1)
      lastMonth = lastMonth.replace(day=1)
      data = filterAPI(objectID)
      url = "http://182.23.61.67/api/getdatabase/"
      info = {}
      content = []
      for i in range(1,13):
          #print(i)
          try:
              params = str(i) + '/' + str(year) + '/old/sensor/'+ str(sensor) + '/' + data['ispID']
              url_dashboard = url + params
              response = requests.post(url=url_dashboard)
              #print('teset')
              raw_data = json_util.loads(response.text)
              snmp = 0
              if raw_data[0]['snmpUptime'] is not None:
                 if len(raw_data) > 1:
                    average_sla = float(sum(d['sla'] for d in raw_data) / len(raw_data))
                 else:
                    average_sla = raw_data[0]['sla']
                 average_sla = round(average_sla,2)
                 info.update({'bulan': i, 'sla': average_sla})
                 content.append(info)
                 info = {}
              else:
                 info.update({'bulan': i, 'sla': None})
                 content.append(info)
                 info = {}
          except:
             pass
      #print(content)
      return jsonify(content)

    @app.route("/api/v1/upload", methods=['POST'])
    def upload():
      target = os.path.join(APP_ROOT, 'files/')
      #print(target)

      if not os.path.isdir(target):
        os.mkdir(target)

      for file in request.files.getlist("file"):
        #print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        #print(destination)
        file.save(destination)
      return jsonify({'ok': True})

    @app.route("/api/v1/getsensor/<sensorid>/<int:year>/<int:month>")
    def getSensorPerMonth(sensorid,year,month):
      target = os.path.join(APP_ROOT, 'files/')
      content = []
      for i in range(32):
        try:
          file = target + sensorid + '-' + str(year) + '-' + str(month).zfill(2) + '-' + str(i).zfill(2) + '.csv'
          csvfile = open(file, 'r')
          reader = csv.DictReader(csvfile)
          for row in reader:
            content.append(row)
        except IOError:
          #print("Could not read file:", file)
          pass
      return jsonify(content)

    @app.route("/api/v1/getsensor/<sensorid>/<int:year>/<int:month>/<int:day>")
    def getSensorDetail(sensorid,year,month,day):
      content = []
      target = os.path.join(APP_ROOT, 'files/')
      csvfile = open(target + sensorid + '-' + str(year) + '-' + str(month).zfill(2) + '-' + str(day).zfill(2) + '.csv', 'r')
      reader = csv.DictReader(csvfile)
      for row in reader:
         content.append(row)
      return jsonify(content)

    @app.route("/api/v1/register/<username>/<password>", methods=['POST'])
    def createUser(username,password):
      users = db.users
      m = hashlib.md5()
      m.update(password.encode('utf-8'))
      users.insert_one({'name' : username, 'password' : m.hexdigest(), 'isp': 7})
      return 'Username ' + username + ' successfully registered'

    @app.route("/api/v1/login", methods=['POST'])
    def Login():
      username = request.form['username']
      password = request.form['password']
      users = db.users
      existing_user = users.find_one({'username': username})
      login_pass = hashlib.md5(password.encode('utf-8'))
      if existing_user:
        if login_pass.hexdigest() == existing_user['password']:
          return {"id": str(existing_user['_id']), 'cluster': existing_user['cluster']}
        return 'Username or password incorrect'
      return 'Username or password incorrect'

    @app.route("/api/v1/<objectID>/changepassword", methods=['POST'])
    def changePassword(objectID):
        password = request.form['password']
        new_password = request.form['new_password']
        data = filterAPI(objectID)
        users = db.users
        new_password_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        existing_user = users.find_one({'password': password_hash})
        if existing_user:
            if password_hash == data['password']:
                users.update_one({'isp': data['isp']}, {'$set': {'password': new_password_hash}})
                return jsonify({'ok': True, 'message': 'Password Updated'}), 200
            return jsonify({'ok': False, 'message': 'Password Invalid'}), 400
        else:
            return jsonify({'ok': False, 'message': 'Password Invalid'}), 400

    @app.route("/api/v1/<objectID>/getimage/<ip>/<sensorid>")
    def getImage(objectID, ip, sensorid):
      url = "https://" + ip + "/chart.png?type=graph&width=1200&height=500&graphid=2&id=" + sensorid + "&username=prtguser&password=Bp3t1OK!"
      r = requests.get(url, stream=True, verify=False)
      r.raw.decode_content = True
      img = Image.open(r.raw)
      return serve_image(img)

    @app.route("/api/v1/send", methods=['POST'])
    def sendMail():
        content = request.get_json()
        subject = content['subject']
        body = content['body']
        users = content['users']
        with mail.connect() as conn:
            for user in users:
                msg = Message(subject, sender='apollo@kirei.co.id', recipients=[user])
                msg.html = body
                conn.send(msg)
        return 'Message Sent!'

    @app.route("/api/v1/<objectID>/getsummary/<int:month>/<int:year>")
    def getSummary(objectID, month, year):
        data_isp = filterAPI(objectID)
        filename = "tb_sla_sensor_{}_{}_{}".format(str(month), str(year), str(data_isp['ispID']))
        collection = db[filename]
        x = collection.find()
        l = list(x)
        data = json.loads(json_util.dumps(l))
        return jsonify(data)

    @app.route("/api/v1/<objectID>/losslevel")
    def getLossLevel(objectID):
        data = filterAPI(objectID)
        limit = int(data['limit'])
        #print(limit)
        url = "http://localhost:5000/api/v1/{}/down".format(objectID)
        response = requests.get(url)
        raw_data = json_util.loads(response.text)
        print(raw_data)
        info = {}
        content_1 = []
        content_2 = []
        content_3 = []
        for key in raw_data:
            if key['downtimesince_raw'] >= limit:
                info.update({'lokasi': key['lokasi'], 'provinsi': key['provinsi'], 'kabkot': key['kabkot'],
                             'sensorID': key['sensorID'], 'loss': key['loss']})
                if key['loss'] > 50000000:
                    content_1.append(info)
                elif 10000000 <= key['loss'] <= 50000000:
                    content_2.append(info)
                elif 0 < key['loss'] < 10000000:
                    content_3.append(info)
            info = {}
        data = {'total_level_1': len(content_1), 'total_level_2': len(content_2), 'total_level_3': len(content_3),
                'details':{'level1': content_1, 'level2': content_2, 'level3': content_3}}
        #pprint(data)
        return jsonify(data)

    @app.route("/api/v1/<objectID>/table/<startdate>/<enddate>")
    def getTable(objectID, startdate, enddate):
        content = []
        url = 'http://localhost:5000/api/v1/{}/status'.format(objectID)
        response = requests.get(url, verify=False)
        raw_data = json.loads(response.text)
        for key in raw_data:
            info = {}
            sensorID = key['sensorID']
            trafficID = key['trafficID']
            pingID = key['pingID']
            lokasi = key['lokasi']
            ip = key['prtgsite']
            param = '&sdate={}-00-00-00&edate={}-00-00-00&avg=0&username=prtguser&password=Bp3t1OK!'.format(startdate, enddate)
            url_uptime = 'https://{}/api/historicdata_totals.xml?id={}{}'.format(ip, str(sensorID), param)
            url_ping = 'https://{}/api/historicdata_totals.xml?id={}{}'.format(ip, str(pingID), param)
            url_traffic = 'https://{}/api/historicdata_totals.xml?id={}{}'.format(ip, str(trafficID), param)
            print(url_uptime)
            print(url_ping)
            print(url_traffic)
            data_uptime = getXMLfromAPI(url_uptime)
            data_ping = getXMLfromAPI(url_ping)
            data_traffic = getXMLfromAPI(url_traffic)
            #pprint(data_uptime)
            #pprint(data_ping)
            #pprint(data_traffic)
            ping_up = "{} {}".format(str(data_ping['historicdata']['uptimepercent']), str(data_ping['historicdata']['uptime']))
            ping_down = "{} {}".format(str(data_ping['historicdata']['downtimepercent']), str(data_ping['historicdata']['downtime']))
            try:
                ping_avg = "{} msec".format(str(float(float(data_ping['historicdata']['average']) / 10)))
            except:
                ping_avg = 'No Data'
                pass
            uptime_up = "{} {}".format(str(data_uptime['historicdata']['uptimepercent']), str(data_uptime['historicdata']['uptime']))
            uptime_down = "{} {}".format(str(data_uptime['historicdata']['downtimepercent']), str(data_uptime['historicdata']['downtime']))
            try:
                uptime_avg = str(float(data_uptime['historicdata']['average']))
            except:
                uptime_avg = 'No Data'
                pass
            traffic_up = "{} {}".format(str(data_traffic['historicdata']['uptimepercent']), str(data_traffic['historicdata']['uptime']))
            traffic_down = "{} {}".format(str(data_traffic['historicdata']['downtimepercent']), str(data_traffic['historicdata']['downtime']))
            try:
                traffic_avg = "{} kbits/s".format(str(float(float(data_traffic['historicdata']['average']) * 8 / 1024)))
                traffic_total = "{} KBytes".format(str(float(float(data_traffic['historicdata']['sum']) / 8192)))
            except:
                traffic_avg = 'No Data'
                traffic_total = 'No Data'
                pass
            info.update({'lokasi': lokasi, 'ping_up': ping_up, 'ping_down': ping_down, 'ping_avg': ping_avg,
                         'traffic_up': traffic_up, 'traffic_down': traffic_down, 'traffic_avg': traffic_avg,
                         'traffic_total': traffic_total, 'uptime_up': uptime_up, 'uptime_down': uptime_down,
                         'uptime_avg': uptime_avg})
            #print(info)
            content.append(info)
        return jsonify(content)

    @app.route("/api/v1/<objectID>/unknown")
    def getUnknown(objectID):
        global url_unknown
        unknown = getFilterData(url_unknown, objectID)
        collection = db[getCollection(objectID)]
        info = {}
        content = []
        for key in unknown:
            x = collection.find_one({'sensorID': key['objid']})
            if x is not None:
                data = json.loads(json_util.dumps(x))
                info.update(data)
                content.append(info)
            info = {}
        return jsonify(content)

    return app
