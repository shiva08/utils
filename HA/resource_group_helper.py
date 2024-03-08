class ResourceGroupHelper:
	def __init__(self, resource_client):
		self.resource_client = resource_client

	def get_resource_group_url(self, subscription_id, resource_group):
		url = f"https://ms.portal.azure.com/#@microsoft.onmicrosoft.com/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group}/overview"
		return url

	def create(self, resource_group, location):
		print(f"Creating resource group {resource_group}")
		self.resource_client.resource_groups.create_or_update(resource_group, {"location" : location})

	def delete(self, resource_group):
		delete_operation = self.resource_client.resource_groups.begin_delete(rg)
		# delete_operation.wait()
		print(f"Deleted resource group: {rg.name}")

	def delete_resource_group_list(self, resource_group_list):
		for resource_group in resource_group_list:
			self.delete(resource_group)
