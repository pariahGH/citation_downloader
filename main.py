from bs4 import BeautifulSoup
import requests
import urllib.parse
import sys
import os
import time
import wx
from threading import Thread
import pytesseract
from PIL import Image
import json

# read in the file, split on "\n\n" - all citation blocks must be separated by two consecutive newlines (one blank space between them)
class PDFThread(Thread):
	def __init__(self, filename, mailName, logDisplay, saveDir, startButton):
		Thread.__init__(self)
		self.filename = filename
		self.mailName = mailName
		self.logDisplay = logDisplay
		self.saveDir = saveDir
		self.startButton = startButton
	
	def getFromSciHub(self, data,w):
		try:
			pdfUrl = ""
			self.logDisplay.AppendText("Attempting to get PDF url...\n")
			#get from scihub - initiate download, but first check if there was a captcha - if so print to stdout, wait 10 seconds, try again
			articlePage = BeautifulSoup(requests.get("https://sci-hub.tw/"+data["doi"]).text,'html5lib')
			iframes = articlePage.find_all("iframe")
			if len(iframes) > 0:
				pdfUrl = iframes[0]["src"]
			else:
				self.logDisplay.AppendText("Hit PDF URL captcha, adding to retry list\n\n")
				return data
					
			self.logDisplay.AppendText("PDF url found for: " + data["title"]+"\n")
			#check if the response is a captcha by checking content type
			#this can also be tweaked to download the captcha
			response = requests.get(pdfUrl)
			if(response.headers["Content-Type"] != "application/pdf"):
				self.logDisplay.AppendText("Hit PDF download captcha, adding to retry list\n\n")
				return data
				
			with open(self.saveDir+"/"+urllib.parse.quote(data["title"][0:99],safe='')+".pdf",'wb') as dest:
				dest.write(response.content)
			# write to log 
			w.write(data["citation"]+"\t"+data["doi"]+"\t"+data["title"]+"\n")
			self.logDisplay.AppendText("Downloaded PDF!\n\n")
			return ""
		except Exception as e:
			self.logDisplay.AppendText("Hit timeout, adding to retry list\n\n")
			return data
		
	def run(self):
		with open(self.filename,'r', encoding="utf8") as f:
			#create our write file
			if not os.path.exists(self.saveDir):
				os.makedirs(self.saveDir)
			
			with open(self.saveDir+'/list.txt','w', encoding="utf8") as w:
				data = f.read()
				captchaArray = []
				# read in every citation, make a query against crossref, extract the doi from the first result, and download it from scihub
				for citationRaw in data.split("\n\n"):
					citation = citationRaw.replace("\n"," ")
					if(citation != ""):
						self.logDisplay.AppendText("Looking up metadata...\n")
						try:
							data = requests.get("https://api.crossref.org/works?"+urllib.parse.urlencode({"query.bibliographic":citation,"mailto":self.mailName}))
							response = data.json()["message"]['items'][0]
								
							doi = response["DOI"]
							score = response["score"]
							title = response["title"][0]
								
							self.logDisplay.AppendText("Found DOI!\n")
							
							#get the iframe that holds the pdf
							returned = self.getFromSciHub({"doi":doi,"title":title,"citation":citation},w)
							if(returned != ""):
								captchaArray.append(returned)
						except Exception as e:
							print(data)
							print(citation)
						
				# retry!
				self.logDisplay.AppendText("Done! Checking retry list...\n\n")
				length = len(captchaArray)
				retries = 0
				while(length >0 and retries != 5):
					self.logDisplay.AppendText(str(length)+" retries found! Waiting 30 minutes...\n\n")
					time.sleep(1800)
					temp = captchaArray
					captchaArray = []
					for retry in temp:
						returned = self.getFromSciHub(retry,w)
						if(returned != ""):
							captchaArray.append(returned)
					retries += 1
					length = len(captchaArray)
				if(retries == 5):
					self.logDisplay.AppendText("Max retries hit, writing leftovers to file!\n\n")
					# iterate over the retries thing and write the citations
					with open('./retries.txt','w', encoding="utf8") as retryDest:
						for retry in captchaArray:
							retryDest.write(retry["citation"]+"\n\n")
				self.logDisplay.AppendText("Done!")
				self.startButton.Enable()

class CitationDownloader(wx.Frame):
	#mailto name is so that cross ref likes us
	filename = ""
	saveDir = ""
	def __init__(self, *args,**kw):
		super(CitationDownloader,self).__init__(*args,**kw,size=(700,600))
		panel = wx.Panel(self)
		#file picker, button, log
		self.startButton = wx.Button(panel,label="Start download")
		selectFileButton = wx.Button(panel, label="Select citation file")
		clearButton = wx.Button(panel, label="Clear")
		selectDirButton = wx.Button(panel, label="Select save folder")
		self.pathDisplay = wx.StaticText(panel,label="No file selected")
		self.dirDisplay = wx.StaticText(panel,label="No save folder selected")
		self.logDisplay = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
		mailLabel = wx.StaticText(panel, label="Email Address (CrossRef):")
		self.mailTo = wx.TextCtrl(panel)
		sizer = wx.BoxSizer(wx.VERTICAL)
		buttonHolder = wx.BoxSizer(wx.HORIZONTAL)
		pathHolder = wx.BoxSizer(wx.HORIZONTAL)
		
		pathHolder.AddMany([
			(self.pathDisplay,1,wx.EXPAND),(self.dirDisplay,1,wx.EXPAND), (mailLabel,1,wx.EXPAND), (self.mailTo,1,wx.EXPAND)
		])
		
		buttonHolder.AddMany([
			(selectFileButton,1,wx.EXPAND),(selectDirButton,1,wx.EXPAND),(self.startButton,1,wx.EXPAND),(clearButton,1,wx.EXPAND)
		])
		
		sizer.AddMany([
			(buttonHolder,.5,wx.EXPAND),(pathHolder,.5,wx.EXPAND),(self.logDisplay,1,wx.EXPAND)
		])
		
		panel.SetSizerAndFit(sizer)
		
		self.Bind(wx.EVT_BUTTON, self.fileSelectClicked, selectFileButton)
		self.Bind(wx.EVT_BUTTON, self.downloadClicked, self.startButton)
		self.Bind(wx.EVT_BUTTON, self.dirSelectClicked, selectDirButton)
		self.Bind(wx.EVT_BUTTON, self.clearClicked, clearButton)
	
	def fileSelectClicked(self, event):
		with wx.FileDialog(self, "Select file", wildcard="TXT files (*.txt)|*.txt", style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return     
			self.filename = fileDialog.GetPaths()[0]
			self.pathDisplay.SetLabel(self.filename)
	
	def dirSelectClicked(self, event):
		with wx.DirDialog(self, "Select folder to save results to", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dirDialog:
			if dirDialog.ShowModal() == wx.ID_CANCEL:
				return     
			self.saveDir = dirDialog.GetPath()
			self.dirDisplay.SetLabel(self.saveDir)
			
	def downloadClicked(self, event):
		mailName = self.mailTo.GetValue()
		if(self.filename != "" and self.saveDir != "" and mailName != ""):
			self.startButton.Disable()
			thread = PDFThread(self.filename, mailName, self.logDisplay, self.saveDir, self.startButton)
			thread.start()
			
	def clearClicked(self, event):
		self.logDisplay.SetValue("")
		self.saveDir = ""
		self.dirDisplay.SetLabel(self.saveDir)
		self.filename = ""
		self.pathDisplay.SetLabel(self.filename)
			
app = wx.App()
frame = CitationDownloader(None, title="Citation Downloader")
frame.Show()
app.MainLoop()