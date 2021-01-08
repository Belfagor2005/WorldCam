#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import socket
import re, sys
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.FileList import FileList
from Components.Input import Input
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Job, job_manager as JobManager, Condition
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, ConfigText, ConfigEnableDisable, KEY_LEFT, KEY_RIGHT, KEY_0, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import *
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.TaskView import JobView
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_SKIN_IMAGE, SCOPE_MEDIA
from Tools.LoadPixmap import LoadPixmap
from enigma import eServiceCenter
from enigma import eServiceReference
from enigma import eTimer, quitMainloop, RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, eListbox, gFont, getDesktop, ePicLoad
from socket import gaierror, error
from threading import Thread
from twisted.internet import reactor
from twisted.web import client
from twisted.web.client import getPage, downloadPage



PY3 = sys.version_info[0] == 3

if PY3:
    # from urllib.request import urlopen, Request
    # from urllib.error import URLError, HTTPError
    # from urllib.parse import urlparse
    # from urllib.parse import urlencode, quote
    # from urllib.request import urlretrieve
    import http.client
    import urllib.request, urllib.parse, urllib.error
    import urllib.parse
    from http.client import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
    from urllib.parse import quote, unquote_plus, unquote
    from urllib.request import Request, urlopen as urlopen2
    from urllib.error import URLError
    from urllib.request import urlopen
    from urllib.parse import parse_qs
else:
    # from urllib2 import urlopen, Request
    # from urllib2 import URLError, HTTPError
    # from urlparse import urlparse
    # from urllib import urlencode, quote
    # from urllib import urlretrieve

    import httplib
    import urllib
    import urlparse
    from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
    from urllib import quote, unquote_plus, unquote
    from urllib2 import Request, URLError, urlopen as urlopen2
    from urllib2 import urlopen
    from urlparse import parse_qs



#from TaskView2 import JobViewNew
import re
##########################
import gettext
from skin import parseColor
#from Playlist import Playlist


from enigma import getDesktop
DESKHEIGHT = getDesktop(0).size().height()

def _(txt):
	t = gettext.dgettext("xbmcaddons", txt)
	if t == txt:
		print("[XBMCAddonsA] fallback to default translation for", txt)
		t = gettext.gettext(txt)
	return t

##########################

HTTPConnection.debuglevel = 1
#from download import startdownload ##mfaraj2608 to for new download management
std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}  
##############################################################
#                                                            #
#   Mainly Coded by pcd, July 2013                 #
#                                                            #
##############################################################

SREF = " "



class Playvid(Screen):
    skin = """
		<screen position="center,center" size="800,500" title="Video List" >
			<widget name="list" position="80,50" size="450,300" scrollbarMode="showOnDemand" />
                        <widget name="info" position="50,150" zPosition="4" size="300,100" font="Regular;22" foregroundColor="#7bd7f7" backgroundColor="#40000000" transparent="1" halign="left" valign="center" />

                        <ePixmap name="red"    position="100,430"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />

	                <widget name="key_red" position="100,430" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="#ffffff" font="Regular;20" transparent="1" shadowColor="#25062748" shadowOffset="-2,-2" /> 

                        <!--ePixmap position="100,650" zPosition="1" size="50,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/XBMCAddons/images/Exit2.png" /-->
         
               </screen>"""            
	

    def __init__(self, session, name, url, desc):
        global SREF
        Screen.__init__(self, session)
        self.name = name
        self.url = url  
        self.skin = Playvid.skin
        self["list"] = List([])
        self["list"] = RSList([])
        self['info'] = Label()
        self['key_red'] = Button(_('Exit'))
        self['key_green'] = Button(_('Download'))
        self['key_yellow'] = Button(_('Play'))
        self['key_blue'] = Button(_('Stop Download'))
        self['setupActions'] = ActionMap(['SetupActions', 'ColorActions', 'TimerEditActions'], {'red': self.close,
         'green': self.okClicked,
         'yellow': self.play,
         'blue': self.stopDL,
         'cancel': self.cancel,         
         'ok': self.okClicked}, -2)
        self.icount = 0
        self.bLast = 0
        self.useragent = "QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)"
        cachefold = "/tmp/"
        self.svfile = " "
        self.list=[]
