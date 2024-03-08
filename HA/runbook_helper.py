import re
import requests
import json
import time
import webbrowser

edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

class RunbookHelper:
	def __init__(self, automation_client):
		self.automation_client = automation_client

	def get_runbook_job_url(self, automation_account_name, subscription_id, resource_group, runbook_name, job_name):
		url = f"https://ms.portal.azure.com/#view/Microsoft_Azure_Automation/JobDashboardBladeV2/jobResourceId/%2Fsubscriptions%2F{subscription_id}%2FresourceGroups%2F{resource_group}%2Fproviders%2FMicrosoft.Automation%2FautomationAccounts%2F{automation_account_name}%2FJobs%2F{job_name}/runbookResourceId/%2Fsubscriptions%2F{subscription_id}%2FresourceGroups%2F{resource_group}%2Fproviders%2FMicrosoft.Automation%2FautomationAccounts%2F{automation_account_name}%2Frunbooks%2F{runbook_name}"
		return url

	def fetch_runbook_content(self, subscription_id, resource_group, automation_account_name, new_runbook, bearer_token):
		headers = {"Authorization": f"Bearer {bearer_token}"} 
		url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Automation/automationAccounts/{automation_account_name}/runbooks/{new_runbook}/content?api-version=2023-11-01"
		response = requests.get(url, headers=headers)
		return response.text

	def update_runbook(self , content, subscription_id, resource_group, automation_account_name, runbook, bearer_token):
		if runbook =="SQLVMAlwaysOnRunner" or runbook == "MultiSubnetHARunner":
			print("Can't update runbooks created by ha team")
			exit()
		url = f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Automation/automationAccounts/{automation_account_name}/runbooks/{runbook}/draft/content?api-version=2023-11-01'

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f'Bearer {bearer_token}'
		}
		response = requests.put(url, headers=headers, data=content)
		time.sleep(10)


	def publish_runbook(self, subscription_id, resource_group, automation_account_name, runbook, bearer_token):
		url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Automation/automationAccounts/{automation_account_name}/runbooks/{runbook}/publish?api-version=2023-11-01"

		headers = {
			'Authorization': f'Bearer {bearer_token}',
			'Content-Type': 'application/json'
		}

		response = requests.post(url, headers=headers)
		if response.status_code == 200 or response.status_code == 202 :
			print(f"Runbook {runbook} has been published.")
		else:
			print(f"Failed to publish runbook. Status code: {response.status_code}.")
		time.sleep(10)

	def create_runbook(self, content, subscription_id, resource_group, automation_account_name, runbook, runbook_type, automation_location, bearer_token):
		# can't create a runbook with content without public url
		# -> create runbook, update draft and publish
		print(f"Creating runbook {runbook}")
		if runbook == "MultiSubnetHARunner" or runbook == "SQLVMAlwaysOnRunner":
			print("Can't create/update exiting runners" )
			exit()
		headers = {"Authorization": f"Bearer {bearer_token}", "Content-Type" :"application/json"} 
		url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Automation/automationAccounts/{automation_account_name}/runbooks/{runbook}?api-version=2023-11-01"
		body = {

					"name": runbook,
					"location": automation_location,
					"properties": {
						"logVerbose": False,
						"logProgress": True,
						"runbookType": runbook_type,
						"description": "Description of the new Runbook",
						"logActivityTrace": 1,
						"draft": {
							"inEdit": False
						}
					}
				}
		response = requests.put(url, headers=headers, data=json.dumps(body))
		time.sleep(10)
		self.update_runbook(content, subscription_id, resource_group, automation_account_name, runbook, bearer_token)

	def start_runbook(self, subscription_id, resource_group, automation_account_name, runbook_name, parameters, job_name):
		print(f"starting runbook {runbook_name}")
		try:
			response = self.automation_client.job.create(
				resource_group_name=resource_group,
				automation_account_name=automation_account_name,
				job_name= job_name,
				parameters={
					"properties": {
						"parameters": parameters,
						"runOn": "",
						"runbook": {
							"name": runbook_name
							}
						}
					}
			) 
		except Exception as e:
			print(e)
		link = self.get_runbook_job_url(automation_account_name, subscription_id, resource_group, runbook_name, job_name)
		webbrowser.get('edge').open(link)

	def copy_runbook(self, automation_location, subscription_id, resource_group, automation_account_name, runbook_name, new_runbook, runbook_type, bearer_token , multisubnet = False, singlesubnet = False, single_rg = None, single_storage = None, single_location = None, single_dcvm = None, single_vm_list = None, single_new_template = None ):
		if new_runbook == "MultiSubnetHARunner" or new_runbook == "SQLVMAlwaysOnRunner":
			print("can't update existing runners")
			exit()
		content = self.fetch_runbook_content(subscription_id, resource_group, automation_account_name, runbook_name, bearer_token)
		if singlesubnet:
			vm_list = single_vm_list.split(',')

			new_string = '@("' + '", "'.join(vm_list) + '")'
			replacements = {
				r'\$ResourceGroupName = "(.*?)";': f'$ResourceGroupName = "{single_rg}";',
				r'\$StorageAccntName = "(.*?)";': f'$StorageAccntName = "{single_storage}";',
				r'\$Location = "(.*?)";': f'$Location = "{single_location}";',
				r'\$dcvm = "(.*?)";': f'$dcvm = "{single_dcvm}";',
				r'\$SqlVmLists = "(.*?)";': f'$SqlVmLists = "{new_string}";',
				r'-TemplateUri (.*?) `' : f'-TemplateUri "https://agtemplatestorage.blob.core.windows.net/templates/{single_new_template}" `'
			}
			for pattern, replacement in replacements.items():
				content = re.sub(pattern, replacement , content)
		self.create_runbook(content, subscription_id, resource_group, automation_account_name, new_runbook, runbook_type, automation_location, bearer_token)
