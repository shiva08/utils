import subprocess
import json
import re
from datetime import datetime
import argparse

def valid_sku(allowedSKU, currentSKU):
  for sku in allowedSKU:
    if currentSKU.startswith(sku):
      return True
  return False

def get_ip_array(ip_offset, ip_array):
  ip_object = []
  for ip in ip_array:
    ip_object += [".".join(ip.split(".")[:3]) + "." + str(ip_offset)]

  return ip_object

def get_vm_array(ip_offset, vmnames) : 
  return [(vmname.split("-")[0] + "-" + str(ip_offset + idx)) for idx,vmname in enumerate(vmnames)]

def get_public_ip_array(ip_offset, vmnames) : 
  return [(vmname + "-ip") for idx,vmname in enumerate(vmnames)]

def update_datadisks(json_object, vm_array):
  for idx, vmname in enumerate(vm_array):
    json_object["parameters"]["dataDisks" + str(idx + 1)]["value"][0]["name"] = vmname + "_DataDisk_0"
    json_object["parameters"]["dataDisks" + str(idx + 1)]["value"][1]["name"] = vmname + "_DataDisk_1"

    json_object["parameters"]["dataDiskResources" + str(idx + 1)]["value"][0]["name"] = vmname + "_DataDisk_0"
    json_object["parameters"]["dataDiskResources" + str(idx + 1)]["value"][1]["name"] = vmname + "_DataDisk_1"


def get_list_of_parameter_json_objects(config):
  sample_parameters_json = json.load(open(config["files"]["parameters"]))
  list_of_parameter_json_objects = []
  ip_array = config["subnets"]
  ip_offset = config["ip_offset"]
  file = open(config["files"]["images"])
  for line in file.readlines():
    ip_offset += 1 # IP for VM
    array = re.split(r"\s+", line.strip())
    array[1] = array[1].lower()
    if not(valid_sku(config["allowedSKU"], array[1])):
      continue
    json_object = json.loads(json.dumps(sample_parameters_json))
    json_object["parameters"]["SQLServerImageType"]["value"] = array[0]
    json_object["parameters"]["SQLServerSku"]["value"] = array[1]
    json_object["parameters"]["LocalAdminPassword"]["value"] = config["password"]
    json_object["parameters"]["SQLServiceAccountPassword"]["value"] = config["password"]
    json_object["parameters"]["DomainUserPassword"]["value"] = config["password"]

    json_object["parameters"]["failoverClusterName"]["value"] = sample_parameters_json["parameters"]["failoverClusterName"]["value"] + str(ip_offset)
    json_object["parameters"]["listenerName"]["value"] = sample_parameters_json["parameters"]["listenerName"]["value"] + str(ip_offset)

    vm_array = get_vm_array(ip_offset, config["vmnames"])
    json_object["parameters"]["VMNamesForPrimaryAndSecondaryReplicas"]["value"] = vm_array

    update_datadisks(json_object, vm_array)

    json_object["parameters"]["listOfPublicIps"]["value"] = get_public_ip_array(ip_offset, vm_array)

    json_object["parameters"]["listOfListenerIps"]["value"] = get_ip_array(ip_offset, ip_array)
    ip_offset += 1

    json_object["parameters"]["listOfFailoverClusterIps"]["value"] = get_ip_array(ip_offset, ip_array)
    ip_offset += 1

    list_of_parameter_json_objects += [json_object]

  return list_of_parameter_json_objects, ip_offset

def load_config(config_file):
  config = json.load(open(config_file))
  return config

def update_ip_offset_in_config(ip_offset, config_file):
  new_config = load_config(config_file)
  new_config["ip_offset"] = ip_offset
  new_config["resource_group"]["create"] = False
  f = open(config_file, 'w')
  json.dump(new_config, f, ensure_ascii=False, indent=4)
  f.close()

def create_resource_group(config) : 
  powershell_cmd = "New-AzResourceGroup -Name {resourceGroupName} -location eastus".format(resourceGroupName = config["resource_group"]["name"])
  print(powershell_cmd)
  result = subprocess.run([config["files"]["powershell"], powershell_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
  print(result.stdout.decode('utf-8'))

def deploy_template(config, parameter_json) : 
  new_deployment_filename = parameter_json["parameters"]["SQLServerImageType"]["value"] + "_" +parameter_json["parameters"]["SQLServerSku"]["value"]
  new_parameter_file = new_deployment_filename + "-parameter.json"
  f = open(new_parameter_file, 'w')
  json.dump(parameter_json, f, ensure_ascii=False, indent=4)
  f.close()

  time_now = datetime.now()
  deployment_name = config["deploymentName"] + "_" + new_deployment_filename + "_" + "{}{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(time_now.year,time_now.month,time_now.day,time_now.hour,time_now.minute,time_now.second,time_now.microsecond)
  deploy_template_image_hardcoded = True
  if deploy_template_image_hardcoded :
    template_json = json.load(open(config["files"]["template"]))
    template_json["resources"][0]["properties"]["template"]["resources"][4]["properties"]["storageProfile"]["imageReference"] = {'publisher': 'microsoftsqlserver', 'offer': parameter_json["parameters"]["SQLServerImageType"]["value"], 'sku': parameter_json["parameters"]["SQLServerSku"]["value"], 'version': 'latest'}

    new_template_file = new_deployment_filename + "-template.json"
    f = open(new_template_file, 'w')
    json.dump(template_json, f, ensure_ascii=False, indent=4)
    f.close()

    powershell_cmd = "New-AzResourceGroupDeployment -Name {name} -ResourceGroupName {resourceGroupName} -TemplateFile {templateFile} -TemplateParameterFile {parameterFile} -verbose".format(name = deployment_name, resourceGroupName = config["resource_group"]["name"], templateFile = new_template_file, parameterFile = new_parameter_file)
  else :
    powershell_cmd = "New-AzResourceGroupDeployment -Name {name} -ResourceGroupName {resourceGroupName} -TemplateFile {templateFile} -TemplateParameterFile {parameterFile} -verbose".format(name = deployment_name, resourceGroupName = config["resource_group"]["name"], templateFile = config["files"]["template"], parameterFile = new_parameter_file)

  print(powershell_cmd)

  # trigger deployments to run in parallel
  result = subprocess.Popen([config["files"]["powershell"], powershell_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

  # result = subprocess.run([config["files"]["powershell"], powershell_cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
  # print(result.stdout.decode('utf-8'))

def main(args):
  config_file_name = "config.json"
  config = load_config(config_file_name)
  if config["resource_group"]["create"] or args.testDeploy != None:
    create_resource_group(config)

  if args.testDeploy != None:
    return

  if config["ip_offset"] > 247 :
    print("Ensure there are atleast 6 available IPs. Check ip_offset in config")
    return

  list_of_parameter_json_objects, ip_offset = get_list_of_parameter_json_objects(config)
  update_ip_offset_in_config(ip_offset, config_file_name)

  for parameter_json in list_of_parameter_json_objects:
    deploy_template(config, parameter_json)

def parseArguments():
    parser = argparse.ArgumentParser()

    # Optional arguments
    # parser.add_argument("-test", "--testDeploy", help="Test if python script is able to deploy resource group", type=bool, default=False)
    parser.add_argument('-testDeploy', action='store', nargs='*')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
  args = parseArguments()
  main(args)