########################
        """
        i=0
        while i<7:
               self.list.append(i)
               i=i+1 
        self.list[0] =(_("Play"))
        self.list[1] =(_("Play with vlc"))
        self.list[2] =(_("Download"))
        self.list[3] =(_("Stop download"))
        self.list[4] =(_("Add to favorites"))
        self.list[5] =(_("Add to bouquets"))
        self.list[6] =(_("Current Downloads"))
        """
        self.list.append((_("Play")))
########################
        self.name = name
#hls        url = "http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8"
#null        url = "http://188.138.9.246/S2/HLS_LIVE/disney/playlist.m3u8"
        self.url = url  
        print("Here in Playvid self.url =", self.url)
        print("<<<Endurl") 
#        self.url = self.url.replace("|", "\|")
        n1 = self.url.find("|", 0)
        if n1 > -1:
                self.url = self.url[:n1]

        print("Here in Playvid self.url B=", self.url)
        #self['info'].setText(txt)

        ####################
##        self.updateTimer = eTimer()
##        self.updateTimer.callback.append(self.updateStatus)
##        self.updateTimer.start(2000)
##        self.updateStatus()
        ####################
        self.updateTimer = eTimer()
        try:
               self.updateTimer_conn = self.updateTimer.timeout.connect(self.updateStatus)
        except AttributeError:
               self.updateTimer.callback.append(self.updateStatus)
#       self.updateTimer.callback.append(self.updateStatus)
##	self.updateTimer.start(2000)
##	self.updateStatus()
        ####################        
        self['info'].setText(" ")
        self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
        SREF = self.srefOld
        """
        if config.plugins.kodiplug.directpl.value is True:
                print "Here in directpl"
                self.onShown.append(self.start2)
        elif "hds://" in url: 
                self.onShown.append(self.start3)
        elif self.url.startswith("stack://"):
                self.onShown.append(self.start4)
        elif "plugin://plugin.video.youtube" in self.url or "youtube.com/" in self.url :
                self.onShown.append(self.start5)        
        
        else:        
                print "Here in no directpl"
        """        
        self.onLayoutFinish.append(self.start)
               
    def start2(self):
        desc = " "
        self.session.open(Playvid2, self.name, self.url, desc)
        self.close()

    def start3(self):
        from stream import GreekStreamTVList
        self.session.open(GreekStreamTVList, streamFile = "/tmp/stream.xml")
        self.close()

    def start4(self):
                       from Playlist import Playlist
                       self.session.open(Playlist, self.url)
                       self.close()       
    def start5(self): 
         self.pop = 1 
         n1 = self.url.find("video_id", 0)
         n2 = self.url.find("=", n1)
         vid = self.url[(n2+1):] 
         cmd = "python '/usr/lib/enigma2/python/Plugins/Extensions/KodiDirect/plugins/plugin.video.youtube/default.py' '6' '?plugin://plugin.video.youtube/play/?video_id=" + vid + "' &"
         self.p = os.popen(cmd)
               
    def start(self):
        print("Here in start")
        infotxt=(_("Selected video: ")) + self.name
        self['info'].setText(infotxt)
        showlist(self.list, self['list'])
    
    def openTest(self):
        pass
        
    def play(self):
        desc = " "
        if self.icount == 0:
               url = self.url
               if url.startswith("rtmp"):
                      url = url + " timeout=15"
               name = self.name
               if "m3u8" in url:
#                      if "shahid.net" in url:
                            print("shahid url = ", url)
                            try:os.remove("/tmp/hls.avi")
                            except:pass                          
#                            url=url.split("?hls")[0]                      
                            cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/IPTVplay/lib/hlsclient.py" "' + url + '" "1" &'
