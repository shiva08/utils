import json
import re
import subprocess
from datetime import datetime


def update_datadisks(json_object, vm_array):
  for idx, vmname in enumerate(vm_array):
    json_object["parameters"]["dataDisks" + str(idx + 1)]["value"][0]["name"] = vmname + "_DataDisk_0"
    json_object["parameters"]["dataDisks" + str(idx + 1)]["value"][1]["name"] = vmname + "_DataDisk_1"

    json_object["parameters"]["dataDiskResources" + str(idx + 1)]["value"][0]["name"] = vmname + "_DataDisk_0"
    json_object["parameters"]["dataDiskResources" + str(idx + 1)]["value"][1]["name"] = vmname + "_DataDisk_1"

location = "westus"
password = ""  






params = json.load(open('parameters.json'))
template = json.load(open('template.json'))

file = open("..\\Images\\images_list.txt")
ip_offset = 0
vm_name_prefix = "shiva"
time_now = datetime.now()
rg_name  =  "{}{}{:02d}{:02d}{:02d}{:02d}".format('shivdeepwinrmimage-',
    time_now.year, time_now.month, time_now.day, time_now.hour, time_now.minute)

powershell_cmd = "New-AzResourceGroup -Name {resourceGroupName} -location {location}".format(resourceGroupName=rg_name, location = location)
result = subprocess.Popen(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", powershell_cmd],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
for line in file.readlines():
    ip_offset += 1  # IP for VM
    array = re.split(r"\s+", line.strip())
    array[1] = array[1].lower()

    # vm name can't be more than 15 chars
    # vm_name_prefix+=array[0]+array[1]

    # if not(array[1].startswith('sqldev') or array[1].startswith('enterprise')):
    #     continue

    vm_name = vm_name_prefix + str(ip_offset)

    params["parameters"]["virtualMachineName"]["value"]= vm_name
    params["parameters"]["virtualMachineName1"]["value"]= vm_name
    params["parameters"]["virtualMachineComputerName1"]["value"]= vm_name
    params["parameters"]["sqlVirtualMachineName"]["value"]= vm_name
    params["parameters"]["networkInterfaceName1"]["value"]=  vm_name + str(ip_offset)
    params["parameters"]["networkSecurityGroupName"]["value"]= vm_name +"-nsg"
    params["parameters"]["virtualNetworkName"]["value"]= vm_name+"-vnet"
    params["parameters"]["publicIpAddressName1"]["value"]= vm_name +"-ip"

    params["parameters"]["adminPassword"]["value"] = password


    vm_array = []
    vm_array += [vm_name]
    update_datadisks(params, vm_array)

    template["resources"][5]["properties"]["storageProfile"][
        "imageReference"] = {'publisher': 'microsoftsqlserver',
                             'offer': array[0],
                             'sku': array[1], 'version': 'latest'}
    t_n = 'template' + "_" + array[0] + "_" + array[1]
    f= open(t_n+'.json','w')
    json.dump(template, f, ensure_ascii=False, indent=4)
    f.close()

    p_n = 'parameter' + "_" + array[0] + "_" + array[1]

    f= open(p_n+'.json','w')
    json.dump(params, f, ensure_ascii=False, indent=4)
    f.close()

    powershell_cmd = "New-AzResourceGroupDeployment -DeploymentDebugLogLevel ResponseContent -Name {name} -ResourceGroupName {resourceGroupName} -TemplateFile {templateFile} -TemplateParameterFile {parameterFile} -verbose".format(name = t_n, resourceGroupName = rg_name, templateFile = t_n+".json", parameterFile = p_n+".json")

    print(powershell_cmd)
    result = subprocess.Popen(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", powershell_cmd], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    # print(result)


# Run this on Azure cloud shell

# $myAzureVMs | ForEach-Object -Parallel {
#     $out = Invoke-AzVMRunCommand `
#         -ResourceGroupName $_.ResourceGroupName `
#         -Name $_.Name  `
#         -CommandId 'RunPowerShellScript' `
#         -ScriptString 'Get-WSManInstance winrm/config/listener -Enumerate'
#     $a = @('HTTP','5985')
#     $flag = $null -ne ($a | ? { $out.Value[0].Message -match $_ })
#     $outs = $_.Name + " " + $flag.ToString()
#     Write-Output $outs
# }
