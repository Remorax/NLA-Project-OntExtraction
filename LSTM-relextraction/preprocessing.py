#!/usr/bin/env python
# coding: utf-8

# In[1]:


import re, sys, nltk
from nltk.tokenize.stanford import StanfordTokenizer
path_to_jar = "/home/vivek/nltk/jars/stanford-postagger.jar"
tokenizer = StanfordTokenizer(path_to_jar)
import _pickle as pickle


# In[2]:


# Extracting the Relations 
# Please comment this when preprocessing the sentences.
# for training data open "TRAIN_FILE.TXT" and for test data open "TEST_FILE_FULL.TXT"

lines = []
for line in open("data/TRAIN_FILE.TXT"):
    lines.append(line.strip())

relations = []
for i, w in enumerate(lines):
    if((i+3)%4==0):
        relations.append(w)
        
f = open("data/train_relations.txt", 'w')
for rel in relations:
    f.write(rel+'\n')


# In[3]:


# For preprocessing Training data open "TRAIN_FILE.TXT and for Test data open "TEST_FILE.txt

lines = []
for line in open("data/TRAIN_FILE.TXT"):   
    m = re.match(r'^([0-9]+)\s"(.+)"$', line.strip())
    if(m is not None):
        lines.append(m.group(2))


# In[ ]:


len(relations)


# In[ ]:


sentences = []
e1 = []
e2 = []
for j,line in enumerate(lines):
    text = []
    temp = []
    t = line.split("<e1>")
    text.append(t[0])
    temp.append(t[0])

    t = t[1].split("</e1>")
    e1_text = text
    e1_text = " ".join(e1_text)
    e1_text = tokenizer.tokenize(e1_text)
    text.append(t[0])
    e11= t[0]
    y = tokenizer.tokenize(t[0])
    y[0] +="E11"
    temp.append(" ".join(y))
    t = t[1].split("<e2>")
    text.append(t[0])
    temp.append(t[0])
    t = t[1].split("</e2>")
    e22 = t[0]
    e2_text = text
    e2_text = " ".join(e2_text)
    e2_text = tokenizer.tokenize(e2_text)
    text.append(t[0])
    text.append(t[1])
    y = tokenizer.tokenize(t[0])
    y[0] +="E22"
    temp.append(" ".join(y))
    temp.append(t[1])

    text = " ".join(text)
    text = tokenizer.tokenize(text)
    temp = " ".join(temp)
    temp = tokenizer.tokenize(temp)

    q1 = tokenizer.tokenize(e11)[0]
    q2 = tokenizer.tokenize(e22)[0]
    for i, word in enumerate(text):
        if(word.find(q1)!=-1):
            if(temp[i].find("E11")!=-1):
                e1.append(i)            
                break
    for i, word in enumerate(text):
        if(word.find(q2)!=-1):
                if(temp[i].find("E22")!=-1):
                    e2.append(i)   
    text = " ".join(text)
    sentences.append(text)
    print(j, text)


# In[ ]:


len(sentences), len(e1), len(e2)


# In[ ]:


# for saving training data open "train_data" and for test data open "test_data"

with open('data/train_data', 'wb') as f:
    pickle.dump((sentences, e1, e2), f)
    f.close()


# In[ ]:




