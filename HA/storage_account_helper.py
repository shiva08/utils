from azure.storage.blob import BlobServiceClient
import webbrowser
import json
import urllib

edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

class StorageAccountHelper:
	def __init__(self, storage_client):
		self.storage_client = storage_client


	def check_container_exists(self, connection_string, container_name):
		blob_service_client = BlobServiceClient.from_connection_string(connection_string)
		container_client = blob_service_client.get_container_client(container_name)

		try:
			if container_client.exists():
				print(f"Container '{container_name}' exists.")
				return True
			else:
				print(f"Container '{container_name}' does not exist.")
				return False
		except Exception as e:
			print(f"An error occurred: {e}")
			return False

	def create_storage_account(self, credentials, storage_account_name, resource_group, location, min_tls = "TLS1_0"):
		print(f"Creating storage account {storage_account_name}")
		if storage_account_name == "agtemplatestorage" or storage_account_name == "storagemultisubnet" : 
			print("Don't override storage accounts")
			exit()
		availability_result = self.storage_client.storage_accounts.check_name_availability(
			{ "name": storage_account_name }
		)

		if not availability_result.name_available:
			print(f"Storage name {storage_account_name} is already in use. Try another name.")
		else:
			poller = self.storage_client.storage_accounts.begin_create(resource_group, storage_account_name,
				{
					"location" : location,
					"kind": "StorageV2",
					"sku": {"name": "Standard_LRS"},
					"minimum_tls_version": min_tls
				}
			)

			# Long-running operations return a poller object; calling poller.result()
			# waits for completion.
			account_result = poller.result()

			print(f"Storage account '{storage_account_name}' created successfully.")


	def get_storage_account_id(self, storage_account):
		for account in self.storage_client.storage_accounts.list():
			if account.name == storage_account:
				return account.id

	def get_container_url(self, storage_account, container):
		account_id = self.get_storage_account_id(storage_account)
		a_encoded = urllib.parse.quote(account_id, safe='')
		url = f"https://ms.portal.azure.com/#view/Microsoft_Azure_Storage/ContainerMenuBlade/~/overview/storageAccountId/{a_encoded}/path/{container}"
		return url

	def get_template_url(self, storage_account, container, template):
		account_id = self.get_storage_account_id(storage_account)
		a_encoded = urllib.parse.quote(account_id, safe='')
		path = f"{container}/{template}"
		path_encoded = urllib.parse.quote(path, safe='')

		url = f"https://ms.portal.azure.com/#view/Microsoft_Azure_Storage/BlobPropertiesBladeV2/storageAccountId/{a_encoded}/path/{path_encoded}/isDeleted~/false/tabToload~/0"
		return url

	def update_ag_parameters_for_new_runbook(self, blob_json, ag_location, ag_vnet, ag_vnet_rg, ag_storage_account, ag_storage_account_rg, ag_subnets ):
		blob_json["parameters"]["location"]["value"] = ag_location
		blob_json["parameters"]["existingVirtualNetworkName"]["value"]=ag_vnet
		blob_json["parameters"]["existingVirtualNetworkResourceGroupName"]["value"]=ag_vnet_rg
		blob_json["parameters"]["storageAccountName"]["value"]=ag_storage_account
		blob_json["parameters"]["storageAccountResourceGroup"]["value"]=ag_storage_account_rg
		blob_json["parameters"]["subnetNames"]["value"] = ag_subnets

	def copy_container(self, storage_account_name, connection_string, source_container_name, destination_container_name, ag_location, ag_vnet, ag_vnet_rg, ag_storage_account, ag_storage_account_rg, ag_subnets, ag_password = None, multi_rg_prefix = ""):
		print(f"Copying container {source_container_name} to {destination_container_name}")
		if destination_container_name == "runner" :
			print("don't override runner container")
			exit()

		if self.check_container_exists(connection_string, destination_container_name):
			return
		blob_service_client = BlobServiceClient.from_connection_string(connection_string)

		destination_container_client = blob_service_client.get_container_client(destination_container_name)
		if not destination_container_client.exists():
		    destination_container_client.create_container()

		source_container_client = blob_service_client.get_container_client(source_container_name)
		blob_list = source_container_client.list_blobs()

		# Copy each blob to the destination container
		for blob in blob_list:
			blob_client = source_container_client.get_blob_client(blob.name)
			destination_blob_client = destination_container_client.get_blob_client(blob.name)
			content = json.loads(blob_client.download_blob().readall().decode('utf-8'))
			if(blob.name == "config.json"):
				content["rg_prefix"] = multi_rg_prefix
				content["password"] = ag_password
			elif(blob.name == "ag-parameters.json"):
			 	self.update_ag_parameters_for_new_runbook(content, ag_location, ag_vnet, ag_vnet_rg, ag_storage_account, ag_storage_account_rg, ag_subnets )
			content = json.dumps(content, indent = 4)
			destination_blob_client.upload_blob(content, overwrite=False)

		webbrowser.get('edge').open(self.get_container_url(storage_account_name, destination_container_name))

	def copy_template(self, storage_account_name, connection_string, container, source_template, destination_template, single_vnet, single_subnet, single_lb, single_location, single_vm_list):
		print(f"Copying template {source_template} to {destination_template}")
		if destination_template == "AGListenerTemplate" :
			print("don't override runner template")
			exit()

		blob_service_client = BlobServiceClient.from_connection_string(connection_string)
		container_client = blob_service_client.get_container_client(container)
		blob_list = container_client.list_blobs()

		# Copy each blob to the destination container
		for blob in blob_list:
			blob_client = container_client.get_blob_client(blob.name)
			destination_blob_client = container_client.get_blob_client(destination_template)

			if(blob.name == source_template):
				a= blob_client.download_blob().readall()
				b = a.decode('utf-8')
				c = json.loads(b)
				c["parameters"]["existingVnet"]["defaultValue"] = single_vnet
				
				c["parameters"]["existingSubnet"]["defaultValue"] = single_subnet

				c["parameters"]["existingInternalLoadBalancer"]["defaultValue"] = single_lb
				c["parameters"]["Location"]["defaultValue"] = single_location
				c["parameters"]["existingVmList"]["defaultValue"] = single_vm_list
				modified_blob_str = json.dumps(c, indent = 4)

				try:
					destination_blob_client.upload_blob(modified_blob_str, overwrite=False)
				except Exception as e:
					print(e)
				break
		webbrowser.get('edge').open(self.get_template_url(storage_account_name, container, destination_template))

	def delete_container(self, connection_string, container_name):
		print(f"Deleting container {container_name}")
		blob_service_client = BlobServiceClient.from_connection_string(connection_string)
		try:
			container_client = blob_service_client.get_container_client(container_name)
			container_client.delete_container()
			print(f"Container '{container_name}' deleted successfully.")
		except ResourceNotFoundError:
			print(f"Container '{container_name}' not found.")
		except Exception as e:
			print(f"An error occurred: {e}")

	def delete_blob(self, connection_string, container_name, blob_name ):

		blob_service_client = BlobServiceClient.from_connection_string(connection_string)

		try:
			blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
			blob_client.delete_blob()
			print(f"Blob '{blob_name}' in container '{container_name}' deleted successfully.")
		except ResourceNotFoundError:
			print(f"Blob '{blob_name}' in container '{container_name}' not found.")
		except Exception as e:
			print(f"An error occurred: {e}")
