import requests, re, urllib, itertools, textract, os
from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urlparse
from collections import Counter, Iterable
from nltk.corpus import wordnet as wn
from gensim.models import KeyedVectors
from anytree import Node
from nltk.tree import Tree
from nltk.chunk.regexp import RegexpParser
from nltk import pos_tag, word_tokenize

def checkAppropriateURL(url):
    parsedURL = urlparse(url)   

    extn = parsedURL.path.split(".")[-1]
    site = parsedURL.netloc.split(".")
    path = parsedURL.path.split("/")[-1]

    if extn in ["pdf","doc","docx","xls","xlsx","ppt","pptx","odt"]:
        return False
    if any(i in site for i in ["pinterest"]):
        return False
    r = dict(requests.head(url).headers)["Content-Type"].split(";")[0]
    if(not r=="text/html"):
        return False
    return True

def scrapeGoogleForAbstracts(query, count):
    words = query.split()
    q = ("+").join(words)
    print (q)
    query_url_goog = "https://www.google.co.in/search?q=\"" + q + "\""
    data = requests.get(query_url_goog).text
    print (data)
    soup = BeautifulSoup(data, "lxml")
    h3Rows = soup.find_all("h3", {"class":"r"})
    spanRows = soup.find_all("span", {"class":"st"})
    zippedRows = zip(h3Rows,spanRows)
    urls = []
    print (list(zippedRows))
    for zippedRow in zippedRows:
        try:
            h3Row = zippedRow[0]
            url = h3Row.find("a")['href']
            if(url.split("?")[0]=="/search"):
                continue
        except (GeneratorExit, KeyboardInterrupt, SystemExit):
            raise
        except:
            continue
        par = urllib.parse.parse_qs(urlparse(url).query)
        try:
            appendingURL = par['q'][0]
        except:
            continue
        if(not checkAppropriateURL(appendingURL)):
            continue
        matchedQuery = query
        allbElems = zippedRow[1].findAll('b')
        for bElem in allbElems:
            if bElem.string[0].isalnum():
                matchedQuery = bElem.string
        urls.append((matchedQuery,appendingURL))
    i = 1
    same = 0
    prev = 0
    while(len(urls)<count):
#         print ("Query: ",query)
        tempurl = query_url_goog + "&start=" +str(i*10)
        i+=1
        data = requests.get(tempurl).text
        soup = BeautifulSoup(data, "lxml")
        h3Rows = soup.find_all("h3", {"class":"r"})
        spanRows = soup.find_all("span", {"class":"st"})
        zippedRows = zip(h3Rows,spanRows)
        for (j,zippedRow) in enumerate(zippedRows):
            try:
                h3Row = zippedRow[0]
                url = h3Row.find("a")['href']
            except (GeneratorExit, KeyboardInterrupt, SystemExit):
                raise
            except:
                continue
            par = urllib.parse.parse_qs(urlparse(url).query)
            try:
                appendingURL = par['q'][0]
                if(not checkAppropriateURL(appendingURL)):
                    continue
                matchedQuery = query
                allbElems = zippedRow[1].findAll('b')
                for bElem in allbElems:
                    if bElem.string[0].isalnum():
                        matchedQuery = bElem.string
                urls.append((matchedQuery, appendingURL))
            except (GeneratorExit, KeyboardInterrupt, SystemExit):
                raise
            except:
                continue
        if prev == len(urls):
            same +=1 
            if same>=10:
                same = 0
                break
        prev = len(urls)
    return urls[:count]



def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def getTextFromURL(url):
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
   'Accept-Encoding': 'none',
   'Accept-Language': 'en-US,en;q=0.8',
   'Connection': 'keep-alive'}
    html = urllib.request.urlopen(urllib.request.Request(url, headers=hdr))
    inputText = text_from_html(html)
#     print (inputText)
    return inputText

def getAbstracts(query, count):
    urls = scrapeGoogleForAbstracts(query, count)
    print (urls)
    print ("lenght",len(urls))
    texts = []
    for (query, url) in urls:
        print (url)
        try:
            text = getTextFromURL(url)
        except (GeneratorExit, KeyboardInterrupt, SystemExit):
            raise
        except:
            continue
        texts.append((query,url,text.strip()))
    return texts

def processWordSet(wordSet):
    for (i,word) in enumerate(wordSet):
        wordSet[i] = re.sub("^[^a-zA-Z]*|[^a-zA-Z(?<!(s\'))]*$","",word)
    return wordSet

