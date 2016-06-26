from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from HTMLParser import HTMLParser
from operator import attrgetter
from django.template import Library

import misc, views

from models import OFL_Match, OFL_Prediction, Coach
from misc.table import Table, Column

register = Library()

@register.filter
def get_range( value ):

  #  Filter - returns a list containing range made from given value
  #  Usage (in template):

  #  <ul>{% for i in 3|get_range %}
  #    <li>{{ i }}. Do something</li>
  #  {% endfor %}</ul>

  #  Results with the HTML:
  #  <ul>
  #    <li>0. Do something</li>
  #    <li>1. Do something</li>
  #    <li>2. Do something</li>
  #  </ul>

  #  Instead of 3 one may use the variable set in the views

  result = range(1,value+1)
  return result
  
@register.filter
def add_one(value):
  result = value + 1
  return result

class OFLScheduleParser(HTMLParser):
    def __init__(self):
      HTMLParser.__init__(self) 
      self.data = []

    def handle_starttag(self, tag, attrs):
      if (tag == 'img'):    
        for attr in attrs:
            #team logo
            if ("src" in attr):
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

def update_leaderboards(coach):
  ofl_pickem_stats = OFLPickemStats.ancestor(coach).get()
  if not ofl_pickem_stats:    #Coach doesn't have stats yet.
      ofl_pickem_stats = OFLPickemStats(parent=coach)
  ofl_pickem_stats.UpdateAll()
  ofl_pickem_stats.put()  
            
def update_schedule_entries(coach, season, week, data):
  def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))
  

  
  point_counter = 1
  match_data = []
  for chunk in chunker(data,11):
    if len(chunk) == 11:
      match_name = str(season) + ":" + str(week) + "|" + chunk[2] + " vs. " + chunk[8]
      match = OFL_Match.get_or_insert(match_name)      
      # match = OFL_Match(key_name = match_name)      
      match.season = season
      match.week = week
      match.teamAcolor = chunk[0]    
      match.teamAlogo = chunk[1]
      match.teamA = chunk[2]
      match.teamAcoach = chunk[3]
      match.teamArace = chunk[4]
      # Check to see if game has been played
      if not "vs.gif" in chunk[5]:
        #if chunk[5]:
        #if data[0].isdigit():
        scoreA, scoreB = chunk[5].split(" - ") 
        match.scoreA = int(scoreA)
        match.scoreB = int(scoreB) 
        match.gamePlayed = True
      # Check if prediction exists, if not, create and disqualify
      prediction = OFL_Prediction.get_by_key_name(match_name, parent=coach)
      if not prediction:
        prediction = OFL_Prediction(key_name = match_name, parent = coach)
        if match.gamePlayed:
          prediction.Disqualify()
        prediction.season = season
        prediction.week = week
        prediction.put()
      if match.gamePlayed:
        if prediction.Update(match.scoreA, match.scoreB):
          prediction.put()        
      match.teamBcolor = chunk[6]    
      match.teamBlogo = chunk[7]
      match.teamB = chunk[8]
      match.teamBcoach = chunk[9]
      match.teamBrace = chunk[10]
      match.put()
    

def sort_wagers(coach, season, week):
  predictions = OFL_Prediction.all().filter("season =", season).filter("week =", week).ancestor(coach).filter("disqualified =", False).order("wager")
  point_counter = 1
  for prediction in predictions:
    if prediction.wager == 0:
      prediction.wager = point_counter
      prediction.put()
    point_counter += 1
    #print prediction.key().name() + " " + str(prediction.wager) + " " + str(prediction.disqualified)
    

