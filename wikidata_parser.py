from pywikibot.data import api
import pywikibot, urllib.request, json 

def getItems(site, itemtitle):
   params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
   request = api.Request(site=site,**params)
   return request.submit()

# Login to wikidata
def run(termsList):   
  for term in termsList:
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    wikidataEntries = getItems(site, term)
    # Print the different Wikidata entries to the screen
    # prettyPrint(wikidataEntries)
    allNames = []
    # Print each wikidata entry as an object
    for wdEntry in wikidataEntries["search"]:
      entity_id = wdEntry["id"]
      with urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetentities&ids=" + entity_id + "&format=json") as url:
        data = json.loads(url.read().decode())
        allClaims = data["entities"][entity_id]["claims"]
        if "P31" in allClaims:
          allInstances = allClaims["P31"]
          for inst in allInstances:
            currentid = inst["mainsnak"]["datavalue"]["value"]["id"]
            with urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="+currentid+"&languages=en&format=json") as suburl:
              dat = json.loads(suburl.read().decode())
              instanceName = dat["entities"][currentid]["labels"]["en"]["value"]
            with urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="+entity_id+"&languages=en&format=json") as suburl:
              dat = json.loads(suburl.read().decode())
              conceptName = dat["entities"][entity_id]["labels"]["en"]["value"]
            allNames.append([instanceName, conceptName])
        if "P279" in allClaims:
          allInstances = allClaims["P279"]
          for inst in allInstances:
            currentid = inst["mainsnak"]["datavalue"]["value"]["id"]
            print (currentid)
            with urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="+currentid+"&languages=en&format=json") as suburl:
              s = suburl.read().decode()
              print (s)
              dat = json.loads(s)
              instanceName = dat["entities"][currentid]["labels"]["en"]["value"]
            with urllib.request.urlopen("https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="+entity_id+"&languages=en&format=json") as suburl:
              dat = json.loads(suburl.read().decode())
              conceptName = dat["entities"][entity_id]["labels"]["en"]["value"]
            allNames.append([instanceName, conceptName])

    return allNames

# Insert termsList extracted from the PDFs here
termsList = ["Security"]

run(termsList)