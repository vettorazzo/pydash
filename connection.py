import pymysql
import configparser

def conecta_BD():
    config = configparser.ConfigParser()
    config.read("config.ini")
    user_mysql = config.get('mysql', 'user')
    password_mysql = config.get('mysql', 'password')
    server_mysql = config.get('mysql', 'server')
    bd_mysql = config.get('mysql', 'bd')
    conn = pymysql.connect(host=server_mysql, user=user_mysql, passwd=password_mysql, db=bd_mysql)
    cursor = conn.cursor()
    return cursor,conn

def conecta_BD_Super():
    config = configparser.ConfigParser()
    config.read("config.ini")
    user_mysql = config.get('mysql-super', 'user')
    password_mysql = config.get('mysql-super', 'password')
    server_mysql = config.get('mysql-super', 'server')
    bd_mysql = config.get('mysql-super', 'bd')
    conn = pymysql.connect(host=server_mysql, user=user_mysql, passwd=password_mysql, db=bd_mysql)
    cursor = conn.cursor()
    return cursor,conn

def busca_Servidores(cursor):
    cursor.execute('select UUID_POOL, LABEL_POOL, DESCR_POOL, MASTER_POOL,\
                    DEFAULT_SR, HOST, UUID_HOST, MODELO_HOST, nCPU_HOST, \
                    MEMORIA_TOTAL_HOST, MEMORIA_LIVRE_HOST, NOME_VM, \
                    UUID_VM, DESCR_VM, SISTEMA_OPERACIONAL_VM, nCPU_VM,\
                    MEMORIA_VM, HOST_RESIDENTE_ON, POWER_STATUS \
                    from servidores ');
    rows_ambiente = cursor.fetchall()
    return rows_ambiente

def busca_Volumes(cursor,storage):
    cursor.execute('select idvolumes, name_volumes, full_volumes, used_volumes, \
                available_volumes, percent_volumes, svm_volumes, \
                department_volumes, groupDep_volumes, fullSnap_volumes, \
                usedSnap_volumes, availableSnap_volumes, percentSnap_volumes,\
                nameAggregate_volumes, controller_volumes from volumes \
                where controller_volumes LIKE "{}"'.format(storage)),
    rows = cursor.fetchall()
    return rows

def busca_VolumesPorGrupo(cursor,storage):
    cursor.execute('select distinct department_volumes, groupDep_volumes from volumes where controller_volumes LIKE "{}"'.format(storage))
    rows = cursor.fetchall()
    return rows

def busca_Aggregates(cursor,storage):
    cursor.execute('select idaggregate, name_aggregate, fullSize_aggregate, usedSize_aggregate, \
                availableSize_aggregate, usedCapacity_aggregate, nameStorage_aggregate from aggregate \
                where nameStorage_aggregate LIKE "{}"'.format(storage)),
    rows_aggr = cursor.fetchall()
    return rows_aggr

def busca_Contratos(cursor):
    cursor.execute('select *  from contrato'),
    rows_contrato = cursor.fetchall()
    return rows_contrato

def busca_MaquinasFisicas(cursor):
    cursor.execute('select * from maquinas_fisicas'),
    rows_maqfisica = cursor.fetchall()
    return rows_maqfisica

def busca_Discos(cursor):
    cursor.execute('select iddisk, size_disk, unitSize_disk, format_disk, \
                    aggregateType_disk, aggregateName_disk, node_disk from disk \
                    where node_disk LIKE "olinda%" or node_disk LIKE "landsat%" \
                    or node_disk LIKE "aggr%"'),
    rows_disk = cursor.fetchall()
    return rows_disk
    
def buscaDadosEgeon(cursor):
    cursor.execute('SELECT `update`, running FROM history_super_egeon;')
    resultSearch = cursor.fetchall()
    return resultSearch

def buscaDadosXC50(cursor):
    cursor.execute('SELECT `update`, running FROM history_super_xc50;')
    resultSearch = cursor.fetchall()
    return resultSearch