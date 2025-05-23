import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    ZABBIX_URL = os.environ.get('ZABBIX_URL', 'http://10.0.0.2:8082/api_jsonrpc.php')
    ZABBIX_TOKEN = os.environ.get('ZABBIX_TOKEN', '247b385c17a6a071888a892f2ede175ea14c3244411cd3b32795ca05deaf1cc8')
    REFRESH_INTERVAL = os.environ.get('REFRESH_INTERVAL', 60)  # in seconds
    DEBUG = os.environ.get('FLASK_DEBUG', False)