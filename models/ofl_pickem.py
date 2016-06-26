from google.appengine.ext import db
from google.appengine.api import urlfetch
from HTMLParser import HTMLParser
import datetime, logging
import properties
from models import Coach

class OFL_Week(db.Model):
  # keyname = s:w
  # Using this class as an ancestor for OFL_Match
  # Querying by ancestor ensures any previous puts have been completed before pulling results.
  season      = db.IntegerProperty()
  week        = db.IntegerProperty()
  
class OFL_Match(db.Model):
  # parent = OFL_Week
  # keyname = teamA vs. teamB
  season      = db.IntegerProperty()
  week        = db.IntegerProperty()
  teamA        = db.StringProperty()
  teamAlogo    = db.StringProperty()
  teamAcolor   = db.StringProperty(default="#000000")
  teamAcoach   = db.StringProperty()
  teamArace    = db.StringProperty()
  teamB        = db.StringProperty()
  teamBlogo    = db.StringProperty()
  teamBcolor   = db.StringProperty(default="#000000")
  teamBcoach   = db.StringProperty()
  teamBrace    = db.StringProperty()
  scoreA       = db.IntegerProperty()
  scoreB       = db.IntegerProperty()
  gamePlayed   = db.BooleanProperty(default=False)
  AVotes       = db.IntegerProperty(default = 0)
  BVotes       = db.IntegerProperty(default = 0)
  dVotes       = db.IntegerProperty(default = 0)
    
  @staticmethod
  def compute_totals(season, week):
    matches = OFL_Match.all().filter("season =", season).filter("week =", week)
    for match in matches:
      original_xml = match.to_xml()
      match.AVotes = 0
      match.dVotes = 0
      match.BVotes = 0
      predictions = OFL_Prediction.all().filter("match =", match)
      for prediction in predictions:
        if (prediction.selection == -1):
          match.AVotes += prediction.wager
        elif (prediction.selection == 0):
          match.dVotes += prediction.wager
        elif (prediction.selection == 1):
          match.BVotes += prediction.wager
      if original_xml != match.to_xml():
        logging.info("compute_totals: Inserting match %s" % match.key().name())
        match.put()
        
  def update_score(self, scoreA, scoreB):
    self.scoreA = int(scoreA)
    self.scoreB = int(scoreB) 
    self.gamePlayed = True
  
class OFLScheduleParser(HTMLParser):
    def __init__(self):
      HTMLParser.__init__(self) 
      self.data = []
      self.season = 0
      self.week = 0

    def handle_starttag(self, tag, attrs):
      if (tag == 'img'):    
        for attr in attrs:
            #team logo
            if ("src" in attr):
              if "/get_wager_pic" in attr[1].strip():
                return
              self.data.append(attr[1].strip())   
      if (tag == 'div'):
        for attr in attrs:
            if ("style" in attr):
               #team color
               self.data.append(attr[1].strip())
    def handle_data(self, data):
        filter = ["Download", "View Score" , "|", "Box Score", "Download", "View All Scores", "AWAY", "HOME", ""]
        data = data.strip().strip("()")
        if data.strip() not in filter:            
            #continue filtering
            if "Season" in data:
              return
            self.data.append(data)
  
    def parse(self, season, week):
      self.data=[]
      self.season = season
      self.week = week
      ofl_info = urlfetch.fetch("http://www.oldworldfootball.com/processSchedule.php?s=%s&w=%s" % (season, week))
      self.feed(ofl_info.content)
      return self.data

    def update_schedule_entries(self, data):
      def chunker(seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

      #Different format for Week 15.  Chunk[5] + Chunk[12] now add Division
      if (self.season >= 16):
        chunk_count = 13
        spacer = 1
      else:
        chunk_count = 11
        spacer = 0
      
      point_counter = 1
      for chunk in chunker(self.data,chunk_count):
        if len(chunk) == chunk_count:
          match_name = str(self.season) + ":" + str(self.week) + "|" + chunk[2] + " vs. " + chunk[8+spacer]
          match = OFL_Match.get_or_insert(match_name)
          logging.info("UPDATING SCHEDULE ENTRIES: Inserting match %s" % match.key().name())
          logging.info("CHUNKS: %s" % chunk)          
          original_xml = match.to_xml()      
          # match = OFL_Match(key_name = match_name)      
          match.season = self.season
          match.week = self.week
          match.teamAcolor = chunk[0]    
          match.teamAlogo = chunk[1]
          match.teamA = chunk[2]
          match.teamAcoach = chunk[3]
          match.teamArace = chunk[4]
        # Check to see if game has been played
          if not "vs.gif" in chunk[5+spacer]:
            scoreA, scoreB = chunk[5+spacer].split(" - ") 
            match.update_score(int(scoreA), int(scoreB))
        # Check if prediction exists, if not, create and disqualify        
          match.teamBcolor = chunk[6+spacer]    
          match.teamBlogo = chunk[7+spacer]
          match.teamB = chunk[8+spacer]
          match.teamBcoach = chunk[9+spacer]
          match.teamBrace = chunk[10+spacer]
          if original_xml != match.to_xml():
            logging.info("update_schedule_entries: Inserting match %s" % match.key().name())
            match.put()  
  
class OFL_Match_Tracker:
  @staticmethod
  def get_match_list(season, week, data=[]):
    if len(data) == 0:
      parser = OFLScheduleParser()
      data = parser.parse(season, week)
    
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))
    
    #Create ancestor record.
    ofl_week = OFL_Week.get_or_insert("%s:%s" % (season, week))
    ofl_week.put()
    
    match_list = []
    point_counter = 1
    for chunk in chunker(data,11):
      if len(chunk) == 11:
        match_name = str(season) + ":" + str(week) + "|" + chunk[2] + " vs. " + chunk[8]
        match = OFL_Match.get_or_insert(match_name, parent=ofl_week)
        original_xml = match.to_xml()            
        match.season = season
        match.week = week
        match.teamAcolor = chunk[0]    
        match.teamAlogo = chunk[1]
        match.teamA = chunk[2]
        match.teamAcoach = chunk[3]
        match.teamArace = chunk[4]
        # Check to see if game has been played
        if not "vs.gif" in chunk[5]:
          scoreA, scoreB = chunk[5].split(" - ") 
          match.update_score(int(scoreA), int(scoreB))
        # Check if prediction exists, if not, create and disqualify        
        match.teamBcolor = chunk[6]    
        match.teamBlogo = chunk[7]
        match.teamB = chunk[8]
        match.teamBcoach = chunk[9]
        match.teamBrace = chunk[10]
        if original_xml != match.to_xml():
          logging.info("update_schedule_entries: Inserting match %s" % match.key().name())
          match_list.append(match)    
    return match_list
    
