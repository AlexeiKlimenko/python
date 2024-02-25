#!/usr/local/bin/python3

#
# via API get backup status of each VM in Proxmox Backup Server, if backup status FAILED then send metric 'offices.proxmox.pbs.{pbs_name}.{failed_vm}.backup_status'
#

import operator
import requests
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import graphyte
from typing import Dict
from operator import itemgetter
from pprint import pprint
import array
from re import search


# define variables

metric_name = 'backup_status'
GRAPHITE_HOST = 'graphite.xxx'
metric_data = 1  # backup FAILED
PBS_CREDENTIALS_FILE = '/temp/pbs.json'

def main():
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning) #Disable SSL warnings

    pbs_array = ['prague-pbs01', 'ny-pbs01', 'paris-pbs01']
    for pbs_name in pbs_array:

        api_token = get_pbs_token()['pbs'][pbs_name]['token']
        result = get_api_data(api_token, pbs_name)
        get_pbs_backup_status(result, pbs_name)

def get_pbs_token() -> Dict:
    # {"pbs": {
    #     "prague-pbs01": {
    #         "token": "XXX",
    #     },
    #     "ny-pbs01": {
    #         "token": "YYY",
    #     },
    #     "paris-pbs01": {
    #         "token": "ZZZ",
    #     }
    # }}
    #
    with open(PBS_CREDENTIALS_FILE, 'r') as f:
        return json.loads(f.read())

def get_api_data(api_token, pbs_name):
    pbs_fqdn_name = pbs_name + '.whitehouse.gov'
        
    api_url = f"https://{pbs_fqdn_name}:8007/api2/json/nodes/localhost/tasks"
    token = 'PBSAPIToken=' + api_token

    headers = {
        'Authorization': token,
    }

    response = requests.get(
        api_url,
        headers=headers,
        timeout=30,
        verify=False
    )

    if response.status_code != 200:
        print('Error! API responded with: {}'.format(response.status_code))
        return

    result = response.json()
    return result

def get_pbs_backup_status(result, pbs_name):

    # List VMs in backups
    all_VMs = []
    for item in result["data"]:
       if item['worker_type'] == 'backup':
          all_VMs.append(item['worker_id'])
    print('working with ', pbs_name)
    print('all_VMs= ', all_VMs)
    # all_VMs = ['Backup_Folder:vm/109', 'Backup_Folder:vm/106', 'Backup_Folder:vm/109,....',

    # Get only unique VMs
    VMs = set(all_VMs)
    print('VMs=', VMs)
    # VMs= {'Backup_Folder:vm/109', 'Backup_Folder:vm/106', 'Backup_Folder:vm/103',....}

    # Init variables for backup status
    dict_backup_status = {}
    for i in VMs:
        dict_backup_status["{0}".format(i)] = "FAILED"
    print('init_backup_status= ', dict_backup_status)
    # init_backup_status=  {'Backup_Folder:vm/101': 'FAILED', 'Backup_Folder:vm/104': 'FAILED', 'Backup_Folder:vm/107': 'FAILED',...

    # MAIN processing JSON to clarify backup status
    for x in result["data"]:
        if x['worker_type'] == 'backup' and x['status'] == 'OK':
            dict_backup_status[x['worker_id']] = "OK"
    print('current backup status= ', dict_backup_status)
    # current backup status=  {'Backup_Folder:vm/101': 'OK', 'Backup_Folder:vm/104': 'OK', 'Backup_Folder:vm/107': 'FAILED',

    # Looking for VMs with backup status FAILED
    target_key = "FAILED"
    keys = [key for key, value in dict_backup_status.items() if value == target_key]

    print("VMs with failed backups:", keys)
    # VMs with failed backups: ['Backup_Folder:vm/107',..

    # Send metrics if backup failed
    if keys:
        for vm in keys:
            # convert VM format from "vm =  Backup_Folder:vm/107 to vm-107"
            vm = vm.replace('/', '-')
            failed_vm = vm.rpartition(':')[2]
            # send metric
            PREFIX = f"offices.proxmox.pbs.{pbs_name}.{failed_vm}"

            print('failed_vm = ',failed_vm)
            print('metric will be send = ', f'{PREFIX}.{metric_name}', metric_data)
            # failed_vm =  vm-107
            # metric will be sent =  offices.proxmox.pbs.prague-pbs01.vm-107.backup_status 1

# graphyte.init(GRAPHITE_HOST)
# graphyte.send(f'{PREFIX}.{metric_name}', metric_data)

main()
