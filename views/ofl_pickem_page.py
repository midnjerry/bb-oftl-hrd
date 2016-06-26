from google.appengine.api import users
from google.appengine.ext import webapp
from operator import attrgetter


import misc, views

from models import OFL_Match, Coach, OFLPickemStats, OFLPickemSeasonRecord, OFLPickemWeekRecord, OFL_Prediction, OFLCookie, OFLScheduleParser
from misc.table import Table, Column

def update_predictions(coach,season,week):
  matches = OFL_Match.all().filter("season =", season).filter("week =", week)
  for match in matches:        
    prediction = OFL_Prediction.get_by_key_name(match.key().name(), parent=coach)
    if not prediction:
      prediction = OFL_Prediction(key_name = match.key().name(), parent = coach, match = match)
      if match.gamePlayed:
        prediction.Disqualify()
      prediction.season = season
      prediction.week = week
      prediction.put()
    if match.gamePlayed:
      if prediction.Update(match.scoreA, match.scoreB):
        prediction.put()
        

def sort_wagers(coach, season, week):
  predictions = OFL_Prediction.all().filter("season =", season).filter("week =", week).ancestor(coach).filter("gameScored =", False).order("wager")
  point_counter = 1
  for prediction in predictions:
    if prediction.wager == 0:
      prediction.wager = point_counter
      prediction.put()
    point_counter += 1
    #print prediction.key().name() + " " + str(prediction.wager) + " " + str(prediction.disqualified)
    

class OFL_Pickem(views.CachedView):
  
  def get(self):

    
    user = users.get_current_user()
    if user:
      log_out_url = users.create_logout_url("/")
      coach = Coach.all().filter("user =", user).get()
      if coach:        
        # Get current season / week
        cookie = OFLCookie.get_by_key_name(coach.key().name())
        if not cookie:
          cookie = OFLCookie(key_name = coach.key().name())
          season, week = misc.get_ofl_season_and_week()
          season += 3
          cookie.season = season
          cookie.week = week
          cookie.put()
        season = cookie.season
        week = cookie.week

        parser = OFLScheduleParser()
        data = parser.parse(season, week)
        parser.update_schedule_entries(data)
        update_predictions(coach, season, week)
        sort_wagers(coach, season, week)

        def logoA_getter(match):
          html = "<img src='http://www.oldworldfootball.com/%s'/>" % (match.teamAlogo)
          return html

        def logoB_getter(match):
          html = "<img src='http://www.oldworldfootball.com/%s'/>" % (match.teamBlogo)
          return html

        def nameA_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          html = "%s (%s - %s)" % (match.teamA, match.teamAcoach, match.teamArace)
          return html

        def nameB_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          html = "%s (%s - %s)" % (match.teamB, match.teamBcoach, match.teamBrace)
          return html

        def key_name_getter(prediction):
          return prediction.key().name()

        def choice_getter(prediction):
          match = OFL_Match.get_by_key_name(prediction.key().name())
          #html = "<img src='./get_wager_pic?keyname=%s&team=A'/>" % (prediction.key().name())
          html = "<img src='http://www.oldworldfootball.com/%s'/>" % (match.teamAlogo)
          if not match.gamePlayed:
            html += "<input type='radio' name='%schoice' value='-1' %s>" % (match.key().name(), prediction.isChecked(-1))
            html += "<input type='radio' name='%schoice' value='0' %s>" % (match.key().name(), prediction.isChecked(0))
            html += "<input type='radio' name='%schoice' value='1' %s>" % (match.key().name(), prediction.isChecked(1))
          else:
            html += "<input type='radio' name='%schoice' value='-1' disabled %s>" % (match.key().name(), prediction.isChecked(-1))
            html += "<input type='radio' name='%schoice' value='0' disabled %s>" % (match.key().name(), prediction.isChecked(0))
            html += "<input type='radio' name='%schoice' value='1' disabled %s>" % (match.key().name(), prediction.isChecked(1))
          html += "<img src='http://www.oldworldfootball.com/%s'/>" % (match.teamBlogo)
          #html += "<img src='./get_wager_pic?keyname=%s&team=B'/>" % (prediction.key().name())
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
          
      def logo_getter(standing):
        coach = Coach.get_by_key_name(standing.get_coach_name())
        img = "<img src='%s' />" % coach.get_logo_url() # FIXME: thumb is broken
        return "<div style='background-color: %(color)s'>%(img)s</div>" % {
          'color': coach.color, 'img': img}

      def name_getter(standing):
        coach = Coach.get_by_key_name(standing.get_coach_name())
        return "<a class='leader_link' rel='leader_coach' href='%s'>%s</a>" % (
          coach.get_box_href(),coach.key().name())
      
      leader_table = {}
      query = OFLPickemStats.all().order('-all_time').fetch(10)
      label = "alltime"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Score",     "Score",       attrgetter("all_time")),
            ],
          query = query,
          cls = "leader_table",
          )
          
      query = OFLPickemSeasonRecord.all().filter("season =", season).order("-points").fetch(10)
      label = "season"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Score",     "Score",       attrgetter("points")),
            ],
          query = query,
          cls = "leader_table",
          )
          
      query = OFLPickemWeekRecord.all().filter("week =", week).filter("season =", season).order("-points").fetch(10)
      label = "week"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Score",     "Score",       attrgetter("points")),
            ],
          query = query,
          cls = "leader_table",
          )
          
      query = OFLPickemStats.all().order('-matches').fetch(10)
      label = "alltime_matches"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Matches",     "Matches Predicted",       attrgetter("matches")),
            ],
          query = query,
          cls = "leader_table",
          )
          
      query = OFLPickemSeasonRecord.all().filter("season =", season).order("-matches").fetch(10)
      label = "season_matches"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Matches",     "Matches Predicted",       attrgetter("matches")),
            ],
          query = query,
          cls = "leader_table",
          )
          
      query = OFLPickemWeekRecord.all().filter("week =", week).filter("season =", season).order("-matches").fetch(10)
      label = "week_matches"
      leader_table[label] = Table(
          columns = [
            Column(" ",         "Logo",        logo_getter, center=True),
            Column("Coach Name", "Coach name", name_getter),
            Column("Matches",     "Matches Predicted",       attrgetter("matches")),
            ],
          query = query,
          cls = "leader_table",
          )    
          
    else:
      log_in_url = users.create_login_url("/") 

    # render and update 
    #--------------------------------------------------------------------#

    ofl_pickem_page = misc.render('ofl_pickem_page.html', locals())
    self.update(ofl_pickem_page)

    self.response.out.write(ofl_pickem_page)
      
    