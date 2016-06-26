
from google.appengine.ext import db
from google.appengine.api import urlfetch
import math, logging, urllib

from models import Race

class RaceStats(db.Model):
  race             = db.ReferenceProperty(Race)
  num_of_teams     = db.IntegerProperty(default=0)
  tds_for          = db.IntegerProperty(default=0)
  tds_against      = db.IntegerProperty(default=0)
  passes_for       = db.IntegerProperty(default=0)
  passes_against   = db.IntegerProperty(default=0)
  pyards_for       = db.IntegerProperty(default=0)
  pyards_against   = db.IntegerProperty(default=0)
  rec_for          = db.IntegerProperty(default=0)
  rec_against      = db.IntegerProperty(default=0)
  ryards_for       = db.IntegerProperty(default=0)
  ryards_against   = db.IntegerProperty(default=0)
  int_for          = db.IntegerProperty(default=0)
  int_against      = db.IntegerProperty(default=0)
  kills_for        = db.IntegerProperty(default=0)
  kills_against    = db.IntegerProperty(default=0)
  cas_for          = db.IntegerProperty(default=0)
  cas_against      = db.IntegerProperty(default=0)
  ko_for           = db.IntegerProperty(default=0)
  ko_against       = db.IntegerProperty(default=0)
  stun_for         = db.IntegerProperty(default=0)
  stun_against     = db.IntegerProperty(default=0)
  tckl_for         = db.IntegerProperty(default=0)
  tckl_against     = db.IntegerProperty(default=0)
 
  matches          = db.IntegerProperty(default=0)
  wins             = db.IntegerProperty(default=0)
  draws            = db.IntegerProperty(default=0)
  losses           = db.IntegerProperty(default=0)

  # tournament points
  tpts       = db.IntegerProperty(default=0)

  # adjusted win percentage
  awp        = db.FloatProperty(default=0.0)

  def addTeam(self, team):
    for property in RaceStats.properties():
      if property.startswith("race"):
        continue
      if property.startswith("num_of_teams"):
        self.num_of_teams += 1
        continue
      setattr(self, property, getattr(self, property) + getattr(team, property))
    self.compute_awp()


  def accumulate(self, team_stats):
    for property in RaceStats.properties():
      if "for" in property or "against" in property:
        setattr(self, property, getattr(self, property) + getattr(team_stats, property))

  def reset(self):
    for property in RaceStats.properties():
      if property.startswith("awp"):
        continue
      if property.startswith("race"):
        continue
      setattr(self, property, 0)

  def compute_awp(self):
    self.awp = 0.0
    if (self.matches > 1):
      self.awp = max(0.0,
        (self.wins + self.draws/2.0) / self.matches - 
        1 / math.sqrt(self.matches))
		
  def update(self, team_record):
    self.accumulate(team_record)

    def inc_wins():   self.wins   += 1
    def inc_draws():  self.draws  += 1
    def inc_losses(): self.losses += 1

    self.matches += 1
    attr_map = {
        1:  'wins',
        0:  'draws',
        -1: 'losses',
        }
    attr = attr_map[team_record.result]
    setattr(self, attr, getattr(self, attr) + 1)

    self.compute_awp()

