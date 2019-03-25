from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
from nltk.chunk.regexp import RegexpParser
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from bs4 import BeautifulSoup
from collections import Counter, Iterable
from bs4.element import Comment
import requests, re, urllib, warnings, operator
from urllib.parse import urlparse
from urllib.error import HTTPError
from nltk.corpus import wordnet as wn

def checkAppropriateURL(url):
    parsedURL = urlparse(url)
    extn = parsedURL.path.split(".")[-1]
    site = parsedURL.netloc.split(".")
    path = parsedURL.path.split("/")[-1]
    if extn in ["pdf","doc","docx","xls","xlsx","ppt","pptx","odt"]:
        return False
    if any(i in site for i in ["pinterest"]):
        return False
    try:
        r = dict(requests.head(url).headers)["Content-Type"].split(";")[0]
        if(not r=="text/html"):
            print ("Failed",url,r)
            return False
    except:
        pass
    return True

def scrapeGoogleForAbstracts(query, count):
    words = query.split()
    q = ("+").join(words)
    print (q)
    gurl = "https://www.google.co.in/search?q=\"" + q + "\""
    data = requests.get(gurl).text
    soup = BeautifulSoup(data, "lxml")
    h3Rows = soup.find_all("h3", {"class":"r"})
    spanRows = soup.find_all("span", {"class":"st"})
    zippedRows = zip(h3Rows,spanRows)

    urls = []
    for zippedRow in zippedRows:
        try:
            h3Row = zippedRow[0]
            url = h3Row.find("a")['href']
            title = h3Row.text
            if(url.split("?")[0]=="/search"):
                continue
        except (GeneratorExit, KeyboardInterrupt, SystemExit):
            raise
        except:
            continue
        par = urllib.parse.parse_qs(urlparse(url).query)
        print ("par",par)
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
        urls.append((matchedQuery,appendingURL,title))
    i = 1
    same = 0
    prev = 0
    while(len(urls)<count):
        # print (len(urls),number)
        tempurl = gurl+ "&start=" +str(i*10)
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
                title = h3Row.text
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
                urls.append((matchedQuery, appendingURL, title))
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

def getCluesPatternsTuple(word):
    patterns = []
    patterns.append(("such as " + word, False))
    patterns.append((word + " and other", True))
    patterns.append((word + " or other", True))
    patterns.append(("including " + word, False))
    patterns.append(("especially " + word, False))
    return (patterns)


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    # Scraping a Web Document

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
    # print (url)
    html = urllib.request.urlopen(urllib.request.Request(url, headers=hdr))
    inputText = text_from_html(html)
    return inputText

def getAbstracts(query, count):
    urls = scrapeGoogleForAbstracts(query, 10)
    # print ("lenght",len(urls))
    texts = []
    for (q,url,title) in urls:
        print (url)
        try:
            text = getTextFromURL(url)
        except (GeneratorExit, KeyboardInterrupt, SystemExit):
            raise
        except:
            continue
        texts.append((q,url,text.strip(),title))
    return texts

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def getHypernymsFromWordnet(word):
    allSynsets = wn.synsets(word)
    multiList = [[[a.name() for a in b.lemmas()] for b in c.hypernyms()]for c in wn.synsets(word)]
    finalList = list(flatten(multiList))
    return finalList

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

def getConcepts(text):
    grammar = """
        CONCEPT:   {(<DT>)?(<JJ>)?<NN|NNS>+}
    """
    chunker = RegexpParser(grammar)
    taggedText = pos_tag(word_tokenize(text))
    textChunks = chunker.parse(taggedText)
    current_chunk = []
    for i in textChunks:
        if (type(i) == Tree and i.label() == "CONCEPT"):
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
    return current_chunk

stopwords_en = stopwords.words("english")

def preprocessing(raw):
    wordlist = word_tokenize(raw)
    text = [w.lower () for w in wordlist if w not in stopwords_en]
    return text

def simDoc(text1, text2):
    word_set = set(text1).union(set(text2))

    freqd_text1 = FreqDist(text1)
    text1_count_dict = dict.fromkeys(word_set, 0)
    for word in text1:
        text1_count_dict[word] = freqd_text1[word]

    freqd_text2 = FreqDist(text2)
    text2_count_dict = dict.fromkeys(word_set, 0)
    for word in text2:
        text2_count_dict[word] = freqd_text2[word]

    taggeddocs = []
    doc1 = TaggedDocument(words = text1, tags = [u'NEWS_1'])
    taggeddocs.append(doc1)
    doc2 = TaggedDocument(words = text2, tags = [u'NEWS_2'])
    taggeddocs.append(doc2)

    #build the modwl
    model = Doc2Vec(taggeddocs, dm =0, alpha=0.025, vector_size=20, min_alpha=0.025, min_count=0)

    model.train(taggeddocs, epochs=model.iter, total_examples=model.corpus_count)
    print ("FF",len(text1),len(text2))
    similarity = model.n_similarity(text1, text2)
    return similarity