class OFL_PickemBox(views.CachedView):
  
  def get(self):

    user = users.get_current_user()
    if user:
      log_out_url = users.create_logout_url("/")
      coach = Coach.all().filter("user =", user).get()
      if coach:
        season, week = self.request.get("schedule").split("-")

        if not season or not week:
          season, week = misc.get_ofl_season_and_week()
          season += 3
        else:
          season = int(season)
          week = int(week)

        parser = OFLScheduleParser()
        ofl_info = urlfetch.fetch("http://www.shalkith.com/bloodbowl/processSchedule.php?s=%s&w=%s" % (season, week))
        parser.feed(ofl_info.content)
        update_schedule_entries(coach, season, week, parser.data)
        sort_wagers(coach, season, week)

        def logoA_getter(match):
          html = "<img src='http://www.shalkith.com/bloodbowl/%s'/>" % (match.teamAlogo)
          return html

        def logoB_getter(match):
          html = "<img src='http://www.shalkith.com/bloodbowl/%s'/>" % (match.teamBlogo)
          return html

        def nameA_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          html = "%s (%s)" % (match.teamA, match.teamAcoach)
          return html

        def nameB_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          html = "%s (%s)" % (match.teamB, match.teamBcoach)
          return html

        def key_name_getter(prediction):
          return prediction.key().name()

        def choice_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          html = "<img src='http://www.shalkith.com/bloodbowl/%s'/>" % (match.teamAlogo)
          if not match.gamePlayed:
            html += "<input type='radio' name='%schoice' value='-1' %s>" % (match.key().name(), prediction.isChecked(-1))
            html += "<input type='radio' name='%schoice' value='0' %s>" % (match.key().name(), prediction.isChecked(0))
            html += "<input type='radio' name='%schoice' value='1' %s>" % (match.key().name(), prediction.isChecked(1))
          else:
            html += "<input type='radio' name='%schoice' value='-1' disabled %s>" % (match.key().name(), prediction.isChecked(-1))
            html += "<input type='radio' name='%schoice' value='0' disabled %s>" % (match.key().name(), prediction.isChecked(0))
            html += "<input type='radio' name='%schoice' value='1' disabled %s>" % (match.key().name(), prediction.isChecked(1))
          html += "<img src='http://www.shalkith.com/bloodbowl/%s'/>" % (match.teamBlogo)
          return html
  

        # Bypassing table.html Django template to create this table
        # Table requires Jquery code for sortable entires and wagers
        # Hidden input tags are also used with form.
        prediction_list = OFL_Prediction.all().filter("season =", season).filter("week =", week).ancestor(coach).filter("gameScored =", False).order("-wager")
        columns = ["Wager", "Away Team", "Prediction", "Home Team"]
        table_html = []
        table_html.append('''
        <table class="ofl_pickem schedule_table">
        <thead>
            <tr>''')
        for column in columns:
          table_html.append('<th style="text-align: center;"> %s </th>' % column)
        table_html.append('''
            </tr>
        </thead>
        <tbody id="sortable">''')
        k = 0        
        for prediction in prediction_list:
          table_html.append('<tr class="row_%s">' % k)
          table_html.append('<input type="hidden" name="row_%s" value="%s">' % (k, prediction.key().name()))
          table_html.append("<input type='hidden' class='row_%s' name='%svalue' value='%s'>" % (k, prediction.key().name(), prediction.wager))
          table_html.append('<td class="row_%s" style="text -align: center;">%s</td>' % (k, prediction.wager))
          table_html.append('<td style="text-align: center;">%s</td>' % nameA_getter(prediction))
          table_html.append('<td style="text-align: center;">%s</td>' % choice_getter(prediction))
          table_html.append('<td style="text-align: center;">%s</td>' % nameB_getter(prediction))
          k += 1
        table_html.append('</tbody>\n</table>')
        table_html = "\n".join(table_html)
        
        played_table = Table(
          columns = [
            # profile
            Column("Points",     "Points Earned",      attrgetter("points")),
            Column("Wager",      "Wager Placed",       attrgetter("wager")),
            Column("Away Team",  "Away Team",          nameA_getter, center=True),
            Column("Prediction", "Your Prediction",    choice_getter, center=True),
            Column("Home Team",  "Home Team",          nameB_getter, center=True),
            ],
          query = OFL_Prediction.all().filter("season =", season).filter("week =", week).ancestor(coach).filter("gameScored =", True).order("-points"),
          id = "played_table",
          cls = "tablesorter",
          )
        
        
        
    else:
      log_in_url = users.create_login_url("/") 

    # render and update 
    #--------------------------------------------------------------------#

    ofl_pickem_page = misc.render('ofl_pickem_box.html', locals())
    self.update(ofl_pickem_page)

    self.response.out.write(ofl_pickem_page)