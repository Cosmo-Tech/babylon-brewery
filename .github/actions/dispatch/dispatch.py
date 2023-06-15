import sys
import json
import requests
from Babylon.utils.environment import Environment


def main():
    env = Environment()
    secrets = env.working_dir.get_file_content(".secrets.yaml.encrypt")
    token = secrets['github']['token']
    
    obj = sys.argv
    inputs = obj[1]
    inputs_dict = json.loads(inputs)
    payload = json.loads(inputs_dict['payload'])
    owner = payload['owner']
    repo_name = payload['repo_name']
    client_payload = payload['client_payload']
    url = f"https://api.github.com/repos/{owner}/{repo_name}/dispatches"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token
    }
    response = requests.post(url, json=client_payload, headers=headers)
    print(response)

if __name__ == "__main__":
    main()