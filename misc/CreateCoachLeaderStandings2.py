from google.appengine.api.labs import taskqueue
from google.appengine.api import users
from google.appengine.ext import db
############# 
# Standard Python imports. 
import os 
import sys 
import logging 
from models import *
import views

def i2s(val): return str(int(val)) # do not use str() in case of unicode
 
CoachLeader.init() 
 
for leader in CoachLeader.all().filter('display_order >=', 4):
   print leader.key().name()
   for stats in CoachStats.all():
     print stats.parent().key().name()
     CoachLeaderStanding(
        key_name = stats.parent().key().name(),
        parent   = leader,
        coach_stats  = stats,
        score    = leader.get_score(stats)).put()
     print "-" + i2s(leader.get_score(stats)) + "<BR>"
	 
views.CoachLeaders.clear()