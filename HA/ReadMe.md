Script to test AG feature (singlesubnet + multisubnet):
1. Authenticate using browser
2. Create resource group
3. Create Domain Controller, Virtual network
4. Create Subnets
5. Create Load balancer 
6. Create copy of singlesubnet and multisubnet runbook
7. Copy containers, templates with updated values
8. Start runbook jobs and open the job, used templates, used dcvm resource group in browser

Usage:
1. Run pip install -r dependencies.txt
2. Add password, connection_string values in config.json
3. python auto.py

![image](https://github.com/shiva08/utils/assets/7246619/a1eb8b01-b9fb-4cff-b078-8a5aca68bcf9)