#ok                            cmd = 'python "/usr/lib/enigma2/python/hlsclient.py" "' + url + '" "1" > /tmp/hls.txt 2>&1 &'
#                            cmd = 'python "/usr/lib/enigma2/python/hlsclient.py" "' + url + '" "1" &'
                            print("hls cmd = ", cmd)
                            os.system(cmd)
                            os.system('sleep 3')
                            url = '/tmp/hls.avi'
        else:
               url = self.svfile
               name = "Video"
        self.session.open(Playstream, name, url)
               
    def getlocal_filename(self):
                       fold = config.plugins.kodiplug.cachefold.value+"/"
                       name = self.name.replace("/media/hdd/xbmc/vid/", "")
                       name = name.replace(" ", "-")
                       pattern = '[a-zA-Z0-9\-]'
                       input = name
                       output = ''.join(re.findall(pattern, input))
                       self.name = output
                       if self.url.endswith("mp4"):
                          svfile = fold + self.name+".mp4"
                       elif self.url.endswith("flv"):   
                          svfile = fold + self.name+".flv"
                       elif self.url.endswith("avi"):   
                          svfile = fold + self.name+".avi"                        
                       elif self.url.endswith("ts"):   
                          svfile = fold + self.name+".ts"                        
                       else:  
                          svfile = fold + self.name+".mpg"
                       filetitle=os.path.split(svfile)[1]    
                       return svfile,filetitle   
                          
                               
    def okClicked(self):
          
          idx=self["list"].getSelectionIndex()
          print("idx",idx)
          if idx==0:
             self.play()
          elif idx==1:
                try:
                      from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
                      self.serverList = vlcServerConfig.getServerlist()
                      if len(self.serverList) == 0:
                          self.session.open(MessageBox, "No server configured in VlcPlayer Plugin!", MessageBox.TYPE_ERROR)
                      elif len(self.serverList) == 1:
                          self.playfile(0)
                      else:
                          self.playfile(0)
                except:
                      txt = _("Plugin VlcPlayer is not installed.\nPlease install it and set it up.")
                      self.session.open(MessageBox, "Plugin VlcPlayer is not installed!", MessageBox.TYPE_ERROR)


          elif idx==2: ##mfaraj2608 to new way to download videos
                print("In Playvid Download") 
                if "#header#" in self.url:
                       self.svfile,self.filetitle = self.getlocal_filename()
                       cmd1 = "rm " + self.svfile
                       os.system(cmd1)
                       n1 = self.url.find("#header#", 0)
                       header = self.url[(n1+8):]
                       self.url = self.url[:n1]
                       cmd = 'wget -O "' + self.svfile + '" --header="' + header + '" --user-agent="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36" "' + self.url + '" &'
                       print("In Playvid cmd =", cmd)
                       os.system(cmd)
                       self.icount = 1
                       return
                
                if self.url.startswith("https"):
                       self.icount = 1
                       self.svfile,self.filetitle = self.getlocal_filename()
                       downloadPage(self.url, self.svfile).addErrback(self.showError)
                
                elif "rtmp" in self.url:
                       params = self.url
                       print("params A=", params)
                       params = "'" + params + "'"
                       params = params.replace(" swfVfy=", "' --swfVfy '")
                       params = params.replace(" playpath=", "' --playpath '")
                       params = params.replace(" app=", "' --app '")
                       params = params.replace(" pageUrl=", "' --pageUrl '")
                       params = params.replace(" tcUrl=", "' --tcUrl '")
                       params = params.replace(" swfUrl=", "' --swfUrl '") 
                       print("params B=", params)
                       
                       self.svfile,self.filetitle = self.getlocal_filename()
                       self.urtmp = "rtmpdump -r " + params + " -o '" + self.svfile + "'"
                       self["info"].setText(_("Start downloading"))
                       self.icount = 1
                       cmd = "rm " + self.svfile
                       print("rtmp cmd =", cmd)
                       os.system(cmd)
                       JobManager.AddJob(downloadJob(self, self.urtmp, self.svfile, 'Title 1')) 
                       self.LastJobView()

                elif "plugin://plugin.video.youtube" in self.url or "youtube.com/" in self.url :
                       from tube_resolver.plugin import getvideo
                       self.url,error = getvideo(self.url)
                       print("Here in Playvid youtube self.url =", self.url)
                       if error is not None or self.url is None:
                               print("failed to get valid youtube stream link")
                               return 
                       self.svfile,self.filetitle = self.getlocal_filename()
                       startdownload(self.session,answer='download',myurl=self.url,filename=self.svfile,title=self.filetitle)                       


                else:
                       self.svfile,self.filetitle = self.getlocal_filename()
                       startdownload(self.session,answer='download',myurl=self.url,filename=self.svfile,title=self.filetitle)                       

          elif idx==3:
                       self.stopDL() 

          elif idx==4:
               print('add to favorite')
               from favorites import addfavorite
               import sys
               
               try:
                  addon_id=os.path.split(os.path.split(sys.argv[0])[0])[1]
                  print("470add_id",addon_id)
                  result=addfavorite(addon_id,self.name,self.url)
               except:
                   result=False
               if result==False:
                   print("failed to add to favorites")
                   self.session.open(MessageBox, _("Failed to add to favorites."), MessageBox.TYPE_ERROR, timeout = 4)
               else:
                   print("added to favorites")
                   self.session.open(MessageBox, _("Item added successfully to favorites."), MessageBox.TYPE_INFO, timeout = 4)
                  
          elif idx==5:
            try:error=stream2bouquet(self.url,self.name,'XBMCAddons_streams')
            except:error=(_("Failed to add stream to bouquet"))        
            if error=='none':
               self.session.open(MessageBox, _((_('Stream added to '))+'XBMCAddons_streams '+ (_('bouquet\nrestart enigma to refresh bouquets'))), MessageBox.TYPE_INFO, timeout = 10)
            else:
               self.session.open(MessageBox, _("Failed to add stream to bouquet."), MessageBox.TYPE_ERROR, timeout = 4)
          elif idx==6:
               from XBMCAddonsMediaExplorer import XBMCAddonsMediaExplorer
               self.session.open(XBMCAddonsMediaExplorer) 

         
    def playfile(self, serverint):
        self.serverList[serverint].play(self.session, self.url, self.name)
        

    def showError(self, error):
               print("DownloadPage error = ", error)

  
    def updateStatus(self):
