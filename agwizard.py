import xml.etree.ElementTree as ET
import json
import os

def get_bool(f):
	if f.lower()=="true":
		return True 
	elif f.lower()=="false":
		return False 

def write_correct_json(a,sql):
	for fi in sql:
		try:
			with open(a+"\\"+fi, 'w', encoding='utf-8') as f:
			    json.dump(sql[fi], f, ensure_ascii=False, indent=2)
		except Exception as e:
			print(e)
def fix_config_files(a,b, flags_file_path):
	sql = {}
	compute = {}

	flags_file = open(flags_file_path,"r")
	flags_from_file =[a.rstrip() for a in flags_file.readlines()]
	flags_file.close()

	for fi in list(set(os.listdir(b))&set(os.listdir(a))):
		if fi!="default.json":
			sql[fi]=json.load(open(a+"\\"+fi,"r"))
			compute[fi]=json.load(open(b+"\\"+fi,"r"))

	l=[]
	for p in sql:
		flag_keys = []
		for flag in sql[p].keys():
			if flag=="storageEndpointSuffix":
				sql[p][flag] = compute[p][flag][1:]
			else:

				if type(sql[p][flag])==str or type(sql[p][flag])==bool:
					if flag in compute[p]["features"]:
						flag_keys+=[flag]
						print(p + " " + flag)


					else:
						if flag in compute[p]:
							if (compute[p][flag]== sql[p][flag]):
								pass
							else:
								if compute[p][flag]=="true" or compute[p][flag]=="false":
									sql[p][flag] = get_bool(compute[p][flag]) 
								else:
									sql[p][flag] = compute[p][flag]

						else:
							l+=[str(flag) +"  " + p +"  "+str(sql[p][flag])]

		for d in flag_keys:
			del sql[p][d]
			sql[p]["features"][d] = get_bool(compute[p]["features"][d]) 

		for ab in (set(sql[p]["features"]) | set(flags_from_file)):
			if ab!="regionSegments":
				cd = ab.lower()
				if ab in compute[p]["features"]:
					sql[p]["features"][ab] = get_bool(compute[p]["features"][ab])
				elif cd in compute[p]["features"]:
					sql[p]["features"][ab] = get_bool(compute[p]["features"][cd])
				else:
					print("flag not present in compute")
					print(ab)
					print(p)



	print("......")
	# print(l)
	write_correct_json(a,sql)

def remove_duplicates_in_xml(file):

	tree = ET.parse(file)
	root = tree.getroot()
	b = set()
	for movie in root.findall('data'):
	    if movie.attrib['name'] in b:
	    	root.remove(movie)
	    else:
	    	b.add(movie.attrib['name'])
	tree.write("outs.xml")

def find_all_fx_controls(file):

	c = open(file,'r')
	for line in c.readlines():
	    # print(line)
	    if "declare module " in line:
	        print(line)

file = "C:\\Users\\snutheti\\work\\IbizaSqlPortal\\Source\\WebRole\\Client\\SqlVirtualMachine\\SqlVirtualMachineResources.resx"
file2 = "C:\\Users\\snutheti\\work\\IbizaSqlPortal\\Source\\WebRole\\Definitions\\Fx.d.ts"
a = "C:\\Users\\snutheti\\work\\IbizaSqlPortal\\Source\\WebRole\\Content\\Config"
b = "C:\\Users\\snutheti\\work\\AzureUX-IaaSExp\\src\\src\\Ux\\Extensions\\Compute\\Content\\Config"
flags_file = "C:\\Users\\snutheti\\Desktop\\flags.txt"

# find_all_fx_controls(file2)
# remove_duplicates_in_xml(file)
fix_config_files(a,b,flags_file)
