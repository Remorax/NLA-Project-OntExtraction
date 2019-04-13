from pronto_testing import *
node_list = []
child_dict = {}
node_info = {}
filename = 'Clustering_Results_modified.txt'
fp = open(filename,'r')
lines = fp.readlines()
for line in lines:
	x = line.strip('\n').split(' ')
	print(x)
	if (len(x)==3):
		node_list,child_dict,node_info = insert_relation(x[2],x[0],x[0],node_list,child_dict,node_info)
export_to_obo(node_list,child_dict,node_info,filename)