# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/KodiLite/plugins/plugin.video.YTtest/youtube_dl/extractor/adobepass.py
from __future__ import unicode_literals
import re
import time
import xml.etree.ElementTree as etree
from .common import InfoExtractor
from ..compat import compat_kwargs, compat_urlparse
from ..utils import unescapeHTML, urlencode_postdata, unified_timestamp, ExtractorError, NO_DEFAULT
MSO_INFO = {u'DTV': {u'name': u'DIRECTV',
          u'username_field': u'username',
          u'password_field': u'password'},
 u'ATT': {u'name': u'AT&T U-verse',
          u'username_field': u'userid',
          u'password_field': u'password'},
 u'ATTOTT': {u'name': u'DIRECTV NOW',
             u'username_field': u'email',
             u'password_field': u'loginpassword'},
 u'Rogers': {u'name': u'Rogers',
             u'username_field': u'UserName',
             u'password_field': u'UserPassword'},
 u'Comcast_SSO': {u'name': u'Comcast XFINITY',
                  u'username_field': u'user',
                  u'password_field': u'passwd'},
 u'TWC': {u'name': u'Time Warner Cable | Spectrum',
          u'username_field': u'Ecom_User_ID',
          u'password_field': u'Ecom_Password'},
 u'Brighthouse': {u'name': u'Bright House Networks | Spectrum',
                  u'username_field': u'j_username',
                  u'password_field': u'j_password'},
 u'Charter_Direct': {u'name': u'Charter Spectrum',
                     u'username_field': u'IDToken1',
                     u'password_field': u'IDToken2'},
 u'Verizon': {u'name': u'Verizon FiOS',
              u'username_field': u'IDToken1',
              u'password_field': u'IDToken2'},
 u'thr030': {u'name': u'3 Rivers Communications'},
 u'com140': {u'name': u'Access Montana'},
 u'acecommunications': {u'name': u'AcenTek'},
 u'acm010': {u'name': u'Acme Communications'},
 u'ada020': {u'name': u'Adams Cable Service'},
 u'alb020': {u'name': u'Albany Mutual Telephone'},
 u'algona': {u'name': u'Algona Municipal Utilities'},
 u'allwest': {u'name': u'All West Communications'},
 u'all025': {u'name': u"Allen's Communications"},
 u'spl010': {u'name': u'Alliance Communications'},
 u'all070': {u'name': u'ALLO Communications'},
 u'alpine': {u'name': u'Alpine Communications'},
 u'hun015': {u'name': u'American Broadband'},
 u'nwc010': {u'name': u'American Broadband Missouri'},
 u'com130-02': {u'name': u'American Community Networks'},
 u'com130-01': {u'name': u'American Warrior Networks'},
 u'tom020': {u'name': u'Amherst Telephone/Tomorrow Valley'},
 u'tvc020': {u'name': u'Andycable'},
 u'arkwest': {u'name': u'Arkwest Communications'},
 u'art030': {u'name': u'Arthur Mutual Telephone Company'},
 u'arvig': {u'name': u'Arvig'},
 u'nttcash010': {u'name': u'Ashland Home Net'},
 u'astound': {u'name': u'Astound (now Wave)'},
 u'dix030': {u'name': u'ATC Broadband'},
 u'ara010': {u'name': u'ATC Communications'},
 u'she030-02': {u'name': u'Ayersville Communications'},
 u'baldwin': {u'name': u'Baldwin Lightstream'},
 u'bal040': {u'name': u'Ballard TV'},
 u'cit025': {u'name': u'Bardstown Cable TV'},
 u'bay030': {u'name': u'Bay Country Communications'},
 u'tel095': {u'name': u'Beaver Creek Cooperative Telephone'},
 u'bea020': {u'name': u'Beaver Valley Cable'},
 u'bee010': {u'name': u'Bee Line Cable'},
 u'wir030': {u'name': u'Beehive Broadband'},
 u'bra020': {u'name': u'BELD'},
 u'bel020': {u'name': u'Bellevue Municipal Cable'},
 u'vol040-01': {u'name': u'Ben Lomand Connect / BLTV'},
 u'bev010': {u'name': u'BEVCOMM'},
 u'big020': {u'name': u'Big Sandy Broadband'},
 u'ble020': {u'name': u'Bledsoe Telephone Cooperative'},
 u'bvt010': {u'name': u'Blue Valley Tele-Communications'},
 u'bra050': {u'name': u'Brandenburg Telephone Co.'},
 u'bte010': {u'name': u'Bristol Tennessee Essential Services'},
 u'annearundel': {u'name': u'Broadstripe'},
 u'btc010': {u'name': u'BTC Communications'},
 u'btc040': {u'name': u'BTC Vision - Nahunta'},
 u'bul010': {u'name': u'Bulloch Telephone Cooperative'},
 u'but010': {u'name': u'Butler-Bremer Communications'},
 u'tel160-csp': {u'name': u'C Spire SNAP'},
 u'csicable': {u'name': u'Cable Services Inc.'},
 u'cableamerica': {u'name': u'CableAmerica'},
 u'cab038': {u'name': u'CableSouth Media 3'},
 u'weh010-camtel': {u'name': u'Cam-Tel Company'},
 u'car030': {u'name': u'Cameron Communications'},
 u'canbytel': {u'name': u'Canby Telcom'},
 u'crt020': {u'name': u'CapRock Tv'},
 u'car050': {u'name': u'Carnegie Cable'},
 u'cas': {u'name': u'CAS Cable'},
 u'casscomm': {u'name': u'CASSCOMM'},
 u'mid180-02': {u'name': u'Catalina Broadband Solutions'},
 u'cccomm': {u'name': u'CC Communications'},
 u'nttccde010': {u'name': u'CDE Lightband'},
 u'cfunet': {u'name': u'Cedar Falls Utilities'},
 u'dem010-01': {u'name': u'Celect-Bloomer Telephone Area'},
 u'dem010-02': {u'name': u'Celect-Bruce Telephone Area'},
 u'dem010-03': {u'name': u'Celect-Citizens Connected Area'},
 u'dem010-04': {u'name': u'Celect-Elmwood/Spring Valley Area'},
 u'dem010-06': {u'name': u'Celect-Mosaic Telecom'},
 u'dem010-05': {u'name': u'Celect-West WI Telephone Area'},
 u'net010-02': {u'name': u'Cellcom/Nsight Telservices'},
 u'cen100': {u'name': u'CentraCom'},
 u'nttccst010': {u'name': u'Central Scott / CSTV'},
 u'cha035': {u'name': u'Chaparral CableVision'},
 u'cha050': {u'name': u'Chariton Valley Communication Corporation, Inc.'},
 u'cha060': {u'name': u'Chatmoss Cablevision'},
 u'nttcche010': {u'name': u'Cherokee Communications'},
 u'che050': {u'name': u'Chesapeake Bay Communications'},
 u'cimtel': {u'name': u'Cim-Tel Cable, LLC.'},
 u'cit180': {u'name': u'Citizens Cablevision - Floyd, VA'},
 u'cit210': {u'name': u'Citizens Cablevision, Inc.'},
 u'cit040': {u'name': u'Citizens Fiber'},
 u'cit250': {u'name': u'Citizens Mutual'},
 u'war040': {u'name': u'Citizens Telephone Corporation'},
 u'wat025': {u'name': u'City Of Monroe'},
 u'wadsworth': {u'name': u'CityLink'},
 u'nor100': {u'name': u'CL Tel'},
 u'cla010': {u'name': u'Clarence Telephone and Cedar Communications'},
 u'ser060': {u'name': u'Clear Choice Communications'},
 u'tac020': {u'name': u'Click! Cable TV'},
 u'war020': {u'name': u'CLICK1.NET'},
 u'cml010': {u'name': u'CML Telephone Cooperative Association'},
 u'cns': {u'name': u'CNS'},
 u'com160': {u'name': u'Co-Mo Connect'},
 u'coa020': {u'name': u'Coast Communications'},
 u'coa030': {u'name': u'Coaxial Cable TV'},
 u'mid055': {u'name': u'Cobalt TV (Mid-State Community TV)'},
 u'col070': {u'name': u'Columbia Power & Water Systems'},
 u'col080': {u'name': u'Columbus Telephone'},
 u'nor105': {u'name': u'Communications 1 Cablevision, Inc.'},
 u'com150': {u'name': u'Community Cable & Broadband'},
 u'com020': {u'name': u'Community Communications Company'},
 u'coy010': {u'name': u'commZoom'},
 u'com025': {u'name': u'Complete Communication Services'},
 u'cat020': {u'name': u'Comporium'},
 u'com071': {u'name': u'ComSouth Telesys'},
 u'consolidatedcable': {u'name': u'Consolidated'},
 u'conwaycorp': {u'name': u'Conway Corporation'},
 u'coo050': {u'name': u'Coon Valley Telecommunications Inc'},
 u'coo080': {u'name': u'Cooperative Telephone Company'},
 u'cpt010': {u'name': u'CP-TEL'},
 u'cra010': {u'name': u'Craw-Kan Telephone'},
 u'crestview': {u'name': u'Crestview Cable Communications'},
 u'cross': {u'name': u'Cross TV'},
 u'cro030': {u'name': u'Crosslake Communications'},
 u'ctc040': {u'name': u'CTC - Brainerd MN'},
 u'phe030': {u'name': u'CTV-Beam - East Alabama'},
 u'cun010': {u'name': u'Cunningham Telephone & Cable'},
 u'dpc010': {u'name': u'D & P Communications'},
 u'dak030': {u'name': u'Dakota Central Telecommunications'},
 u'nttcdel010': {u'name': u'Delcambre Telephone LLC'},
 u'tel160-del': {u'name': u'Delta Telephone Company'},
 u'sal040': {u'name': u'DiamondNet'},
 u'ind060-dc': {u'name': u'Direct Communications'},
 u'doy010': {u'name': u'Doylestown Cable TV'},
 u'dic010': {u'name': u'DRN'},
 u'dtc020': {u'name': u'DTC'},
 u'dtc010': {u'name': u'DTC Cable (Delhi)'},
 u'dum010': {u'name': u'Dumont Telephone Company'},
 u'dun010': {u'name': u'Dunkerton Telephone Cooperative'},
 u'cci010': {u'name': u'Duo County Telecom'},
 u'eagle': {u'name': u'Eagle Communications'},
 u'weh010-east': {u'name': u'East Arkansas Cable TV'},
 u'eatel': {u'name': u'EATEL Video, LLC'},
 u'ell010': {u'name': u'ECTA'},
 u'emerytelcom': {u'name': u'Emery Telcom Video LLC'},
 u'nor200': {u'name': u'Empire Access'},
 u'endeavor': {u'name': u'Endeavor Communications'},
 u'sun045': {u'name': u'Enhanced Telecommunications Corporation'},
 u'mid030': {u'name': u'enTouch'},
 u'epb020': {u'name': u'EPB Smartnet'},
 u'jea010': {u'name': u'EPlus Broadband'},
 u'com065': {u'name': u'ETC'},
 u'ete010': {u'name': u'Etex Communications'},
 u'fbc-tele': {u'name': u'F&B Communications'},
 u'fal010': {u'name': u'Falcon Broadband'},
 u'fam010': {u'name': u'FamilyView CableVision'},
 u'far020': {u'name': u'Farmers Mutual Telephone Company'},
 u'fay010': {u'name': u'Fayetteville Public Utilities'},
 u'sal060': {u'name': u'fibrant'},
 u'fid010': {u'name': u'Fidelity Communications'},
 u'for030': {u'name': u'FJ Communications'},
 u'fli020': {u'name': u'Flint River Communications'},
 u'far030': {u'name': u'FMT - Jesup'},
 u'foo010': {u'name': u'Foothills Communications'},
 u'for080': {u'name': u'Forsyth CableNet'},
 u'fbcomm': {u'name': u'Frankfort Plant Board'},
 u'tel160-fra': {u'name': u'Franklin Telephone Company'},
 u'nttcftc010': {u'name': u'FTC'},
 u'fullchannel': {u'name': u'Full Channel, Inc.'},
 u'gar040': {u'name': u'Gardonville Cooperative Telephone Association'},
 u'gbt010': {u'name': u'GBT Communications, Inc.'},
 u'tec010': {u'name': u'Genuine Telecom'},
 u'clr010': {u'name': u'Giant Communications'},
 u'gla010': {u'name': u'Glasgow EPB'},
 u'gle010': {u'name': u'Glenwood Telecommunications'},
 u'gra060': {u'name': u'GLW Broadband Inc.'},
 u'goldenwest': {u'name': u'Golden West Cablevision'},
 u'vis030': {u'name': u'Grantsburg Telcom'},
 u'gpcom': {u'name': u'Great Plains Communications'},
 u'gri010': {u'name': u'Gridley Cable Inc'},
 u'hbc010': {u'name': u'H&B Cable Services'},
 u'hae010': {u'name': u'Haefele TV Inc.'},
 u'htc010': {u'name': u'Halstad Telephone Company'},
 u'har005': {u'name': u'Harlan Municipal Utilities'},
 u'har020': {u'name': u'Hart Communications'},
 u'ced010': {u'name': u'Hartelco TV'},
 u'hea040': {u'name': u'Heart of Iowa Communications Cooperative'},
 u'htc020': {u'name': u'Hickory Telephone Company'},
 u'nttchig010': {u'name': u'Highland Communication Services'},
 u'hig030': {u'name': u'Highland Media'},
 u'spc010': {u'name': u'Hilliary Communications'},
 u'hin020': {u'name': u'Hinton CATV Co.'},
 u'hometel': {u'name': u'HomeTel Entertainment, Inc.'},
 u'hoodcanal': {u'name': u'Hood Canal Communications'},
 u'weh010-hope': {u'name': u'Hope - Prescott Cable TV'},
 u'horizoncable': {u'name': u'Horizon Cable TV, Inc.'},
 u'hor040': {u'name': u'Horizon Chillicothe Telephone'},
 u'htc030': {u'name': u'HTC Communications Co. - IL'},
 u'htccomm': {u'name': u'HTC Communications, Inc. - IA'},
 u'wal005': {u'name': u'Huxley Communications'},
 u'imon': {u'name': u'ImOn Communications'},
 u'ind040': {u'name': u'Independence Telecommunications'},
 u'rrc010': {u'name': u'Inland Networks'},
 u'stc020': {u'name': u'Innovative Cable TV St Croix'},
 u'car100': {u'name': u'Innovative Cable TV St Thomas-St John'},
 u'icc010': {u'name': u'Inside Connect Cable'},
 u'int100': {u'name': u'Integra Telecom'},
 u'int050': {u'name': u'Interstate Telecommunications Coop'},
 u'irv010': {u'name': u'Irvine Cable'},
 u'k2c010': {u'name': u'K2 Communications'},
 u'kal010': {u'name': u'Kalida Telephone Company, Inc.'},
 u'kal030': {u'name': u'Kalona Cooperative Telephone Company'},
 u'kmt010': {u'name': u'KMTelecom'},
 u'kpu010': {u'name': u'KPU Telecommunications'},
 u'kuh010': {u'name': u'Kuhn Communications, Inc.'},
 u'lak130': {u'name': u'Lakeland Communications'},
 u'lan010': {u'name': u'Langco'},
 u'lau020': {u'name': u'Laurel Highland Total Communications, Inc.'},
 u'leh010': {u'name': u'Lehigh Valley Cooperative Telephone'},
 u'bra010': {u'name': u'Limestone Cable/Bracken Cable'},
 u'loc020': {u'name': u'LISCO'},
 u'lit020': {u'name': u'Litestream'},
 u'tel140': {u'name': u'LivCom'},
 u'loc010': {u'name': u'LocalTel Communications'},
 u'weh010-longview': {u'name': u'Longview - Kilgore Cable TV'},
 u'lon030': {u'name': u'Lonsdale Video Ventures, LLC'},
 u'lns010': {u'name': u'Lost Nation-Elwood Telephone Co.'},
 u'nttclpc010': {u'name': u'LPC Connect'},
 u'lumos': {u'name': u'Lumos Networks'},
 u'madison': {u'name': u'Madison Communications'},
 u'mad030': {u'name': u'Madison County Cable Inc.'},
 u'nttcmah010': {u'name': u'Mahaska Communication Group'},
 u'mar010': {u'name': u'Marne & Elk Horn Telephone Company'},
 u'mcc040': {u'name': u'McClure Telephone Co.'},
 u'mctv': {u'name': u'MCTV'},
 u'merrimac': {u'name': u'Merrimac Communications Ltd.'},
 u'metronet': {u'name': u'Metronet'},
 u'mhtc': {u'name': u'MHTC'},
 u'midhudson': {u'name': u'Mid-Hudson Cable'},
 u'midrivers': {u'name': u'Mid-Rivers Communications'},
 u'mid045': {u'name': u'Midstate Communications'},
 u'mil080': {u'name': u'Milford Communications'},
 u'min030': {u'name': u'MINET'},
 u'nttcmin010': {u'name': u'Minford TV'},
 u'san040-02': {u'name': u'Mitchell Telecom'},
 u'mlg010': {u'name': u'MLGC'},
 u'mon060': {u'name': u'Mon-Cre TVE'},
 u'mou110': {u'name': u'Mountain Telephone'},
 u'mou050': {u'name': u'Mountain Village Cable'},
 u'mtacomm': {u'name': u'MTA Communications, LLC'},
 u'mtc010': {u'name': u'MTC Cable'},
 u'med040': {u'name': u'MTC Technologies'},
 u'man060': {u'name': u'MTCC'},
 u'mtc030': {u'name': u'MTCO Communications'},
 u'mul050': {u'name': u'Mulberry Telecommunications'},
 u'mur010': {u'name': u'Murray Electric System'},
 u'musfiber': {u'name': u'MUS FiberNET'},
 u'mpw': {u'name': u'Muscatine Power & Water'},
 u'nttcsli010': {u'name': u'myEVTV.com'},
 u'nor115': {u'name': u'NCC'},
 u'nor260': {u'name': u'NDTC'},
 u'nctc': {u'name': u'Nebraska Central Telecom, Inc.'},
 u'nel020': {u'name': u'Nelsonville TV Cable'},
 u'nem010': {u'name': u'Nemont'},
 u'new075': {u'name': u'New Hope Telephone Cooperative'},
 u'nor240': {u'name': u'NICP'},
 u'cic010': {u'name': u'NineStar Connect'},
 u'nktelco': {u'name': u'NKTelco'},
 u'nortex': {u'name': u'Nortex Communications'},
 u'nor140': {u'name': u'North Central Telephone Cooperative'},
 u'nor030': {u'name': u'Northland Communications'},
 u'nor075': {u'name': u'Northwest Communications'},
 u'nor125': {u'name': u'Norwood Light Broadband'},
 u'net010': {u'name': u'Nsight Telservices'},
 u'dur010': {u'name': u'Ntec'},
 u'nts010': {u'name': u'NTS Communications'},
 u'new045': {u'name': u'NU-Telecom'},
 u'nulink': {u'name': u'NuLink'},
 u'jam030': {u'name': u'NVC'},
 u'far035': {u'name': u'OmniTel Communications'},
 u'onesource': {u'name': u'OneSource Communications'},
 u'cit230': {u'name': u'Opelika Power Services'},
 u'daltonutilities': {u'name': u'OptiLink'},
 u'mid140': {u'name': u'OPTURA'},
 u'ote010': {u'name': u'OTEC Communication Company'},
 u'cci020': {u'name': u'Packerland Broadband'},
 u'pan010': {u'name': u'Panora Telco/Guthrie Center Communications'},
 u'otter': {u'name': u'Park Region Telephone & Otter Tail Telcom'},
 u'mid050': {u'name': u'Partner Communications Cooperative'},
 u'fib010': {u'name': u'Pathway'},
 u'paulbunyan': {u'name': u'Paul Bunyan Communications'},
 u'pem020': {u'name': u'Pembroke Telephone Company'},
 u'mck010': {u'name': u'Peoples Rural Telephone Cooperative'},
 u'pul010': {u'name': u'PES Energize'},
 u'phi010': {u'name': u'Philippi Communications System'},
 u'phonoscope': {u'name': u'Phonoscope Cable'},
 u'pin070': {u'name': u'Pine Belt Communications, Inc.'},
 u'weh010-pine': {u'name': u'Pine Bluff Cable TV'},
 u'pin060': {u'name': u'Pineland Telephone Cooperative'},
 u'cam010': {u'name': u'Pinpoint Communications'},
 u'pio060': {u'name': u'Pioneer Broadband'},
 u'pioncomm': {u'name': u'Pioneer Communications'},
 u'pioneer': {u'name': u'Pioneer DTV'},
 u'pla020': {u'name': u'Plant TiftNet, Inc.'},
 u'par010': {u'name': u'PLWC'},
 u'pro035': {u'name': u'PMT'},
 u'vik011': {u'name': u'Polar Cablevision'},
 u'pottawatomie': {u'name': u'Pottawatomie Telephone Co.'},
 u'premiercomm': {u'name': u'Premier Communications'},
 u'psc010': {u'name': u'PSC'},
 u'pan020': {u'name': u'PTCI'},
 u'qco010': {u'name': u'QCOL'},
 u'qua010': {u'name': u'Quality Cablevision'},
 u'rad010': {u'name': u'Radcliffe Telephone Company'},
 u'car040': {u'name': u'Rainbow Communications'},
 u'rai030': {u'name': u'Rainier Connect'},
 u'ral010': {u'name': u'Ralls Technologies'},
 u'rct010': {u'name': u'RC Technologies'},
 u'red040': {u'name': u'Red River Communications'},
 u'ree010': {u'name': u'Reedsburg Utility Commission'},
 u'mol010': {u'name': u'Reliance Connects- Oregon'},
 u'res020': {u'name': u'Reserve Telecommunications'},
 u'weh010-resort': {u'name': u'Resort TV Cable'},
 u'rld010': {u'name': u'Richland Grant Telephone Cooperative, Inc.'},
 u'riv030': {u'name': u'River Valley Telecommunications Coop'},
 u'rockportcable': {u'name': u'Rock Port Cablevision'},
 u'rsf010': {u'name': u'RS Fiber'},
 u'rtc': {u'name': u'RTC Communication Corp'},
 u'res040': {u'name': u'RTC-Reservation Telephone Coop.'},
 u'rte010': {u'name': u'RTEC Communications'},
 u'stc010': {u'name': u'S&T'},
 u'san020': {u'name': u'San Bruno Cable TV'},
 u'san040-01': {u'name': u'Santel'},
 u'sav010': {u'name': u'SCI Broadband-Savage Communications Inc.'},
 u'sco050': {u'name': u'Scottsboro Electric Power Board'},
 u'scr010': {u'name': u'Scranton Telephone Company'},
 u'selco': {u'name': u'SELCO'},
 u'she010': {u'name': u'Shentel'},
 u'she030': {u'name': u'Sherwood Mutual Telephone Association, Inc.'},
 u'ind060-ssc': {u'name': u'Silver Star Communications'},
 u'sjoberg': {u'name': u"Sjoberg's Inc."},
 u'sou025': {u'name': u'SKT'},
 u'sky050': {u'name': u'SkyBest TV'},
 u'nttcsmi010': {u'name': u'Smithville Communications'},
 u'woo010': {u'name': u'Solarus'},
 u'sou075': {u'name': u'South Central Rural Telephone Cooperative'},
 u'sou065': {u'name': u'South Holt Cablevision, Inc.'},
 u'sou035': {u'name': u'South Slope Cooperative Communications'},
 u'spa020': {u'name': u'Spanish Fork Community Network'},
 u'spe010': {u'name': u'Spencer Municipal Utilities'},
 u'spi005': {u'name': u'Spillway Communications, Inc.'},
 u'srt010': {u'name': u'SRT'},
 u'cccsmc010': {u'name': u'St. Maarten Cable TV'},
 u'sta025': {u'name': u'Star Communications'},
 u'sco020': {u'name': u'STE'},
 u'uin010': {u'name': u'STRATA Networks'},
 u'sum010': {u'name': u'Sumner Cable TV'},
 u'pie010': {u'name': u'Surry TV/PCSI TV'},
 u'swa010': {u'name': u'Swayzee Communications'},
 u'sweetwater': {u'name': u'Sweetwater Cable Television Co'},
 u'weh010-talequah': {u'name': u'Tahlequah Cable TV'},
 u'tct': {u'name': u'TCT'},
 u'tel050': {u'name': u'Tele-Media Company'},
 u'com050': {u'name': u'The Community Agency'},
 u'thr020': {u'name': u'Three River'},
 u'cab140': {u'name': u'Town & Country Technologies'},
 u'tra010': {u'name': u'Trans-Video'},
 u'tre010': {u'name': u'Trenton TV Cable Company'},
 u'tcc': {u'name': u'Tri County Communications Cooperative'},
 u'tri025': {u'name': u'TriCounty Telecom'},
 u'tri110': {u'name': u'TrioTel Communications, Inc.'},
 u'tro010': {u'name': u'Troy Cablevision, Inc.'},
 u'tsc': {u'name': u'TSC'},
 u'cit220': {u'name': u'Tullahoma Utilities Board'},
 u'tvc030': {u'name': u'TV Cable of Rensselaer'},
 u'tvc015': {u'name': u'TVC Cable'},
 u'cab180': {u'name': u'TVision'},
 u'twi040': {u'name': u'Twin Lakes'},
 u'tvtinc': {u'name': u'Twin Valley'},
 u'uis010': {u'name': u'Union Telephone Company'},
 u'uni110': {u'name': u'United Communications - TN'},
 u'uni120': {u'name': u'United Services'},
 u'uss020': {u'name': u'US Sonet'},
 u'cab060': {u'name': u'USA Communications'},
 u'she005': {u'name': u'USA Communications/Shellsburg, IA'},
 u'val040': {u'name': u'Valley TeleCom Group'},
 u'val025': {u'name': u'Valley Telecommunications'},
 u'val030': {u'name': u'Valparaiso Broadband'},
 u'cla050': {u'name': u'Vast Broadband'},
 u'sul015': {u'name': u'Venture Communications Cooperative, Inc.'},
 u'ver025': {u'name': u'Vernon Communications Co-op'},
 u'weh010-vicksburg': {u'name': u'Vicksburg Video'},
 u'vis070': {u'name': u'Vision Communications'},
 u'volcanotel': {u'name': u'Volcano Vision, Inc.'},
 u'vol040-02': {u'name': u'VolFirst / BLTV'},
 u'ver070': {u'name': u'VTel'},
 u'nttcvtx010': {u'name': u'VTX1'},
 u'bci010-02': {u'name': u'Vyve Broadband'},
 u'wab020': {u'name': u'Wabash Mutual Telephone'},
 u'waitsfield': {u'name': u'Waitsfield Cable'},
 u'wal010': {u'name': u'Walnut Communications'},
 u'wavebroadband': {u'name': u'Wave'},
 u'wav030': {u'name': u'Waverly Communications Utility'},
 u'wbi010': {u'name': u'WBI'},
 u'web020': {u'name': u'Webster-Calhoun Cooperative Telephone Association'},
 u'wes005': {u'name': u'West Alabama TV Cable'},
 u'carolinata': {u'name': u'West Carolina Communications'},
 u'wct010': {u'name': u'West Central Telephone Association'},
 u'wes110': {u'name': u'West River Cooperative Telephone Company'},
 u'ani030': {u'name': u'WesTel Systems'},
 u'westianet': {u'name': u'Western Iowa Networks'},
 u'nttcwhi010': {u'name': u'Whidbey Telecom'},
 u'weh010-white': {u'name': u'White County Cable TV'},
 u'wes130': {u'name': u'Wiatel'},
 u'wik010': {u'name': u'Wiktel'},
 u'wil070': {u'name': u'Wilkes Communications, Inc./RiverStreet Networks'},
 u'wil015': {u'name': u'Wilson Communications'},
 u'win010': {u'name': u'Windomnet/SMBS'},
 u'win090': {u'name': u'Windstream Cable TV'},
 u'wcta': {u'name': u'Winnebago Cooperative Telecom Association'},
 u'wtc010': {u'name': u'WTC'},
 u'wil040': {u'name': u'WTC Communications, Inc.'},
 u'wya010': {u'name': u'Wyandotte Cable'},
 u'hin020-02': {u'name': u'X-Stream Services'},
 u'xit010': {u'name': u'XIT Communications'},
 u'yel010': {u'name': u'Yelcot Communications'},
 u'mid180-01': {u'name': u'yondoo'},
 u'cou060': {u'name': u'Zito Media'}}

