# order matters!
import models
from models.coach import *
from models.team import *
from models.player import *
from models.ofl_pickem import *
from models.leader import *
from models.match import *
from models.tournament import *
from models.race_stats import *


#Script to initiate all static classes for a fresh DB (used for newly created local servers).
CoachLeader.init()
TeamLeader.init()
PlayerLeader.init()
Skill.init()
Race.init()
Position.init()
Injury.init()

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