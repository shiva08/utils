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

Screenshots:
![image](https://github.com/shiva08/utils/assets/7246619/d4df83f1-5d08-4734-acc3-043eeb3e5764)

![image](https://github.com/shiva08/utils/assets/7246619/a1eb8b01-b9fb-4cff-b078-8a5aca68bcf9)

![image](https://github.com/shiva08/utils/assets/7246619/fbd882c9-f94f-400e-90f6-0b36f2f12b74)

![image](https://github.com/shiva08/utils/assets/7246619/90f87477-7c79-4302-a525-0985d84f6171)

![image](https://github.com/shiva08/utils/assets/7246619/f68bd8f6-1db7-445f-b78e-5d5567f5ab4a)

![image](https://github.com/shiva08/utils/assets/7246619/7d553585-c9d7-47e0-8c93-df8163d6e172)

![image](https://github.com/shiva08/utils/assets/7246619/43c20a00-4c3d-4cae-a384-a3e7d1d518ee)
