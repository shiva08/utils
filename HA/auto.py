import webbrowser
import json
import time
from colorama import init, Fore, Back, Style
from azure.identity import InteractiveBrowserCredential
import azure.mgmt.automation as automation
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient

from config_helper import ConfigHelper
from resource_group_helper import ResourceGroupHelper
from storage_account_helper import StorageAccountHelper
from load_balancer_helper import LoadBalancerHelper
from subnet_helper import SubnetHelper
from runbook_helper import RunbookHelper
from dcvm_helper import DcvmHelper

init(autoreset=True)

edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

class Auto:
	def __init__(self, config):
		self.config = config
		self.credentials = None
		self.resource_client = None
		self.automation_client = None
		self.network_client = None
		self.storage_client = None
		self.dcvm_parameters = {}

	def authenticate(self):
		self.credentials = InteractiveBrowserCredential()
		token = self.credentials.get_token("https://management.azure.com/.default")
		self.config["bearer_token"] = token.token

	def init_clients(self):
		self.resource_client = ResourceManagementClient(self.credentials, self.config["subscription_id"])
		self.automation_client = automation.AutomationClient(self.credentials, self.config["subscription_id"])
		self.network_client = NetworkManagementClient(self.credentials, self.config["subscription_id"])
		self.storage_client = StorageManagementClient(self.credentials, self.config["subscription_id"])

	def init_helper_classes(self):
		self.resource_group_helper = ResourceGroupHelper(self.resource_client)
		self.subnet_helper = SubnetHelper(self.network_client)
		self.storage_account_helper = StorageAccountHelper(self.storage_client)
		self.load_balancer_helper = LoadBalancerHelper(self.network_client)
		self.runbook_helper = RunbookHelper(self.automation_client)
		self.dcvm_helper = DcvmHelper(self.resource_client, self.resource_group_helper)

	def update_dcvm_params(self, file):
		with open(file, 'r') as f:
			g = json.load(f)
		g["parameters"]["location"]["value"] = self.config["dcvm"]["location"]
		g["parameters"]["adminPassword"]["value"] = self.config["dcvm"]["password"]
		g["parameters"]["domainAdminPassword"]["value"] = self.config["dcvm"]["password"]
		g["parameters"]["SQLAccountPassword"]["value"] = self.config["dcvm"]["password"]
		g["parameters"]["sqlAuthenticationPassword"]["value"] = self.config["dcvm"]["password"]

		with open(file, 'w') as f:
			f.write(json.dumps(g, indent=4))

	def create_prerequisites(self):
		print(Fore.YELLOW + "Creating prerequisites")

		if self.config["dcvm"]["create"]:
			self.resource_group_helper.create(self.config["dcvm"]["resource_group"], self.dcvm_parameters["parameters"]["location"]["value"])
			self.dcvm_helper.deploy_dcvm(self.config["subscription_id"], self.config["dcvm"]["resource_group"], self.config["dcvm"]["deployment_name"], self.config["dcvm"]["template_file_path"], self.config["dcvm"]["parameters_file_path"] )

		if self.config["multisubnet"]:
			for i, subnet in enumerate(self.config["subnets"]):
				self.subnet_helper.create(self.config["subscription_id"], self.config["dcvm"]["resource_group"], self.dcvm_parameters["parameters"]["virtualNetworkName"]["value"], subnet, self.dcvm_parameters["parameters"]["networkSecurityGroupName"]["value"], f"10.0.{i+1}.0/24" )

		self.storage_account_helper.create_storage_account(self.config["subscription_id"], self.config["storage_account"]["name"], self.config["dcvm"]["resource_group"], self.dcvm_parameters["parameters"]["location"]["value"], self.config["storage_account"]["min_tls"])
		
		if self.config["singlesubnet"]:
			self.load_balancer_helper.create_load_balancer(self.config["subscription_id"], self.dcvm_parameters["parameters"]["virtualNetworkName"]["value"], self.dcvm_parameters["parameters"]["subnetName"]["value"], self.config["dcvm"]["resource_group"], self.dcvm_parameters["parameters"]["location"]["value"], self.config["loadbalancer"]["name"])

	def fetch_dcvm_parameters(self):
		if not self.dcvm_parameters : 
			with open(self.config["dcvm"]["parameters_file_path"], 'r') as file:
				self.dcvm_parameters = json.load(file)

	def create(self):
		self.authenticate()
		self.init_clients()
		self.init_helper_classes()
		self.fetch_dcvm_parameters()
		self.create_prerequisites()

		if self.config["multisubnet"] :
			print(Fore.GREEN + "Multisubnet setup")

			self.storage_account_helper.copy_container(self.config["automation"]["multisubnet"]["storage_account"]["name"], self.config["automation"]["multisubnet"]["storage_account"]["connection_string"], self.config["automation"]["multisubnet"]["storage_account"]["container"]["existing"], self.config["automation"]["multisubnet"]["storage_account"]["container"]["new"], self.dcvm_parameters["parameters"]["location"]["value"], self.dcvm_parameters["parameters"]["virtualNetworkName"]["value"], self.config["dcvm"]["resource_group"], self.config["storage_account"]["name"], self.config["dcvm"]["resource_group"], self.config["subnets"], self.config["dcvm"]["password"], self.config["automation"]["multisubnet"]["runbook"]["rg_prefix"])
			self.runbook_helper.copy_runbook(automation_location = self.config["automation"]["location"], subscription_id = self.config["subscription_id"], resource_group = self.config["automation"]["resource_group"], automation_account_name = self.config["automation"]["account"], runbook_name = self.config["automation"]["multisubnet"]["runbook"]["existing"], new_runbook = self.config["automation"]["multisubnet"]["runbook"]["new"], runbook_type = self.config["automation"]["multisubnet"]["runbook"]["type"], bearer_token = self.config["bearer_token"], multisubnet = True)
			self.runbook_helper.publish_runbook(self.config["subscription_id"], self.config["automation"]["resource_group"], self.config["automation"]["account"], self.config["automation"]["multisubnet"]["runbook"]["new"], self.config["bearer_token"])
			time.sleep(60*3)
			self.runbook_helper.start_runbook(self.config["subscription_id"], self.config["automation"]["resource_group"], self.config["automation"]["account"], self.config["automation"]["multisubnet"]["runbook"]["new"], {"container" : self.config["automation"]["multisubnet"]["storage_account"]["container"]["new"]} , self.config["automation"]["multisubnet"]["job_name"])

		if self.config["singlesubnet"] :
			print(Fore.GREEN + "Singlesubnet setup")

			self.storage_account_helper.copy_template(self.config["automation"]["singlesubnet"]["storage_account"]["name"], self.config["automation"]["singlesubnet"]["storage_account"]["connection_string"], self.config["automation"]["singlesubnet"]["storage_account"]["container"]["existing"], self.config["automation"]["singlesubnet"]["storage_account"]["container"]["template"]["existing"], self.config["automation"]["singlesubnet"]["storage_account"]["container"]["template"]["new"], self.dcvm_parameters["parameters"]["virtualNetworkName"]["value"], self.dcvm_parameters["parameters"]["subnetName"]["value"], self.config["loadbalancer"]["name"], self.dcvm_parameters["parameters"]["location"]["value"], self.dcvm_parameters["parameters"]["VirtualMachineList"]["value"])
			self.runbook_helper.copy_runbook(automation_location = self.config["automation"]["location"], subscription_id = self.config["subscription_id"], resource_group = self.config["automation"]["resource_group"], automation_account_name = self.config["automation"]["account"], runbook_name = self.config["automation"]["singlesubnet"]["runbook"]["existing"], new_runbook = self.config["automation"]["singlesubnet"]["runbook"]["new"], runbook_type = self.config["automation"]["singlesubnet"]["runbook"]["type"], bearer_token = self.config["bearer_token"], multisubnet = False, singlesubnet = True, single_rg = self.config["dcvm"]["resource_group"], single_storage = self.config["storage_account"]["name"], single_location = self.dcvm_parameters["parameters"]["location"]["value"], single_dcvm = self.dcvm_parameters["parameters"]["virtualMachineName"]["value"] , single_vm_list = self.dcvm_parameters["parameters"]["VirtualMachineList"]["value"], single_new_template = self.config["automation"]["singlesubnet"]["storage_account"]["container"]["template"]["new"])
			self.runbook_helper.publish_runbook(self.config["subscription_id"], self.config["automation"]["resource_group"], self.config["automation"]["account"], self.config["automation"]["singlesubnet"]["runbook"]["new"], self.config["bearer_token"])
			time.sleep(60*3)
			self.runbook_helper.start_runbook(self.config["subscription_id"], self.config["automation"]["resource_group"], self.config["automation"]["account"], self.config["automation"]["singlesubnet"]["runbook"]["new"], 			
				self.config["automation"]["singlesubnet"]["runbook"]["parameters"], self.config["automation"]["singlesubnet"]["job_name"])

# Don't change config["name"]
# Remember to delete the created resources, deletion isn't automated since there's high chance of deleting other's resources
generate_new_config = False
config_file = "config.json"
config_helper_obj = ConfigHelper(config_file)
config_helper_obj.read_config()
if generate_new_config:
	config_helper_obj.update_config()
config = config_helper_obj.get_config()

auto_obj = Auto(config)
auto_obj.update_dcvm_params(config["dcvm"]["parameters_file_path"])
auto_obj.create()