def getHypernymsFromWordnet(word):
    allSynsets = wn.synsets(word)
    multiList = [[[a.name() for a in b.lemmas()] for b in c.hypernyms()]for c in wn.synsets(word)]
    finalList = flatten(multiList)
    return Counter(finalList)

def compareTuple(x,model):
    try:
        sim = model.similarity(x[0],x[1])
        return sim
    except:
        return 0

def initNodesList(wordSet):
    nodesList = []
    for wordNode in wordSet:
        nodesList.append(Node(wordNode))
    return nodesList

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def getHearstPatterns(word):
    # Pattern, Instances after/before, One/many instances
    patterns = []
    patterns.append((word + " such as", True))
    patterns.append(("such " + word + " as", True))
    patterns.append(("and other " + word, False))
    patterns.append(("or other " + word, False))
    patterns.append((word + ", including", True))
    patterns.append((word + ", especially", True))
    return patterns

def getInstances(text):
    grammar = """
        PRE:   {<NNS|NNP|NN|NP|JJ|UH>+}
        MID: {<DT|IN|POS|FW|-|NP|NPS|NN|NNS>+}
        INSTANCE:   {(<DT+>)?(<JJ+>)?<PRE>(<MID><PRE>)?}
    """
    chunker = RegexpParser(grammar)
    taggedText = pos_tag(word_tokenize(text))
    textChunks = chunker.parse(taggedText)
    current_chunk = []
    for i in textChunks:
        if (type(i) == Tree and i.label() == "INSTANCE"):
            # print (i.leaves())
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
    return current_chunk

def extractHypernyms(posList, text, query):
    allInstances = []
    for (st,end) in posList:
        if query[1]:
            #Instances after, and exists                
            tempText = text[end+1:]
            rest = re.match(".*?\.",tempText)
            if rest:
                rest = rest.group()
            else:
                rest = tempText
            andExists = re.search(" (and|or) ", rest)
            if andExists:
                print ("rest:", rest)
                lastConceptPos = andExists.end()
                lastConcept = rest[lastConceptPos:]
                print ("lastConcept: ", lastConcept)
                lastConceptExtracted = getInstances(lastConcept.strip())
                if lastConceptExtracted:
                    allInstances.append(lastConceptExtracted[0])
                prevConceptsEnd = andExists.start()
                prevConcepts = rest[:prevConceptsEnd]
                prevConceptsList = prevConcepts.split(",")
                prevConceptsList = [a for a in prevConceptsList if a.strip()]
                print ("****START")
                print ("previous Concepts:",prevConcepts)
                for concept in prevConceptsList:
                        print (concept.strip(), getInstances(concept.strip()))
                        conceptExtracted = getInstances(concept.strip())
                        if conceptExtracted:
                            allInstances.append(conceptExtracted[-1])
                print ("*****DONE")
            else:
                allConcepts = rest.split(",")
                print ("#####HERE ARE ALL CONCEPTS:",allConcepts)
                for (i,concept) in enumerate(allConcepts):
                        if i==(len(allConcepts)-1):
                            print (concept)
                            conceptExtracted = getInstances(concept.strip())
                            print ("1######CONCEPT EXTRACTED:", conceptExtracted)
                            if conceptExtracted:
                                allInstances.append(conceptExtracted[0])
                        else:
                            conceptExtracted = getInstances(concept.strip())
                            print ("######CONCEPT EXTRACTED:", conceptExtracted)
                            if conceptExtracted:
                                allInstances.append(conceptExtracted[-1])
        else:
            tempText = text[:st]
            print ("tempText", tempText)
            try:
                lastSentPos = [m.end() for m in re.finditer(".*?\.",tempText)][-1]
                lastSent = tempText[:lastSentPos]
            except:
                lastSent = tempText
            lastSentList = lastSent.split(",")
            lastSentList = [a for a in lastSentList if a.strip()]
            if len(lastSentList) == 1:
                conceptExtracted = getInstances(lastSentList[0].strip())
                if conceptExtracted:
                    allInstances.append(conceptExtracted[-1])
            else:
                for (i,concept) in enumerate(lastSentList):
                    conceptExtracted = getInstances(concept.strip())
                    if conceptExtracted:
                        if i==(len(lastSentList)-1):
                            allInstances.append(conceptExtracted[0])
                        else:
                            allInstances.append(conceptExtracted[-1])
    return allInstances

