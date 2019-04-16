from SPARQLWrapper import SPARQLWrapper, JSON
def get_terms(termlist):
	final_list = []
	for term in termlist:
		print(term)
		sparql = SPARQLWrapper("http://dbpedia.org/sparql")
		sparql.setQuery("""SELECT * WHERE {<http://dbpedia.org/resource/"""+term + """> <http://purl.org/dc/terms/subject> ?categories .}""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		# print(term)
		for result in results["results"]["bindings"]:
			res = result["categories"]["value"]
			name = res.split(':')[-1]
			# print(name)
			final_list.append([name,term])
		# print(results)
	return final_list