#        print "self.icount =", self.icount
#     print "In updateStatus self.pop =", self.pop
     if self.pop == 1:
            try:
               ptxt = self.p.read()
#               print "In updateStatus ptxt =", ptxt
               if "data B" in ptxt:
                      n1 = ptxt.find("data B", 0)
                      n2 = ptxt.find("&url", n1)
                      n3 = ptxt.find("\n", n2) 
                      url = ptxt[(n2+5):n3]  
                      url = url.replace("AxNxD", "&")
                      self.url = url.replace("ExQ", "=")  
#                      print "In updateStatus url =", url
                      name = "Video"
                      desc = " "
                      self.session.open(Playvid, self.name, self.url, desc)
                      self.close()
                      self.updateTimer.stop()
#               else:
#                      self.openTest()
#                      return       
            except:
               self.openTest()
#               return   
     else:
        if not os.path.exists(self.svfile):
            print("No self.svfile =", self.svfile) 
            self.openTest()
            return
             
        if self.icount == 0:
            self.openTest()
            return 
        
#        print "Exists self.svfile =", self.svfile
        b1 = os.path.getsize(self.svfile)
#        print "b1 =", b1
        b = b1 / 1000
        if b == self.bLast:
            infotxt = _('Download Complete....') + str(b)
            self['info'].setText(infotxt)
            return 
        self.bLast = b
        infotxt = _('Downloading....') + str(b) + ' kb'
        self['info'].setText(infotxt)

    def LastJobView(self):
        currentjob = None
        for job in JobManager.getPendingJobs():
            currentjob = job

        if currentjob is not None:
            self.session.open(JobViewNew, currentjob)

    def cancel(self):
           cmd = "rm -f " + self.svfile
           os.system(cmd) 
           cmd = "rm -f '/tmp/hls.avi'"
           os.system(cmd) 
           Screen.close(self, False)

    def stopDL(self):
                cmd = "rm -f " + self.svfile
                os.system(cmd)                
                self.session.nav.playService(self.srefOld)
                cmd1 = "killall -9 rtmpdump"
                cmd2 = "killall -9 wget"
                os.system(cmd1)
                os.system(cmd2)
                self['info'].setText("Current download task stopped")
                self.close()

    def keyLeft(self):
        self['text'].left()

    def keyRight(self):
        self['text'].right()

    def keyNumberGlobal(self, number):
        self['text'].number(number)

