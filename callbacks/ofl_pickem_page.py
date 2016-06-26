from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
import datetime



from models import *
import views, misc
import logging
from grappl.utils import batch_put

# Handlers for various callbacks
# ------------------------------

class SavePredictions(webapp.RequestHandler):
  def post(self):
    count = self.request.get("count")
    assert count
    user = users.get_current_user()
    coach = Coach.all().filter("user =", user).get()    
    count = int(count)
    logging.info("Count = %s", count)
    for i in range(0, count):
      keyname = self.request.get("row_%s" % i)
      season, week = keyname.split("|")[0].split(":")
      wager = self.request.get(keyname+"value")
      selection = self.request.get(keyname+"choice")
      prediction = OFL_Prediction.get_or_insert(key_name = keyname, parent = coach)
      original_xml = prediction.to_xml()      
      match = OFL_Match.get_by_key_name(keyname)
      prediction.match = match
      prediction.wager = int(wager)
      prediction.selection = int(selection)
      prediction.season = int(season)
      prediction.week = int(week)
      if prediction.to_xml() != original_xml:
        logging.info("Modifying prediction: "+keyname + " wager: " + wager + " selection: " + selection)
        prediction.put()
    logging.info("Running OFL_Match totals for %s-%s" % (prediction.season, prediction.week))
    OFL_Match.compute_totals(prediction.season, prediction.week)

      
class GetSchedule(webapp.RequestHandler):
  def post(self):  
    coach_name = self.request.get("coach_name")
    week = self.request.get("week")
    season = self.request.get("season")
    cookie = OFLCookie.get_by_key_name(coach_name)
    if not cookie:
      cookie = OFLCookie(key_name = coach_name)
    if week:
      cookie.week = int(week)
    else:
      cookie.week = 1
    if season:
      cookie.season = int(season)
    else:
      cookie.season = 10
    cookie.put()

class GetWagerPic(webapp.RequestHandler):
  def get(self):
    keyname = self.request.get("keyname")
    team = self.request.get("team")
    
    match = OFL_Match.get_by_key_name(keyname)
    if match and (team == "A" or team == "B"):      
      if team == "A":
        if match.AVotes > 0:
          score = 20 * match.AVotes / (match.dVotes + match.BVotes + match.AVotes)
        else: 
          score = 0
      elif team == "B":
        if match.BVotes > 0:
          score = 20 * match.BVotes / (match.dVotes + match.BVotes + match.AVotes)
        else:
          score = 0
      # here you could add A or B to the filename
      filename = "./dynamic/images/coins%02dB.png" % (score)
      data = open(filename, 'rb').read()
      print "Content-type: image/png\n"
      print data
    else:
      filename = "./dynamic/images/coins00B.png"
      data = open(filename, 'rb').read()
      print "Content-type: image/png\n"
      print data
      
class NotifyMatch(webapp.RequestHandler):
  def get(self):
  
    #Print graphic
    filename = "./dynamic/images/pixel.gif"
    data = open(filename, 'rb').read()
    print "Content-type: image/gif\n"
    print data
    
    # Format:
    # <img src=\"http://bb-oftl.appspot.com/submit_match_result.gif?keyname=s:w|teamA vs. teamB&score=#|# width=\"1\" height=\"1\">
    
    
    # keyname = s:w|teamA vs. teamB|scoreA:scoreB
    # score = teamAscore:teamBscore
    keyname = self.request.get("keyname")
    score = self.request.get("score")
    
    if not keyname:
      return
    ofl_match = OFL_Match.get_by_key_name(keyname)
    if ofl_match:
      season, week = keyname.split("|")[0].split(":")
      scoreA, scoreB = score.split("|")    
      logging.error("Match %s has been submitted." % keyname)

      #Update the OFL_Match
      ofl_match.update_score(int(scoreA), int(scoreB))
      ofl_match.put()
  
      #Now update all predictions for coaches.
      put_list = []
    
      # update leader standings for each team
      for prediction in OFL_Prediction.all().filter("season =", season).filter("week =", week):
        prediction.Update(ofl_match.scoreA, ofl_match.scoreB)
        logging.debug("Updating prediction %s for %s" % (prediction.key().name(), prediction.parent().key().name()))
        put_list.append(prediction)
      batch_put(put_list)
    

    
      
  