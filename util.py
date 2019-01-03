import urllib.parse
import requests
from bs4 import BeautifulSoup

class Logger:
	def __init__(self, logDisplay, saveDir):
		self.logDisplay = logDisplay
		self.saveDir = saveDir
		
	def logToDisplay(self, text):
		self.logDisplay.AppendText(f'{text}\n')
		
	def logMapping(self, text):
		with open(f'{self.saveDir}/list.txt','w') as file:
			file.write(f'{text}\n')
			
	def savePDF(self, name, data):
		with open(f'{self.saveDir}/{name}.pdf','wb') as dest:
			dest.write(data)

class SciHubError(Exception):
    def __init__(self, message, data):
        super().__init__(message)
        self.data = data
			
def getMetadata(citation, mailName):
	data = requests.get("https://api.crossref.org/works?"+urllib.parse.urlencode({"query.bibliographic":citation,"mailto":mailName}))
	response = data.json()["message"]['items'][0]
	return (response["DOI"], response["title"][0])
		
def getPDF(citationRaw, logger, mailName):
	citation = citationRaw.replace("\n"," ")
	if(citation != ""):
		logger.logToDisplay("Looking up metadata...")
		doi, title = getMetadata(citation, mailName)
		logger.logToDisplay(f'Found DOI {doi} for {title} from {citation}!')
		getFromSciHub({"doi":doi,"title":title,"citation":citation},logger)
	else:
		logger.logToDisplay("Skipping blank citation entry\n")
		
def iterateCitations(data):
	errorArray = []
	for citation in data:
		try:
			util.getPDF(citation, self.logger, self.mailName)
		except util.SciHubError as e:
			errorArray.append(e.data)
	return (errorArray, len(errorArray))
		
def getFromSciHub(data, logger):
	try:
		pdfUrl = ""
		logger.logToDisplay("Attempting to get PDF url...")
		
		articlePage = BeautifulSoup(requests.get("https://sci-hub.tw/"+data["doi"]).text,'html5lib')
		iframes = articlePage.find_all("iframe")
		
		if len(iframes) > 0:
			pdfUrl = iframes[0]["src"]
		else:
			logger.logToDisplay("Hit PDF URL captcha, adding to retry list\n")
			raise SciHubError('url captcha', data)
				
		logger.logToDisplay("PDF url found for: " + data["title"])
		
		#check if the response is a captcha by checking content type
		response = requests.get(pdfUrl)
		if(response.headers["Content-Type"] != "application/pdf"):
			logger.logToDisplay("Hit PDF download captcha, adding to retry list\n")
			raise SciHubError('download captcha', data)
			
		#in case there are funky characters
		name = urllib.parse.quote(data["title"])
		logger.savePDF(name, response.content)
		
		logger.logMapping(data["citation"]+"\t"+data["doi"]+"\t"+data["title"])
		logger.logToDisplay("Downloaded PDF!\n")
		
	except Exception as e:
		if(type(e) is SciHubError):
			raise e
		print(e)
		logger.logToDisplay("Hit timeout, adding to retry list\n")
		raise SciHubError('timeout', data)