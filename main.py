import os
import time
import wx
from threading import Thread
import json
import util

class PDFThread(Thread):
	def __init__(self,options, logger, startButton):
		Thread.__init__(self)
		self.fileName = options["fileName"]
		self.mailName = options["mailName"]
		self.saveDir = options["saveDir"]
		self.logger = logger
		self.startButton = startButton
		
	def run(self):
		with open(self.fileName,'r', encoding="utf8") as f:
			data = f.read().split("\n\n")
			errorArray, length = iterateCitations(data)
			# retry!
			self.logger.logToDisplay("Done! Checking retry list...\n")
			retries = 0
			while(length >0 and retries != 5):
				self.logger.logToDisplay(str(length)+" retries found! Waiting 30 minutes...\n")
				time.sleep(1800)
				errorArray, length = iterateCitations(errorArray)
				retries += 1
			if(retries == 5):
				self.logger.logToDisplay("Max retries hit, writing leftovers to file!\n")
				with open('./retries.txt','w', encoding="utf8") as retryDest:
					for retry in errorArray:
						retryDest.write(retry["citation"]+"\n\n")
			self.logger.logToDisplay("Done!")
			self.startButton.Enable()

class CitationDownloader(wx.Frame):
	#mailto name is so that cross ref likes us and lets use their special pool
	fileName = ""
	saveDir = ""
	def __init__(self, *args,**kw):
		super(CitationDownloader,self).__init__(*args,**kw,size=(700,600))
		panel = wx.Panel(self)
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
			self.fileName = fileDialog.GetPaths()[0]
			self.pathDisplay.SetLabel(self.fileName)
	
	def dirSelectClicked(self, event):
		with wx.DirDialog(self, "Select folder to save results to", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dirDialog:
			if dirDialog.ShowModal() == wx.ID_CANCEL:
				return     
			self.saveDir = dirDialog.GetPath()
			self.dirDisplay.SetLabel(self.saveDir)
			
	def downloadClicked(self, event):
		mailName = self.mailTo.GetValue()
		if(mailName != ""):
			if(self.fileName != "" and self.saveDir != ""):
				if not os.path.exists(self.saveDir):
					os.makedirs(self.saveDir)
				self.startButton.Disable()
				logger = util.Logger(self.logDisplay, self.saveDir)
				options = {"fileName": self.fileName, "mailName": mailName, "saveDir":self.saveDir}
				thread = PDFThread(options, logger, self.startButton)
				thread.start()
		else:
			self.logDisplay.AppendText("Please enter an email address - CrossRef uses a special pool for those who provide a mailTo\n\n")
			
	def clearClicked(self, event):
		self.logDisplay.SetValue("")
		self.saveDir = ""
		self.dirDisplay.SetLabel(self.saveDir)
		self.fileName = ""
		self.pathDisplay.SetLabel(self.fileName)
			
app = wx.App()
frame = CitationDownloader(None, title="Citation Downloader")
frame.Show()
app.MainLoop()