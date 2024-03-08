import webbrowser
from azure.mgmt.network.models import (
    LoadBalancer, FrontendIPConfiguration, Subnet, LoadBalancingRule, Probe, BackendAddressPool
)

edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))

class LoadBalancerHelper:
	def __init__(self, network_client):
		self.network_client = network_client

	def create_load_balancer(self, subscription_id, vnet_name, subnet_name, resource_group, location, load_balancer_name):
		print(f"creating load balancer {load_balancer_name}")
		subnet_info = self.network_client.subnets.get(resource_group, vnet_name, subnet_name)
		subnet_ref = subnet_info.id

		# Creating an internal Standard SKU load balancer
		async_lb_creation = self.network_client.load_balancers.begin_create_or_update(
			resource_group_name=resource_group,
			load_balancer_name=load_balancer_name,
			parameters=LoadBalancer(
				location=location,
				sku={'name': 'Standard'},
				frontend_ip_configurations=[
					FrontendIPConfiguration(
						name='myFrontendIPConfig',
						subnet=Subnet(id=subnet_ref)
					)
				],
				backend_address_pools=[
					BackendAddressPool(
						name='myBackendPool'
					)
				],
				load_balancing_rules=[
					LoadBalancingRule(
						name='myLBRule',
						frontend_ip_configuration=FrontendIPConfiguration(
							id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/frontendIPConfigurations/myFrontendIPConfig"
						),
						backend_address_pool=BackendAddressPool(
							id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/loadBalancers/{load_balancer_name}/backendAddressPools/myBackendPool"
						),
						protocol='Tcp',
						frontend_port=80,
						backend_port=80,
						enable_floating_ip=False,
						idle_timeout_in_minutes=4,
						load_distribution='Default'
					)
				],
				probes=[
					Probe(
						name='myHealthProbe',
						protocol='Tcp',
						port=80,
						interval_in_seconds=15,
						number_of_probes=4
					)
				]
			)
		)

		# Wait for the creation to complete
		lb_info = async_lb_creation.result()