#class Playvid2(Screen, InfoBarMenu, InfoBarBase, SubsSupport, InfoBarSeek, InfoBarNotifications, InfoBarShowHide):
class Playstream(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarShowHide):
    
    def __init__(self, session, name, url):
        
                Screen.__init__(self, session)
                self.skinName = "MoviePlayer"
                title = "Play"
                self["list"] = MenuList([])
                InfoBarMenu.__init__(self)
                InfoBarNotifications.__init__(self)
                InfoBarBase.__init__(self)
                InfoBarShowHide.__init__(self)
                self["actions"] = ActionMap(["WizardActions", "MoviePlayerActions", "EPGSelectActions", "MediaPlayerSeekActions", "ColorActions", "InfobarShowHideActions", "InfobarActions"],
                {
                    "leavePlayer":              self.cancel,
                    "back":             self.cancel,
                }, -1)

                self.allowPiP = False
                InfoBarSeek.__init__(self, actionmap = "MediaPlayerSeekActions")
                url = url.replace(":", "%3a")
                self.url = url
                self.name = name
                print("Here in Playstream self.url = ", self.url)
                self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
                self.onLayoutFinish.append(self.openTest)

    def openTest(self):                
                url = self.url
                print("Here in Playstream self.url B= ", url)
                ref = "4097:0:1:0:0:0:0:0:0:0:" + url
#                ref = "4097:0:1:0:0:0:0:0:0:3:" + url
                print("Here in Playstream ref = ", ref)
#                ref = eServiceReference(0x1001, 0, url)
                sref = eServiceReference(ref)
                sref.setName(self.name)
                self.session.nav.stopService()
                self.session.nav.playService(sref)
           

    def cancel(self):
                self.session.nav.stopService()
                self.session.nav.playService(self.srefOld)
                self.close()

    def keyLeft(self):
            self["text"].left()
	
    def keyRight(self):
            self["text"].right()
	
    def keyNumberGlobal(self, number):
        self["text"].number(number) 


		

class downloadJob(Job):
        def __init__(self, toolbox, cmdline, filename, filetitle):
                Job.__init__(self, _("Saving Video"))
                self.toolbox = toolbox
                self.retrycount = 0
                downloadTask(self, cmdline, filename, filetitle)

        def retry(self):
            assert self.status == self.FAILED
            self.retrycount += 1
            self.restart()
	
class downloadTask(Task):
        ERROR_CORRUPT_FILE, ERROR_RTMP_ReadPacket, ERROR_SEGFAULT, ERROR_SERVER, ERROR_UNKNOWN = list(range(5))
        def __init__(self, job, cmdline, filename, filetitle):
                Task.__init__(self, job, filetitle)
                self.setCmdline(cmdline)
                self.filename = filename
                self.toolbox = job.toolbox
                self.error = None
                self.lasterrormsg = None
            
        def processOutput(self, data):
            try:
                if data.endswith('%)'):
                    startpos = data.rfind("sec (")+5
                    if startpos and startpos != -1:
                        self.progress = int(float(data[startpos:-4]))
                elif data.find('%') != -1:
                    tmpvalue = data[:data.find("%")]
                    tmpvalue = tmpvalue[tmpvalue.rfind(" "):].strip()
                    tmpvalue = tmpvalue[tmpvalue.rfind("(")+1:].strip()
                    self.progress = int(float(tmpvalue))
                else:
                    Task.processOutput(self, data)
            except Exception as errormsg:
                Task.processOutput(self, data)

        def processOutputLine(self, line):
                self.error = self.ERROR_SERVER
                
        def afterRun(self):
            pass



#lululla edit        
class webcamList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if DESKHEIGHT > 1000:
            self.l.setItemHeight(50)
            self.l.setFont(0, gFont('Regular', 40))
        else:
            self.l.setItemHeight(40)
            self.l.setFont(0, gFont('Regular', 23))        

