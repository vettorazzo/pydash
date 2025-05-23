from flask import Blueprint, render_template, jsonify, current_app
from app.zabbix_api import ZabbixAPI
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def dashboard():
    zabbix = ZabbixAPI()
    hosts = zabbix.get_hosts()
    problems = zabbix.get_problems()
    
    # Get data for the first host as default
    host_metrics = {}
    if hosts:
        host_metrics = zabbix.get_host_metrics(hosts[0]['hostid'])
    
    return render_template('dashboard.html', 
                         hosts=hosts, 
                         metrics=host_metrics,
                         problems=problems)

@bp.route('/host/<hostid>')
def host_data(hostid):
    zabbix = ZabbixAPI()
    metrics = zabbix.get_host_metrics(hostid)
    return jsonify(metrics)

@bp.route('/problems')
def get_problems():
    zabbix = ZabbixAPI()
    problems = zabbix.get_problems()
    return jsonify(problems)