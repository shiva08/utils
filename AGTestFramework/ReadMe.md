Description
1. Deploy end to end availability group with multiple images, skus
2. Handles parallel deployments
3. After finishing deployments, ip_offset (which is used for new ips, vmnames, disks, etc) will be updated in the config 

Prerequisites
1. Ensure you have a valid domain controller, virtual network and necessary subnets. DNS server of vnet should be pointing to dcvm
2. Ensure the vmnames, IPs don't clash with existing resources
3. Number of IPs required = (Number of image tests) * (Number of subnets + 1 ) 

Instructions
1. Refer config.json for location of files
2. Create/Use your own resource group. Add this info in config: 
    "resource_group": { "name" : "snutheti_net6_ha_tests", "create" : true }
3. To test the environment - create resource group: python run.py -testDeploy
4. To execute the tests : python run.py

Tracking Deployment status
1. Sample deployment name : shiva_sql2016sp3-ws2019_enterprise_20230524194445576547 at https://ms.portal.azure.com/#@microsoft.onmicrosoft.com/resource/subscriptions/0009fc4d-e310-4e40-8e63-c48a23e9cdc1/resourceGroups/shivdeeptestframes/deployments
2. Format : name_image_sku_yyyymmddhhmmssmicrosecond

Template used: AG End to end deployment template from production downloaded on 05/24/2023

Further reading
1. https://github.com/microsoft/tigertoolbox/tree/master/AzureSQLVM/e2e-ag-setup
2. https://msdata.visualstudio.com/Database%20Systems/_wiki/wikis/Database%20Systems.wiki/50800/Multi-subnet-AG-setup

Next steps
1. Incorporate AG with single subnet/load balancer 
2. Automate tests for AG provisioning with powershell

Problems faced
1. To maintain uniqueness for parallel deploymnents: ARM template resource ids/deployment names are not unique by design. I am not sure why this was designed like this. This is only useful for update scenarios which seem very few compared to create ones 

