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


for coach in Coach.all():
  print coach.key().name() + "<br>"
  coach_stats = CoachStats.all().ancestor(coach).get()
  if not coach_stats:    #Coach doesn't have stats yet.
    coach_stats = CoachStats(parent=coach)
  coach_stats.reset()
  for team in Team.all().filter("coach = ", coach):
       print "   " + team.key().name() + i2s(team.tpts) + "<br>"
       CoachStats.addTeam(coach_stats, team)
  print i2s(coach_stats.tpts) + "<br>"
  if coach_stats.matches > 1:
    CoachStats.compute_awp(coach_stats)
  coach_stats.put()