class AdobePassIE(InfoExtractor):
    _SERVICE_PROVIDER_TEMPLATE = u'https://sp.auth.adobe.com/adobe-services/%s'
    _USER_AGENT = u'Mozilla/5.0 (X11; Linux i686; rv:47.0) Gecko/20100101 Firefox/47.0'
    _MVPD_CACHE = u'ap-mvpd'
    _DOWNLOADING_LOGIN_PAGE = u'Downloading Provider Login Page'

    def _download_webpage_handle(self, *args, **kwargs):
        headers = self.geo_verification_headers()
        headers.update(kwargs.get(u'headers', {}))
        kwargs[u'headers'] = headers
        return super(AdobePassIE, self)._download_webpage_handle(*args, **compat_kwargs(kwargs))

    @staticmethod
    def _get_mvpd_resource(provider_id, title, guid, rating):
        channel = etree.Element(u'channel')
        channel_title = etree.SubElement(channel, u'title')
        channel_title.text = provider_id
        item = etree.SubElement(channel, u'item')
        resource_title = etree.SubElement(item, u'title')
        resource_title.text = title
        resource_guid = etree.SubElement(item, u'guid')
        resource_guid.text = guid
        resource_rating = etree.SubElement(item, u'media:rating')
        resource_rating.attrib = {u'scheme': u'urn:v-chip'}
        resource_rating.text = rating
        return u'<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">' + etree.tostring(channel).decode() + u'</rss>'

    def _extract_mvpd_auth(self, url, video_id, requestor_id, resource):

        def xml_text(xml_str, tag):
            return self._search_regex(u'<%s>(.+?)</%s>' % (tag, tag), xml_str, tag)

        def is_expired(token, date_ele):
            token_expires = unified_timestamp(re.sub(u'[_ ]GMT', u'', xml_text(token, date_ele)))
            return token_expires and token_expires <= int(time.time())

        def post_form(form_page_res, note, data = {}):
            form_page, urlh = form_page_res
            post_url = self._html_search_regex(u'<form[^>]+action=(["\\\'])(?P<url>.+?)\\1', form_page, u'post url', group=u'url')
            if not re.match(u'https?://', post_url):
                post_url = compat_urlparse.urljoin(urlh.geturl(), post_url)
            form_data = self._hidden_inputs(form_page)
            form_data.update(data)
            return self._download_webpage_handle(post_url, video_id, note, data=urlencode_postdata(form_data), headers={u'Content-Type': u'application/x-www-form-urlencoded'})

        def raise_mvpd_required():
            raise ExtractorError(u'This video is only available for users of participating TV providers. Use --ap-mso to specify Adobe Pass Multiple-system operator Identifier and --ap-username and --ap-password or --netrc to provide account credentials.', expected=True)

        def extract_redirect_url(html, url = None, fatal = False):
            REDIRECT_REGEX = u'[0-9]{,2};\\s*(?:URL|url)=\\\'?([^\\\'"]+)'
            redirect_url = self._search_regex(u'(?i)<meta\\s+(?=(?:[a-z-]+="[^"]+"\\s+)*http-equiv="refresh")(?:[a-z-]+="[^"]+"\\s+)*?content="%s' % REDIRECT_REGEX, html, u'meta refresh redirect', default=NO_DEFAULT if fatal else None, fatal=fatal)
            if not redirect_url:
                return
            else:
                if url:
                    redirect_url = compat_urlparse.urljoin(url, unescapeHTML(redirect_url))
                return redirect_url

        mvpd_headers = {u'ap_42': u'anonymous',
         u'ap_11': u'Linux i686',
         u'ap_z': self._USER_AGENT,
         u'User-Agent': self._USER_AGENT}
        guid = xml_text(resource, u'guid') if u'<' in resource else resource
        count = 0
        while count < 2:
            requestor_info = self._downloader.cache.load(self._MVPD_CACHE, requestor_id) or {}
            authn_token = requestor_info.get(u'authn_token')
            if authn_token and is_expired(authn_token, u'simpleTokenExpires'):
                authn_token = None
            if not authn_token:
                mso_id = self._downloader.params.get(u'ap_mso')
                if not mso_id:
                    raise_mvpd_required()
                username, password = self._get_login_info(u'ap_username', u'ap_password', mso_id)
                if not username or not password:
                    raise_mvpd_required()
                mso_info = MSO_INFO[mso_id]
                provider_redirect_page_res = self._download_webpage_handle(self._SERVICE_PROVIDER_TEMPLATE % u'authenticate/saml', video_id, u'Downloading Provider Redirect Page', query={u'noflash': u'true',
                 u'mso_id': mso_id,
                 u'requestor_id': requestor_id,
                 u'no_iframe': u'false',
                 u'domain_name': u'adobe.com',
                 u'redirect_url': url})
                if mso_id == u'Comcast_SSO':
                    provider_redirect_page, urlh = provider_redirect_page_res
                    if u'automatically signing you in' in provider_redirect_page:
                        oauth_redirect_url = self._html_search_regex(u'window\\.location\\s*=\\s*[\\\'"]([^\\\'"]+)', provider_redirect_page, u'oauth redirect')
                        self._download_webpage(oauth_redirect_url, video_id, u'Confirming auto login')
                    else:
                        if u'<form name="signin"' in provider_redirect_page:
                            provider_login_page_res = provider_redirect_page_res
                        elif u'http-equiv="refresh"' in provider_redirect_page:
                            oauth_redirect_url = extract_redirect_url(provider_redirect_page, fatal=True)
                            provider_login_page_res = self._download_webpage_handle(oauth_redirect_url, video_id, self._DOWNLOADING_LOGIN_PAGE)
                        else:
                            provider_login_page_res = post_form(provider_redirect_page_res, self._DOWNLOADING_LOGIN_PAGE)
                        mvpd_confirm_page_res = post_form(provider_login_page_res, u'Logging in', {mso_info[u'username_field']: username,
                         mso_info[u'password_field']: password})
                        mvpd_confirm_page, urlh = mvpd_confirm_page_res
                        if u'<button class="submit" value="Resume">Resume</button>' in mvpd_confirm_page:
                            post_form(mvpd_confirm_page_res, u'Confirming Login')
                elif mso_id == u'Verizon':
                    provider_redirect_page, urlh = provider_redirect_page_res
                    if u'Please wait ...' in provider_redirect_page:
                        saml_redirect_url = self._html_search_regex(u'self\\.parent\\.location=(["\\\'])(?P<url>.+?)\\1', provider_redirect_page, u'SAML Redirect URL', group=u'url')
                        saml_login_page = self._download_webpage(saml_redirect_url, video_id, u'Downloading SAML Login Page')
                    else:
                        saml_login_page_res = post_form(provider_redirect_page_res, u'Logging in', {mso_info[u'username_field']: username,
                         mso_info[u'password_field']: password})
                        saml_login_page, urlh = saml_login_page_res
                        if u'Please try again.' in saml_login_page:
                            raise ExtractorError(u"We're sorry, but either the User ID or Password entered is not correct.")
                    saml_login_url = self._search_regex(u'xmlHttp\\.open\\("POST"\\s*,\\s*(["\\\'])(?P<url>.+?)\\1', saml_login_page, u'SAML Login URL', group=u'url')
                    saml_response_json = self._download_json(saml_login_url, video_id, u'Downloading SAML Response', headers={u'Content-Type': u'text/xml'})
                    self._download_webpage(saml_response_json[u'targetValue'], video_id, u'Confirming Login', data=urlencode_postdata({u'SAMLResponse': saml_response_json[u'SAMLResponse'],
                     u'RelayState': saml_response_json[u'RelayState']}), headers={u'Content-Type': u'application/x-www-form-urlencoded'})
                else:
                    provider_redirect_page, urlh = provider_redirect_page_res
                    provider_refresh_redirect_url = extract_redirect_url(provider_redirect_page, url=urlh.geturl())
                    if provider_refresh_redirect_url:
                        provider_redirect_page_res = self._download_webpage_handle(provider_refresh_redirect_url, video_id, u'Downloading Provider Redirect Page (meta refresh)')
                    provider_login_page_res = post_form(provider_redirect_page_res, self._DOWNLOADING_LOGIN_PAGE)
                    mvpd_confirm_page_res = post_form(provider_login_page_res, u'Logging in', {mso_info.get(u'username_field', u'username'): username,
                     mso_info.get(u'password_field', u'password'): password})
                    if mso_id != u'Rogers':
                        post_form(mvpd_confirm_page_res, u'Confirming Login')
                session = self._download_webpage(self._SERVICE_PROVIDER_TEMPLATE % u'session', video_id, u'Retrieving Session', data=urlencode_postdata({u'_method': u'GET',
                 u'requestor_id': requestor_id}), headers=mvpd_headers)
                if u'<pendingLogout' in session:
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                authn_token = unescapeHTML(xml_text(session, u'authnToken'))
                requestor_info[u'authn_token'] = authn_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)
            authz_token = requestor_info.get(guid)
            if authz_token and is_expired(authz_token, u'simpleTokenTTL'):
                authz_token = None
            if not authz_token:
                authorize = self._download_webpage(self._SERVICE_PROVIDER_TEMPLATE % u'authorize', video_id, u'Retrieving Authorization Token', data=urlencode_postdata({u'resource_id': resource,
                 u'requestor_id': requestor_id,
                 u'authentication_token': authn_token,
                 u'mso_id': xml_text(authn_token, u'simpleTokenMsoID'),
                 u'userMeta': u'1'}), headers=mvpd_headers)
                if u'<pendingLogout' in authorize:
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                if u'<error' in authorize:
                    raise ExtractorError(xml_text(authorize, u'details'), expected=True)
                authz_token = unescapeHTML(xml_text(authorize, u'authzToken'))
                requestor_info[guid] = authz_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)
            mvpd_headers.update({u'ap_19': xml_text(authn_token, u'simpleSamlNameID'),
             u'ap_23': xml_text(authn_token, u'simpleSamlSessionIndex')})
            short_authorize = self._download_webpage(self._SERVICE_PROVIDER_TEMPLATE % u'shortAuthorize', video_id, u'Retrieving Media Token', data=urlencode_postdata({u'authz_token': authz_token,
             u'requestor_id': requestor_id,
             u'session_guid': xml_text(authn_token, u'simpleTokenAuthenticationGuid'),
             u'hashed_guid': u'false'}), headers=mvpd_headers)
            if u'<pendingLogout' in short_authorize:
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                count += 1
                continue
            return short_authorize

        return