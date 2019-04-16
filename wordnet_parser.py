from nltk.corpus import wordnet as wn
def get_relations(termlist):
	final_list = []
	for term in termlist:
		for concept in wn.synsets(term):
			for instance in concept.hypernyms():
				instance_name,concept_name = instance.name().split('.')[0], concept.name().split('.')[0]
				# print(instance_name,concept_name)
				final_list.append([instance_name,concept_name])
	return final_list
print(get_relations(["security"]))