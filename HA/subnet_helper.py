class SubnetHelper:
	def __init__(self, network_client):
		self.network_client = network_client

	def create(self, subscription_id, resource_group, vnet, subnet, nsg, address_prefix):
		print(f"creating subnet {subnet}")
		try:
			async_subnet_creation = self.network_client.subnets.begin_create_or_update(
				resource_group,
				vnet,
				subnet,
				{
					"address_prefix": address_prefix,
					"network_security_group": {
						"id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkSecurityGroups/{nsg}"
					}
				}
			)
			subnet_info = async_subnet_creation.result()
		except Exception as e:
			print(e)
