
# order matters!
from coach import *
from team import *
from player import *
from ofl_pickem import *
from leader import *
from match import *
from tournament import *
from race_stats import *


def init():
  CoachLeader.init()
  TeamLeader.init()
  PlayerLeader.init()
#  OFLPickemLeader.init()
  Skill.init()
  Race.init()
  Position.init()
  Injury.init()

