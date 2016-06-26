
from google.appengine.ext import db
from google.appengine.ext import webapp
import datetime, logging

import misc
from models import Team, OFLScheduleParser, OFL_Match, OFL_Prediction, Coach
from grappl.utils import batch_put

#class RetireCoaches(webapp.RequestHandler):
#  def get(self):
#    logging.debug("checking coach retirement....")
#
#    sixteen_weeks_ago = datetime.date.today() - datetime.timedelta(weeks=16)
#
#    for coach in Coach.all().filter("retired =", False):
#      if not coach.last_active:
#        continue
#      
#      if coach.last_active < sixteen_weeks_ago:
#        logging.debug("retiring %s" % coach.key().name())
#        misc.retire_coach(coach)

#class RetireTeams(webapp.RequestHandler):
#
#  def get(self):
#    logging.debug("checking team retirement....")
#
#    sixteen_weeks_ago = datetime.date.today() - datetime.timedelta(weeks=16)
#
#    for team in Team.all().filter("retired =", False):
#      if not team.last_active:
#        assert team.matches == 0
#        continue
#
#      if team.last_active < sixteen_weeks_ago:
#        logging.debug("retiring %s" % team.key().name())
#        misc.retire_team(team)

   
        

class OFLPickemRefresh(webapp.RequestHandler):
  def get(self):
    logging.debug("checking OFL match results...")
    # We have to parse OFL Schedule to get up to date results.
    season, week = misc.get_ofl_season_and_week()
    season += 3
    weekbegin = week - 1
    if weekbegin < 1:
      weekbegin = 1
    weekend = week + 1
    if weekend > 16:
      weekend = 16
    for week in range(weekbegin, weekend+1):
      parser = OFLScheduleParser()
      data = []
      data = parser.parse(season, week)
      parser.update_schedule_entries(data)
      #Now that entries are updated, let's look at predictions for all coaches
      put_list=[]
      predictions = OFL_Prediction.all().filter("season =", season).filter("week =", week)
      for prediction in predictions:
        keyname = prediction.key().name()
        match = OFL_Match.get_by_key_name(keyname)
        # match exists so compare - should not occur unless Thul changes team matchups
        if match:
          if match.gamePlayed:
            if prediction.Update(match.scoreA, match.scoreB):
              put_list.append(prediction)
              logging.debug("Updating prediction %s for %s" % (prediction.key().name(), prediction.parent().key().name())) 
      batch_put(put_list)