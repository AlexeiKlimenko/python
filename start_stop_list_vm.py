#!/usr/bin/python3

# How to use
# python3 start_stop__list_vm.py --action list
# Discovered next VMs:
# VM: test-vm-1 
# VM: backup-vm 
# VM: monitoring-vm 
# python3 start_stop__list_vm.py --action start --name backup-vm

import json, os, requests, argparse

YC_TOKEN = os.getenv('YC_TOKEN')
YC_FOLDER_ID = os.getenv('YC_FOLDER_ID')

headers = {
    'Authorization': f'Bearer {YC_TOKEN}'
}

parser = argparse.ArgumentParser()
parser.add_argument('--action', type=str, help='Action: stop/start/list')
parser.add_argument('--name', type=str, help='Instance name')
args = parser.parse_args()


def stop_instance(instanceID):
    url = f'https://compute.api.cloud.yandex.net/compute/v1/instances/{instanceID}:stop'
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f'Instance with ID = {instanceID} stopped')
    else:
        print(f'Error: {response.text} - {response.status_code}')

def start_instance(instanceID):
    url = f'https://compute.api.cloud.yandex.net/compute/v1/instances/{instanceID}:start'
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(f'Instance with ID = {instanceID} started')
    else:
        print(f'Error: {response.text} - {response.status_code}')

def get_id_by_name(name):
    url = f'https://compute.api.cloud.yandex.net/compute/v1/instances?folderId={YC_FOLDER_ID}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        instances = response.json().get('instances', [])
        for instance in instances:
            name = instance.get('name', [])
            instanceId = instance.get('id')
            if args.name == name:
                return instanceId
    else:
        print(f'Error: {response.text} - {response.status_code}')
        return "NotFoundId"

def list_all_instances():
    url = f'https://compute.api.cloud.yandex.net/compute/v1/instances?folderId={YC_FOLDER_ID}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        instances = response.json().get('instances', [])
        for instance in instances:
            name = instance.get('name', [])
            print(f'VM: {name} ')
    else:
        print(f'Error: {response.text} - {response.status_code}')

if __name__ == "__main__":
    InstanceId = get_id_by_name(args.name)
    if args.action == 'stop':
        print(f'Instance {InstanceId} is stopping')
        stop_instance(InstanceId)
    if args.action == 'start':
        print(f'Instance {InstanceId} is starting')
        start_instance(InstanceId)
    if args.action == 'list':
        print('Discovered next VMs:')
        list_all_instances()