##################            
            
            
class RSList(MenuList):
        def __init__(self, list):
            MenuList.__init__(self, list, True, eListboxPythonMultiContent)
            self.l.setItemHeight(40)
            textfont = int(25)
            self.l.setFont(0, gFont("Regular", textfont))
                    

def RSListEntry(download):
        res = [(download)]

        white = 0xffffff 
        grey = 0xb3b3b9
        green = 0x389416
        black = 0x000000
        yellow = 0xe5b243
        blue = 0x002d39
        red = 0xf07655
        col = 0xffffff
        colsel = 0xf07655
        backcol = 0x000000
        backsel = 0x000000
#        res.append(MultiContentEntryText(pos=(0, 0), size=(650, 40), text=download, color=col, color_sel = colsel, backcolor = backcol, backcolor_sel = backcol))
        res.append(MultiContentEntryText(pos=(0, 0), size=(1000, 40), text=download, color=col, color_sel = colsel, backcolor = backcol, backcolor_sel = backcol))
        return res

                  
def showlist(data, list):                   
                   icount = 0
                   plist = []
                   for line in data:
#                               print "In showlist line =", line
                           name = data[icount]            

                           plist.append(RSListEntry(name))                               
                           icount = icount+1

                   list.setList(plist)
                        #list.sort() 


#################                

def getserviceinfo(sref):## this def returns the current playing service name and stream_url from give sref
          try:
                    p=ServiceReference(sref)
                    servicename=str(p.getServiceName())
                    serviceurl=str(p.getPath())
                    return servicename,serviceurl
          except:
                return None,None
                
def getVideoUrl(vid):
        VIDEO_FMT_PRIORITY_MAP = {
            '38' : 1, #MP4 Original (HD)
            '37' : 2, #MP4 1080p (HD)
            '22' : 3, #MP4 720p (HD)
            '18' : 4, #MP4 360p
            '35' : 5, #FLV 480p
            '34' : 6, #FLV 360p
        }
        video_url = None
        video_id = vid

        # Getting video webpage
        #URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
        watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id
        watchrequest = Request(watch_url, None, std_headers)
        try:
            print("[MyTube] trying to find out if a HD Stream is available",watch_url)
            watchvideopage = urlopen(watchrequest).read()
        except (URLError, HTTPException, socket.error) as err:
            print("[MyTube] Error: Unable to retrieve watchpage - Error code: ", str(err))
            return None

        # Get video info
        for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el))
            request = Request(info_url, None, std_headers)
            try:
                infopage = urlopen(request).read()
                videoinfo = parse_qs(infopage)
                if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
                    break
            except (URLError, HTTPException, socket.error) as err:
                print("[MyTube] Error: unable to download video infopage",str(err))
                return None

        if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
            # Attempt to see if YouTube has issued an error message
            if 'reason' not in videoinfo:
                print('[MyTube] Error: unable to extract "fmt_url_map" or "url_encoded_fmt_stream_map" parameter for unknown reason')
            else:
                reason = unquote_plus(videoinfo['reason'][0])
                print('[MyTube] Error: YouTube said: %s' % reason.decode('utf-8'))
            return None

        video_fmt_map = {}
        fmt_infomap = {}
        if 'url_encoded_fmt_stream_map' in videoinfo:
            tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
        else:
            tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
            for fmtstring in tmp_fmtUrlDATA:
                fmturl = fmtid = ""
                if 'url_encoded_fmt_stream_map' in videoinfo:
                        try:
                                    for arg in fmtstring.split('&'):
                                        if arg.find('=') >= 0:
                                            print(arg.split('='))
                                            key, value = arg.split('=')
                                            if key == 'itag':
                                                if len(value) > 3:
                                                    value = value[:2]
                                                fmtid = value
                                            elif key == 'url':
                                                fmturl = value

                                        if fmtid != "" and fmturl != "" and fmtid in VIDEO_FMT_PRIORITY_MAP:
                                            video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl)}
                                            fmt_infomap[int(fmtid)] = "%s" %(unquote_plus(fmturl))
                                        fmturl = fmtid = ""

                        except:
                            print("error parsing fmtstring:",fmtstring)
                            return None
                    
            else:
                (fmtid,fmturl) = fmtstring.split('|')
                if fmtid in VIDEO_FMT_PRIORITY_MAP and fmtid != "":
                    video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
                    fmt_infomap[int(fmtid)] = unquote_plus(fmturl)
                    print("[MyTube] got",sorted(fmt_infomap.keys()))
                if video_fmt_map and len(video_fmt_map):
                    print("[MyTube] found best available video format:",video_fmt_map[sorted(video_fmt_map.keys())[0]]['fmtid'])
                    best_video = video_fmt_map[sorted(video_fmt_map.keys())[0]]
                    video_url = "%s" %(best_video['fmturl'].split(';')[0])
                    print("[MyTube] found best available video url:",video_url)
                else:   
                    return None
                return video_url