def getHypernymsFromWWW(word):
    allHypernyms = []
    queriesList = getHearstPatterns(word)
    for query in queriesList:
        texts = getAbstracts(query[0], 10)
        for (q,url,text) in texts:
            startEndPositions = []
            try:
                for m in re.finditer(re.escape(q), text):
                    try:
                        startEndPositions.append((m.start(), m.end()))
                    except:
                        print ("query:",q,"url:",url)
                        continue
            except:
                print ("1","query:",q,"url:",url)
                continue
            allHypernyms.extend(extractHypernyms(startEndPositions, text, query))
    return Counter(allHypernyms)

def getHypernymsFromTextCorpus(word):
    allInstances = []
    for quer in ["such as", "including", "especially", "such_as"]:
        if quer == "such_as":
            regex = "such " + word + " as" + ".*?\." 
        else:
            regex = word + ".*?\."
        allMatches = re.findall(regex, textCorpus)
        for match in allMatches:
            if quer=="such_as":
                rest = match
            else:
                rest = re.search(quer+".*", match)
                if rest:
                    rest = rest.group()
                else:
                    continue
            andExists = re.search(" (and|or) ", rest)
            if andExists:
                print ("rest:", rest)
                lastConceptPos = andExists.end()
                lastConcept = rest[lastConceptPos:]
                print ("lastConcept: ", lastConcept)
                lastConceptExtracted = getInstances(lastConcept.strip())
                if lastConceptExtracted:
                    allInstances.append(lastConceptExtracted[0])
                prevConceptsEnd = andExists.start()
                prevConcepts = rest[:prevConceptsEnd]
                prevConceptsList = prevConcepts.split(",")
                prevConceptsList = [a for a in prevConceptsList if a.strip()]
                print ("****START")
                print ("previous Concepts:",prevConcepts)
                for concept in prevConceptsList:
                        print (concept.strip(), getInstances(concept.strip()))
                        conceptExtracted = getInstances(concept.strip())
                        if conceptExtracted:
                            allInstances.append(conceptExtracted[-1])
                print ("*****DONE")
            else:
                allConcepts = rest.split(",")
                print ("#####HERE ARE ALL CONCEPTS:",allConcepts)
                for (i,concept) in enumerate(allConcepts):
                        if i==(len(allConcepts)-1):
                            print (concept)
                            conceptExtracted = getInstances(concept.strip())
                            print ("1######CONCEPT EXTRACTED:", conceptExtracted)
                            if conceptExtracted:
                                allInstances.append(conceptExtracted[0])
                        else:
                            conceptExtracted = getInstances(concept.strip())
                            print ("######CONCEPT EXTRACTED:", conceptExtracted)
                            if conceptExtracted:
                                allInstances.append(conceptExtracted[-1])
        
    for quer in ["and other ", "or other "]:
        regex = "\..*?" + word 
        allMatches = re.findall(regex, textCorpus)
        for match in allMatches:
            rest = re.search(".*" + quer, match)
            if rest:
                rest= rest.group()
            else:
                continue
            allConcepts = rest.split(",")
            print ("#####HERE ARE ALL CONCEPTS:",allConcepts)
            for (i,concept) in enumerate(allConcepts):
                conceptExtracted = getInstances(concept.strip())
                print ("######CONCEPT EXTRACTED:", conceptExtracted)
                if conceptExtracted:
                    allInstances.append(conceptExtracted[-1])
    return Counter(allInstances)

def getHypernyms(word):
    wordnet = getHypernymsFromWordnet(word)
    www = getHypernymsFromWWW(word)
    text = getHypernymsFromTextCorpus(word)
    return (wordnet + www + text)

wordSet = ["vulnerability","threat"]

model = KeyedVectors.load_word2vec_format("~/GoogleNews-vectors-negative300.bin", binary=True)

# Sort by decreasing similarity
tuplesList = list(itertools.combinations(wordSet,2))
sortedList = sorted(tuplesList, key=lambda x : compareTuple(x,model), reverse=True)

clusteredSet = set()
hypernymDict = {}

root = Node("root")
nodesList = initNodesList(wordSet)

directory = os.fsencode("SecurityPDFs")

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".pdf"): 
        textCorpus += textract.process("SecurityPDFs/" + filename).decode("utf-8")
        continue

hypernymDict = {}

for word in wordSet:
    hypernymDict[word] = getHypernyms(word)

open("Clustering_Results.txt","w+").write(str(hypernymDict))