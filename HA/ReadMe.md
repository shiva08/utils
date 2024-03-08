Script to test AG feature (singlesubnet + multisubnet):
1. Authenticate using browser
2. Create resource group
3. Create Domain Controller, Virtual network
4. Create Subnets
5. Create Load balancer 
6. Create copy of singlesubnet and multi subnet runbook
7. Copy containers, templates with updated values
8. Start runbook jobs and open the job, used templates, used dcvm resource group in browser

Usage:
Run pip install -r dependencies.txt
Add password, connection_string values in config.json
