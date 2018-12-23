# Citation Downloader

Ever go on a binge reading research papers and end up with dozens if not hundreds of references that you want to download?
I have, and it takes forever to go through and download them one by one. And for some people, access is too expensive in the first place. 

This script uses CrossRef's API to parse references for a DOI number, then uses Sci-Hub to download it (AFAIK places like Elseveir don't even have an API for downloading papers).

The Sci-Hub captcha is currently handled by saving failed attempts and failed attempts, then iterating through the failures after a half hour wait - this current repeats five times. 

In my experience, any that haven't downloaded after 5 retries are unlikely to work for the rest of the day. 

The captchas folder contains a bunch of captchas that I saved, with a vague idea of training Tesseract to try and implement captcha solving - this may or may not ever actually happen as its currently good enough for my needs. That being said, feel free to try and take a crack at it. 

Comes with a GUI built with wxPython for your clicking convenience. No cmd-line interface.

I added a license because I figure if people who know more about laws than I do say its a good idea, it's probably a good idea. That being said, take this code and run with it. Attribtion is nice but not required. My only request is that you use this ~~power~~ script for the furtherance of humanity's knowledge. 