def extractConcepts(posList, text, query):
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
                lastConceptExtracted = getConcepts(lastConcept.strip())
                if lastConceptExtracted:
                    allInstances.append(lastConceptExtracted[0])
                prevConceptsEnd = andExists.start()
                prevConcepts = rest[:prevConceptsEnd]
                prevConceptsList = prevConcepts.split(",")
                prevConceptsList = [a for a in prevConceptsList if a.strip()]
                print ("****START")
                print ("previous Concepts:",prevConcepts)
                for concept in prevConceptsList:
                        print (concept.strip(), getConcepts(concept.strip()))
                        conceptExtracted = getConcepts(concept.strip())
                        if conceptExtracted:
                            allInstances.append(conceptExtracted[-1])
                print ("*****DONE")
            else:
                allConcepts = rest.split(",")
                print ("#####HERE ARE ALL CONCEPTS:",allConcepts)
                for (i,concept) in enumerate(allConcepts):
                        if i==(len(allConcepts)-1):
                            print (concept)
                            conceptExtracted = getConcepts(concept.strip())
                            print ("1######CONCEPT EXTRACTED:", conceptExtracted)
                            if conceptExtracted:
                                allInstances.append(conceptExtracted[0])
                        else:
                            conceptExtracted = getConcepts(concept.strip())
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
                conceptExtracted = getConcepts(lastSentList[0].strip())
                if conceptExtracted:
                    allInstances.append(conceptExtracted[-1])
            else:
                for (i,concept) in enumerate(lastSentList):
                    conceptExtracted = getConcepts(concept.strip())
                    if conceptExtracted:
                        if i==(len(lastSentList)-1):
                            allInstances.append(conceptExtracted[0])
                        else:
                            allInstances.append(conceptExtracted[-1])
    return allInstances

def getHypernymsFromWWW(instance):
    cluesPatternsTuple = getCluesPatternsTuple(instance)
    hits = {}
    for c,(clue,isAfter) in enumerate(cluesPatternsTuple):
         
        allAbstracts = getAbstracts(clue,10)
        # print (allAbstracts)
        for (query,url,abstract,title) in allAbstracts:
            filename = ''.join(e for e in url if e.isalnum())
            f = open(filename[:15]+".txt","w+")
            f.write(abstract)
            f.close()

        for cnt,(query,url,abstract,title) in enumerate(allAbstracts):
            print (len(abstract))
            text1 = preprocessing(abstract)
            text2 = preprocessing(text)
            print ("ssF",len(text1),len(text2))
            if(not len(text1)):
                continue
            similarity = simDoc(text1, text2)

            if similarity>threshold:
                print (c,"::",cnt,":",url)
                startEndPositions = []
                try:
                    for m in re.finditer(re.escape(query), abstract):
                        try:
                            startEndPositions.append((m.start(), m.end()))
                        except:
                            print ("query:",query,"url:",url)
                            titleSearch = re.search(clue, title)
                            if titleSearch:
                                startEndPositions.append((titleSearch.start(), titleSearch.end()))
                            else:
                                continue
                except:
                    print ("1","query:",q,"url:",url)
                    continue
                allConcepts = extractConcepts(startEndPositions, abstract, query)
                if(allConcepts):
                    for conc in allConcepts:
                        if conc in hits:
                            hits[conc] += 1
                        else:
                            hits[conc] = 1
                print ("Number,",c," All concepts:", allConcepts)
    
    print ("Done for instance", instance)
    concept = max(hits.items(), key=operator.itemgetter(1))[0]
    return (concept, hits)


def URLInput():
    url = 'https://www.webstaurantstore.com/article/101/types-of-pizza.html'
    text = getTextFromURL(url)
    return text

def DocInput():
    file = open("test.txt")
    text = file.read()
    return text



def main(text, threshold):
#     instances = getInstances(text)
    instances = ["vulnerability", "threat"]
    finalList = []
    for instance in instances:
        #Add Code for iterating through patterns and clues here
        
        concept = getHypernymsFromWWW(instance)
        finalList.append((concept,instance))    

        concept = getHypernymsFromWordnet(instance)
        finalList.append((concept,instance))
        print ("Doing instance",instance)
    print ("Here's the final list of instances: ",finalList)
    return finalList

# text = URLInput()
text = DocInput()
threshold = 0.3
hypernymsDict = main(text, threshold)