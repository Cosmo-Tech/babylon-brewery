import sys
import json
from Babylon.utils.environment import Environment



def main():
    env = Environment()
    print("One day in Babylon")
    obj = sys.argv
    inputs = obj[1]
    inputs_dict = json.loads(inputs)
    deploy = json.loads(inputs_dict['deploy'])
    platform = json.loads(inputs_dict['platform'])
    for i,v in deploy.items():
        env.configuration.set_deploy_var(i, v)
    for i,v in platform.items():
        env.configuration.set_platform_var(i, v)


if __name__ == "__main__":
    main()