class OFL_Prediction_Tracker:
  @staticmethod
  def create_predictions(ofl_match_list, coach):
    #Creates prediction entries for specified coach assigning point values from 1 to num_of_matches to each prediction.
    prediction_list = []
    for match in ofl_match_list:
      prediction = OFL_Prediction(parent = match.parent(), match = match, coach = coach)
      if match.gamePlayed:
        prediction.Disqualify()
      prediction_list.append(prediction)
    return prediction_list
    
  def update_predictions(match):
    #Takes a match result and updates all predictions for that match.
    
    
    return prediction_list
      
  def query_prediction_list(coach, season, week):
    prediction_list = []
    
    prediction_list = OFL_Prediction.all().filter("season =", season).filter("week =", week).filter("coach =", coach)
    
    return prediction_list
  
  
  
class OFL_Prediction(db.Model):    
  # parent = coach
  # parent = s:w  <--- new format
  # key_name = s:w|teamA vs. teamB
  coach        = db.ReferenceProperty(Coach)  
  match        = db.ReferenceProperty(OFL_Match)
  selection    = db.IntegerProperty(default=0)       # -1 for Away, 0 for Draw (default), 1 for Home
  wager        = db.IntegerProperty(default=0)       # point total assigned
  points       = db.IntegerProperty(default=0)       # actual points awarded
  disqualified = db.BooleanProperty(default=False)
  gameScored   = db.BooleanProperty(default=False)
  season       = db.IntegerProperty(default=0)
  week         = db.IntegerProperty(default=0)
  
  def scoreMatch(self, scoreAway, scoreHome):
    
    if self.wager > 0:
      result = scoreHome - scoreAway
      if result != 0:
        result = result / abs(result)  
      # result now equals -1, 0, or 1
      
      if self.selection == result:
        self.points = self.wager
      else:
        self.points = 0
      
  
  def isChecked(self, choice):
    if self.selection == int(choice):
      return "checked"
    else:
      return ""

  def Update(self, scoreA, scoreB):
    updatePrediction = False
    if not self.disqualified:
      result = scoreB - scoreA
      if result != 0:
        result = result / abs(result)
      # result now equals -1, 0, or 1

      #First check if coach has instance of OFLPickemStats
      coach = self.parent()
      stats = OFLPickemStats.get_by_key_name(coach.key().name())
      if not stats:
        stats = OFLPickemStats(key_name = coach.key().name())
        stats.recompute()
        #logging.info("Update: Inserting OFL_PickemStats %s for %s" % (stats.match.key().name() , stats.parent().key().name()))
        logging.info("inserting OFL_PickemStats")
        stats.put()

      # Now check to see if the game was already scored (this is intended for match results that get changed / admin'ed by commisioner)        
      if self.gameScored:
        if result != self.selection and self.points > 0:
          #originally predicted corret, but now wrong.
          stats.subtract(self.season, self.week, self.points)
          self.points = 0
          #logging.info("changing admin'd result: Inserting OFL_PickemStats %s for %s" % (stats.match.key().name() , stats.parent().key().name()))
          logging.info("updating OFL_PickemStats")
          stats.put()
          updatePrediction = True
        
        
        if result == self.selection and self.points == 0:
          #originally predicted wrong, but now is correct.
          self.points = self.wager
          stats.update(self.season, self.week, self.points)
          #logging.info("changing admin'd result: Inserting OFL_PickemStats %s for %s" % (stats.match.key().name() , stats.parent().key().name()))
          logging.info("updating OFL_PickemStats")
          stats.put()
          updatePrediction = True
      
      else:
        if result == self.selection:
          self.points = self.wager
          stats.update(self.season, self.week, self.points)
          #logging.info("Update: Inserting OFL_Prediction %s for %s" % (stats , stats.parent().key().name()))
          logging.info("Update: updating stats")
          stats.put()
        else:
          self.points = 0
        self.gameScored=True
        updatePrediction=True
                
    return updatePrediction
        
  def Disqualify(self):
    self.disqualified = True
    self.gameScored = True
      
