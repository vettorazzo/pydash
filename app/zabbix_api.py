import requests
import json
from flask import current_app
from datetime import datetime, timedelta

class ZabbixAPI:
    def __init__(self):
        self.url = current_app.config['ZABBIX_URL']
        self.token = current_app.config['ZABBIX_TOKEN']
        self.headers = {'Content-Type': 'application/json-rpc'}

    def _make_request(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self.token,
            "id": 1
        }
        
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                data=json.dumps(payload))
            response.raise_for_status()
            return response.json().get('result', {})
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Zabbix API request failed: {e}")
            return None

    def get_hosts(self):
        return self._make_request("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"]
        })

    def get_host_metrics(self, hostid, time_range=60):
        time_till = datetime.now()
        time_from = time_till - timedelta(minutes=time_range)

        # CPU Usage
        cpu_items = self._make_request("item.get", {
            "hostids": hostid,
            "search": {"key_": "system.cpu.util"},
            "output": ["itemid", "name", "key_"]
        })

        # Memory Usage
        memory_items = self._make_request("item.get", {
            "hostids": hostid,
            "search": {"key_": "vm.memory.size"},
            "output": ["itemid", "name", "key_"]
        })

        # Network Traffic
        network_items = self._make_request("item.get", {
            "hostids": hostid,
            "search": {"key_": "net.if.in"},
            "output": ["itemid", "name", "key_"]
        })

        # Disk Usage
        disk_items = self._make_request("item.get", {
            "hostids": hostid,
            "search": {"key_": "vfs.fs.size"},
            "output": ["itemid", "name", "key_"]
        })

        # Get history data for each metric
        metrics = {}
        
        for item in cpu_items:
            history = self._make_request("history.get", {
                "itemids": item['itemid'],
                "history": 0,
                "time_from": time_from.timestamp(),
                "time_till": time_till.timestamp(),
                "output": "extend"
            })
            metrics[f"cpu_{item['key_'].split('.')[-1]}"] = {
                "name": item['name'],
                "data": [{'timestamp': h['clock'], 'value': h['value']} for h in history]
            }

        for item in memory_items:
            history = self._make_request("history.get", {
                "itemids": item['itemid'],
                "history": 3,  # numeric unsigned
                "time_from": time_from.timestamp(),
                "time_till": time_till.timestamp(),
                "output": "extend"
            })
            metrics[f"memory_{item['key_'].split('.')[-1]}"] = {
                "name": item['name'],
                "data": [{'timestamp': h['clock'], 'value': h['value']} for h in history]
            }

        for item in network_items:
            history = self._make_request("history.get", {
                "itemids": item['itemid'],
                "history": 3,
                "time_from": time_from.timestamp(),
                "time_till": time_till.timestamp(),
                "output": "extend"
            })
            metrics[f"network_{item['key_'].split('.')[-1]}"] = {
                "name": item['name'],
                "data": [{'timestamp': h['clock'], 'value': h['value']} for h in history]
            }

        for item in disk_items:
            history = self._make_request("history.get", {
                "itemids": item['itemid'],
                "history": 3,
                "time_from": time_from.timestamp(),
                "time_till": time_till.timestamp(),
                "output": "extend"
            })
            metrics[f"disk_{item['key_'].split('.')[-1]}"] = {
                "name": item['name'],
                "data": [{'timestamp': h['clock'], 'value': h['value']} for h in history]
            }

        return metrics

    def get_host_availability(self, hostid):
        return self._make_request("host.get", {
            "hostids": hostid,
            "output": ["available"],
            "selectItems": ["state"],
            "selectTriggers": ["description", "priority"]
        })

    def get_problems(self):
        return self._make_request("problem.get", {
            "output": "extend",
            "selectTags": "extend",
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": 10
        })
    