#!/usr/bin/env python
# Helper script to keep environment TF_VAR variables in sync with .var Terraform variables.
import json
import yaml

ci_file = '.circleci/config.yml'
json_file = 'configs/cloud_settings.json'
tfvars_file = 'deployment/cloud/aws/cicd_vars.tf'


# write_to tfvars_file a list given in HCL .tf valid format.
def write_to(content_list):
    with open(tfvars_file, 'w') as stream:
        for tf_var in content_list:
            stream.writelines(f'variable "{tf_var}" ' + '{ type = string }\n')


# read_from path to find variables starting with TF_VAR
# @return list of variables found.
def read_fromyaml(path):
    envars_list = []
    with open(path, 'r') as stream:
        try:
            ci_yaml = yaml.safe_load(stream)
            if "environment" in ci_yaml["jobs"]["terraform-plan"]:
                for tf_var in ci_yaml["jobs"]["terraform-plan"]["environment"]:
                    envars_list.append(tf_var[7:])

        except yaml.YAMLError as exc:
            print(f'Got exception: \n {exc}')

    return envars_list


# read_from path to find variables starting with TF_VAR
# @return list of variables found.
def read_fromjson(path):
    envars_list = []
    with open(path, 'r') as stream:
        try:
            contents = json.load(stream)
            for tf_var in contents:
                envars_list.append(tf_var)

        except json.JSONDecodeError as exc:
            print(f'Got exception: \n {exc}')

    return envars_list

if __name__ == "__main__":
    tfvars = read_fromyaml(ci_file)
    tfvars += read_fromjson(json_file)

    write_to(tfvars)