class OFLPickemStats(db.Model):
  #key_name         = coach.key().name()
  all_time          = db.IntegerProperty(default=0)
  matches           = db.IntegerProperty(default=0)      

  def get_coach_name(self):
    return self.key().name() 
  
  def subtract(self, season, week, points):
    record = OFLPickemSeasonRecord.all().ancestor(self).filter("season =", season).get()
    if not record:
      record = OFLPickemSeasonRecord(season = season, parent = self)
      record.put()
    record.subtract(week, points)
    self.all_time -= points
    self.matches -= 1
    record.put()

  def update(self, season, week, points):
    record = OFLPickemSeasonRecord.all().ancestor(self).filter("season =", season).get()
    if not record:
      record = OFLPickemSeasonRecord(season = season, parent = self)
      record.put()
    record.update(week, points)
    self.all_time += points
    self.matches += 1
    record.put()

  def reset(self):
    self.all_time = 0
    records = OFLPickemSeasonRecord.all().ancestor(self)
    for record in records:
      record.reset()
      record.put()

  def recompute(self):
    self.reset()    
    coach = Coach.get_by_key_name(self.key().name())
    predictions = OFL_Prediction.all().ancestor(coach).filter("points >", 0)
    for prediction in predictions:
      self.update(prediction.season, prediction.week, prediction.points)
        
class OFLPickemSeasonRecord(db.Model):
  #parent            = OFLPickemStats
  season             = db.IntegerProperty(default=0)
  points             = db.IntegerProperty(default=0)
  matches            = db.IntegerProperty(default=0)  

  def get_coach_name(self):
    return self.parent().key().name()
  
  def update(self, week, points): 
    record = OFLPickemWeekRecord.all().ancestor(self).filter("week =", week).get()
    if not record:
      record = OFLPickemWeekRecord(season = self.season, week = week, parent = self)
      logging.info("update: Inserting OFLPickemSeasonRecord %s" % record.parent().parent().key().name())
      record.put()
    record.points += points
    record.matches += 1
    self.points += points
    self.matches += 1
    logging.info("update: Inserting OFLPickemSeasonRecord %s" % record.parent().key().name())
    record.put()
    
  def subtract(self, week, points):  
    record = OFLPickemWeekRecord.all().ancestor(self).filter("week =", week).get()
    if not record:
      record = OFLPickemWeekRecord(season = self.season, week = week, parent = self)
      logging.info("subtract: Inserting OFLPickemSeasonRecord %s" % record.parent().key().name())
      record.put()
    record.points -= points
    record.matches -= 1
    self.points -= points
    self.matches -= 1
    logging.info("subtract: Inserting OFLPickemSeasonRecord %s" % record.parent().key().name())
    record.put()  
  
  def reset(self):
    self.points = 0
    self.matches = 0
    records = OFLPickemWeekRecord.all().ancestor(self)
    for record in records:
      record.points = 0
      record.matches = 0
      logging.info("reset: Inserting OFLPickemSeasonRecord %s" % record.parent().key().name())
      record.put()

class OFLPickemWeekRecord(db.Model):
  #parent            = OFLPickemSeasonRecord
  season             = db.IntegerProperty(default=0)
  week               = db.IntegerProperty(default=1)
  points             = db.IntegerProperty(default=0)
  matches            = db.IntegerProperty(default=0)
    
  def get_coach_name(self):
    return self.parent().parent().key().name()  
    
class OFLCookie(db.Model):
  #key_name          = coach
  season             = db.IntegerProperty(default=0)
  week               = db.IntegerProperty(default=0)