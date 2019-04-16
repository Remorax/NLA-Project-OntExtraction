#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
from nltk.parse import stanford
import nltk
from itertools import chain

os.environ['STANFORD_PARSER'] = '/home/vivek/nltk/jars/stanford-parser.jar'
os.environ['STANFORD_MODELS'] = '/home/vivek/nltk/jars/stanford-parser-3.7.0-models.jar'


# In[2]:


# Dependency Tree
from nltk.parse.stanford import StanfordDependencyParser
dep_parser=StanfordDependencyParser(model_path="/home/vivek/nltk/jars/englishPCFG.ser.gz")


# In[3]:


def lca(tree, index1, index2):
    node = index1
    path1 = []
    path2 = []
    path1.append(index1)
    path2.append(index2)
    while(node != tree.root):
        node = tree.nodes[node['head']]
        path1.append(node)
    node = index2
    while(node != tree.root):
        node = tree.nodes[node['head']]
        path2.append(node)
    for l1, l2 in zip(path1[::-1],path2[::-1]):
        if(l1==l2):
            temp = l1
    return temp


# In[4]:


def path_lca(tree, node, lca_node):
    path = []
    path.append(node)
    while(node != lca_node):
        node = tree.nodes[node['head']]
        path.append(node)
    return path


# In[5]:


def seq(lca):
    l=[lca]
    for key in tree.nodes[lca]['deps']:
        for i in tree.nodes[lca]['deps'][key]:
            l.extend(seq(i))
    return l


# In[ ]:





# In[6]:


import _pickle 
f = open('../data/training_data', 'rb')
sentences, e1, e2 = _pickle.load(f)
f.close()


# In[7]:


sentences[7588] = 'The reaction mixture is kept in the dark at room temperature for 1.5 hours .'
sentences[2608] = "This strawberry sauce has about a million uses , is freezer-friendly , and is so much better than that jar of Smuckers strawberry sauce that you 've had sitting in your fridge since that time you made banana splits 1.5 years ago ."


# In[8]:


# sentences[2590] = "The pendant with the bail measure 1.25'' ."
# sentences[2664] = "The cabinet encloses a 6.5 inch cone woofer , 4 inch cone midrange , and a 0.86 inch balanced dome tweeter ."


# In[9]:


length = len(sentences)


# In[10]:


words_seq = []
pos_tags_seq = []
deps_seq = []
word_path1 = []
word_path2 = []
dep_path1 = []
dep_path2 = []
pos_tags_path1 = []
pos_tags_path2 = []
childs_path1 = []
childs_path2 = []
pos_path1 = []
pos_path2 = []
for i in range(length):
    word_path1.append(0)
    word_path2.append(0)
    dep_path1.append(0)
    dep_path2.append(0)
    pos_tags_path1.append(0)
    pos_tags_path2.append(0)
    words_seq.append(0)
    pos_tags_seq.append(0)
    deps_seq.append(0)
    childs_path1.append(0)
    childs_path2.append(0)
    pos_path1.append(0)
    pos_path2.append(0)


# In[11]:


for i in range(length):
    try:
        parse_tree = dep_parser.raw_parse(sentences[i])
        for trees in parse_tree:
            tree = trees
            
        word2pos = dict((tree.nodes[k]['address'], j) for k,j in zip(tree.nodes, range(len(tree.nodes))))
        pos2word = dict((j, tree.nodes[k]['address']) for k,j in zip(tree.nodes, range(len(tree.nodes))))

        pos_tags_seq[i] = [tree.nodes[k]['tag'] for k in tree.nodes][1:]
        words_seq[i] = [tree.nodes[k]['word'] for k in tree.nodes][1:]
        deps_seq[i] = [tree.nodes[k]['rel'] for k in tree.nodes][1:]
        
        node1 = tree.nodes[e1[i]+1]
        node2 = tree.nodes[e2[i]+1]
        if node1['address']!=None and node2['address']!=None:
            print(i, "success")
            lca_node = lca(tree, node1, node2)
            path1 = path_lca(tree, node1, lca_node)
            path2 = path_lca(tree, node2, lca_node)[:-1]

            word_path1[i] = [p["word"] for p in path1]
            word_path2[i] = [p["word"] for p in path2]
            dep_path1[i] = [p["rel"] for p in path1]
            dep_path2[i] = [p["rel"] for p in path2]
            pos_tags_path1[i] = [p["tag"] for p in path1]
            pos_tags_path2[i] = [p["tag"] for p in path2]
            
            pos_path1[i] = [word2pos[node['address']] for node in path1]
            pos_path2[i] = [word2pos[node['address']] for node in path2]
            childs = [sorted(chain.from_iterable(node['deps'].values())) for node in path1]
            childs_path1[i] = [[word2pos[c] for c in child] for child in childs]
            childs = [sorted(chain.from_iterable(node['deps'].values())) for node in path2]
            childs_path2[i] = [[word2pos[c] for c in child] for child in childs]
        else:
            print(i, node1["address"], node2["address"])
    except AssertionError:
        print(i, "error")


# In[12]:


file = open('../data/train_pathsv3', 'wb')
_pickle.dump([words_seq, deps_seq, pos_tags_seq, word_path1, word_path2, dep_path1, dep_path2, pos_tags_path1, pos_tags_path2, pos_path1, pos_path2, childs_path1, childs_path2], file)


# In[ ]:




