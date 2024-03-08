import json
import webbrowser

edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
class DcvmHelper:
	def __init__(self, resource_client, resource_group_helper):
		self.resource_client = resource_client
		self.resource_group_helper = resource_group_helper

	def deploy_template(self,resource_group, deployment_name, template_file_path, parameters_file_path):
		with open(template_file_path, "r") as template_file:
			template = json.load(template_file)

		with open(parameters_file_path, "r") as parameters_file:
			parameters = json.load(parameters_file)

		deployment_properties = {
			"mode": "Incremental",
			"template": template,
			"parameters": parameters["parameters"]
		}

		deployment_async_operation = self.resource_client.deployments.begin_create_or_update(
			resource_group, deployment_name, {'properties': deployment_properties,'tags': []}
		)
		deployment_async_operation.wait()

	def deploy_dcvm(self, subscription_id, resource_group, deployment_name, template_file_path, parameters_file_path ):
		print("Deploying dcvm, vnet, vms")
		self.deploy_template(resource_group, deployment_name, template_file_path, parameters_file_path)
		link = self.resource_group_helper.get_resource_group_url(subscription_id, resource_group)
		try:
			webbrowser.get('edge').open(link)
		except Exception as e:
			print(f"An error occurred: {e}")

# credentials = InteractiveBrowserCredential()
# resource_client = ResourceManagementClient(credentials, subscription_id)
# resource_group_helper = ResourceGroupHelper(resource_client)

# obj = DcvmHelper(resource_client, resource_group_helper)
# obj.deploy_dcvm(subscription_id, resource_group, deployment_name, template_file_path, parameters_file_path )
