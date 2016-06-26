from google.appengine.api.labs import taskqueue
from google.appengine.api import users
from google.appengine.ext import db
############# 
# Standard Python imports. 
import os 
import sys 
import logging 

from models import *

def i2s(val): return str(int(val)) # do not use str() in case of unicode


for race in Race.all():
  print race.key().name() + "<br>"
  race_stats = RaceStats.all().filter("race =", race).get()
  if not race_stats:    #Race doesn't have stats yet.
    print race.key().name() + " not found, creating....<br>"
    race_stats = RaceStats(race = race)
#    race_stats.race = race
  race_stats.reset()
  for team in Team.all().filter("race = ", race):
       print "   " + team.key().name() + i2s(team.tpts) + "<br>"
       RaceStats.addTeam(race_stats, team)
  print i2s(race_stats.tpts) + "<br>"
  if race_stats.matches > 1:
    RaceStats.compute_awp(race_stats)
  race_stats.put()
