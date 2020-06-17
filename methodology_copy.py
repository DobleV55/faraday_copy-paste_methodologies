# -*- coding: utf-8 -*-
import csv
import sys
import json
import click
import tempfile
from requests import Session

@click.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--server_address', prompt=True, help='Faraday server url', default='http://localhost:5985')
@click.option('--workspace_from', prompt=True)
@click.option('--methodology_name', prompt=True)
@click.option('--destination_workspace', prompt=True)
def create_csv_tasks(username, password, server_address, workspace_from, methodology_name, destination_workspace):
    print('Authentication to server {0}'.format(server_address))
    session = Session()
    # authentication to faraday server
    response = session.post(server_address + '/_api/login', json={'email': username, 'password': password})
    assert response.status_code != 401
    methodology_id = None
    methodology_data = session.get(server_address + '/_api/v2/ws/{}/taskGroups/'.format(workspace_from)).json()
    for methodology in methodology_data['rows']:
        if methodology['value']['name'] == methodology_name:
            methodology_id = methodology['value']['_id']
            break
    if not methodology_id:
        print('Methodology "{}" not found'.format(methodology_name))
        sys.exit(1)
    task_data = session.get(server_address + '/_api/v2/ws/{}/tasks/'.format(workspace_from)).json()
    methodology_tasks = []
    for task in task_data['rows']:
        if task['value']['group_id'] == methodology_id:
            methodology_tasks.append(task['value'])
    #data = json_to_csv(methodology_tasks)
    json_to_task(workspace_from, methodology_name, methodology_tasks, session, server_address, username, password, destination_workspace)

def json_to_task(workspace_from, methodology_name, data, session, server_address, username, password, destination_workspace):
    # POST a la API de tasks con el json
    new_methodology = {
        "name": methodology_name,
        "type":"TaskGroup",
        "group_type":"instance",
        "instance_of":"",
        "tCompletedtasks":0,
        "totaltasks":0}
    response = session.post(server_address + '/_api/v2/ws/{}/taskGroups/'.format(destination_workspace), json=new_methodology)
    group_id = response.json()['_id']
    index = 0
    for original_data in data:
        original_data['tags'] = original_data['tags']
        original_data['assigned_to'] = original_data['assigned_to']
        original_data['group_id'] = group_id
        task_response = session.post(
                        server_address + '/_api/v2/ws/{}/tasks/'.format(destination_workspace), 
                        data=json.dumps(original_data)
        )
        assert task_response.status_code == 201, task_response.text
        index += 1

    print('{} tasks created'.format(index))


if __name__ == "__main__":
    create_csv_tasks()