#######################################    

def addstreamboq(bouquetname=None):
           boqfile="/etc/enigma2/bouquets.tv"
           if not os.path.exists(boqfile):
              pass
           else:
              fp=open(boqfile,"r")
              lines=fp.readlines()
              fp.close()
              add=True
              for line in lines:
                 
                 if "userbouquet."+bouquetname+".tv" in line :
                    
                    add=False
                    break
           if add==True:   
              fp=open(boqfile,"a")                               
              fp.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.%s.tv" ORDER BY bouquet\n'% bouquetname) 
              fp.close()
              add=True


def stream2bouquet(url=None,name=None,bouquetname=None):
          error='none' 
          bouquetname='XBMCAddons'                              
          fileName ="/etc/enigma2/userbouquet.%s.tv" % bouquetname
          out = '#SERVICE 4097:0:0:0:0:0:0:0:0:0:%s:%s\r\n' % (urllib.quote(url), urllib.quote(name))
          #py3
          #out = '#SERVICE 4097:0:0:0:0:0:0:0:0:0:%s:%s\r\n' % (urllib.parse.quote(url), urllib.parse.quote(name))
          
          try:
              addstreamboq(bouquetname)
              if not os.path.exists(fileName):
                 fp = open(fileName, 'w')
                 fp.write("#NAME %s\n"%bouquetname) 
                 fp.close()
                 fp = open(fileName, 'a')                          
                 fp.write(out)                 
              else:
                 fp=open(fileName,'r')
                 lines=fp.readlines()
                 fp.close()
                 for line in lines:
                     if out in line:
                        error=(_('Stream already added to bouquet'))
                        return error
                 fp = open(fileName, 'a')                          
                 fp.write(out)                 
              fp.write("")
              fp.close()              
          except:
             error=(_('Adding to bouquet failed'))
          return error
          
##added for need of aspect ratio
class StatusScreen(Screen):

    def __init__(self, session):
        desktop = getDesktop(0)
        size = desktop.size()
        self.sc_width = size.width()
        self.sc_height = size.height()
        statusPositionX = 50
        statusPositionY = 100
        self.delayTimer = eTimer()
        try:
               self.delayTimer_conn = self.delayTimer.timeout.connect(self.hideStatus)
        except AttributeError:
               self.delayTimer.callback.append(self.hideStatus)
        
        self.delayTimerDelay = 1500
        self.shown = True
        self.skin = '\n            <screen name="StatusScreen" position="%s,%s" size="%s,90" zPosition="0" backgroundColor="transparent" flags="wfNoBorder">\n                    <widget name="status" position="0,0" size="%s,70" valign="center" halign="left" font="Regular;22" transparent="1" foregroundColor="yellow" shadowColor="#40101010" shadowOffset="3,3" />\n            </screen>' % (str(statusPositionX),
         str(statusPositionY),
         str(self.sc_width),
         str(self.sc_width))
        Screen.__init__(self, session)
        self.stand_alone = True
        print('initializing status display')
        self['status'] = Label('')
        self.onClose.append(self.__onClose)

    def setStatus(self, text, color = 'yellow'):
        self['status'].setText(text)
        self['status'].instance.setForegroundColor(parseColor(color))
        self.show()
        self.delayTimer.start(self.delayTimerDelay, True)

    def hideStatus(self):
        self.hide()
        self['status'].setText('')

    def __onClose(self):
        self.delayTimer.stop()
        del self.delayTimer

