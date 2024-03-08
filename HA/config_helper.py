import json
from datetime import datetime

class ConfigHelper:
	def __init__(self, config_file):
		self.config = None
		self.config_file = config_file

	def get_config(self):
		return self.config

	def append_name(self, str1):
		return self.config["name"] + datetime.today().strftime('%m%d%H%M') + str1[14:]

	def update_config(self):
		# all names are of autoha03071910 format - 6 digits + 8 mmddhhminmin
		self.config["dcvm"]["resource_group"] = self.append_name(self.config["dcvm"]["resource_group"])
		self.config["dcvm"]["deployment_name"] = self.append_name(self.config["dcvm"]["deployment_name"])  

		self.config["storage_account"]["name"] = self.append_name(self.config["storage_account"]["name"])
		self.config["loadbalancer"]["name"] = self.append_name(self.config["loadbalancer"]["name"])
		self.config["automation"]["singlesubnet"]["runbook"]["new"] = self.append_name(self.config["automation"]["singlesubnet"]["runbook"]["new"]) 
		self.config["automation"]["singlesubnet"]["job_name"] = self.append_name(self.config["automation"]["singlesubnet"]["job_name"])
		self.config["automation"]["singlesubnet"]["storage_account"]["container"]["template"]["new"] = self.append_name(self.config["automation"]["singlesubnet"]["storage_account"]["container"]["template"]["new"])

		self.config["automation"]["multisubnet"]["runbook"]["new"] = self.append_name(self.config["automation"]["multisubnet"]["runbook"]["new"]) 
		self.config["automation"]["multisubnet"]["job_name"] = self.append_name(self.config["automation"]["multisubnet"]["job_name"])
		self.config["automation"]["multisubnet"]["storage_account"]["container"]["new"] = self.append_name(self.config["automation"]["multisubnet"]["storage_account"]["container"]["new"])

		self.config["automation"]["multisubnet"]["runbook"]["rg_prefix"] = self.append_name(self.config["automation"]["multisubnet"]["runbook"]["rg_prefix"] )

		with open(self.config_file, 'w') as f:
			f.write(json.dumps(self.config, indent=4))

	def read_config(self):
		f = open(self.config_file,'r')
		self.config = json.loads(f.read())
		f.close()
