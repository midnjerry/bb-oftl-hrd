
from google.appengine.ext import webapp
from google.appengine.api import mail

from grappl.submit import prepare_submit, process_submit, process_update
import models, views
from models import Player, Team
from grappl import submit

class Submit(webapp.RequestHandler):

  def post(self):

    data = {}
    for arg in self.request.arguments():
      data[arg] = self.request.get(arg)

    try:
      prepare_submit(data, self)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl-hrd.appspotmail.com",
          to="balderasfam@gmail.com",
          subject="bb-oftl-hrd: preparation error!",
          body="Failed with exception: %s" % e)
      raise


class SubmitTask(webapp.RequestHandler):

  def post(self):

    submit_data_key_string = self.request.get("submit_data_key_string")
    submit_data = models.SubmitData.get(submit_data_key_string)
    localtest   = bool(self.request.get("localtest"))

    match_lookup = submit_data.parent().parent()

    try:
      process_submit(submit_data, localtest)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl-hrd.appspotmail.com",
          to="balderasfam@gmail.com",
          subject="bb-oftl-hrd: submit error for %s!" % match_lookup.get_string(),
          body="Failed with exception: %s" % e)

      # In this case we reraise to allow the task to recover itself.
      # This is OK because the task is idempotent!
      raise


class UpdateTask(webapp.RequestHandler):

  def post(self):

    match_key_string = self.request.get("match_key_string")
    match = models.Match.get(match_key_string)
    match_lookup = match.parent()

    try:
      process_update(match)
    except Exception, e:
      mail.send_mail(
          sender="grappl@bb-oftl-hrd.appspotmail.com",
          to="balderasfam@gmail.com",
          subject="bb-oftl-hrd: update error for %s!" % match_lookup.get_string(),
          body="Failed with exception: %s" % e)

      # In this case we reraise to allow the task to recover itself.
      # This is OK because the task is idempotent!
      raise


class GetBBLog(webapp.RequestHandler):
  def get(self):
    n = self.request.get("n")
    try:
      bblog = (models.SubmitData.all()
          .order('-uploaded')
          .fetch(1, offset=int(n))[0].bblog)
    except:
      bblog = "N/A"
    self.response.out.write(bblog)
    
class UnRetireTeam(webapp.RequestHandler):
  #Purple Hate Machine
  #Beasts of R'yleh
  def get(self):
    team_key = db.Key.from_path("Team", self.request.get("team_key_name"))
    team = Team.get(team_key)
    if not team:
      self.response.out.write("%s is not a valid team<BR>" % team_key)
      return
    self.response.out.write("%s<BR>" % team.key().name())
    players = team.player_set
    try:
        submit.update_player_leaders(players)
    except:
        for player in players:
            self.response.out.write("Error!: %s<BR>" % team.key().name())
            self.response.out.write("...%s:%s<BR>" % (player.name, player.key().name()))
    submit.update_team_leaders(team)
    self.response.out.write("Unretiring Team: %s<BR>" % team.key().name())
    team.retired = False
    team.put()    
    views.TeamLeaders.clear()
    views.PlayerLeaders.clear()
    
class UpdatePlayerStandings(webapp.RequestHandler):
  def get(self):
    
    teams = Team.all().filter('retired ==', True).fetch(25)
#    players = Player.all().filter().fetch(100)
    for team in teams:
        self.response.out.write("%s<BR>" % team.key().name())
        players = team.player_set
        for player in players:
            self.response.out.write("...%s<BR>" % player.name)
        try:
            submit.update_player_leaders(players)
        except:
            for player in players:
                self.response.out.write("...%s:%s<BR>" % (player.name, player.key().name()))
            self.response.out.write("%s" % team.key().name())
        
    submit.update_team_leaders(teams)
    self.response.out.write(teams)
    for team in teams:
        team.retired = False
        team.put()
    views.TeamLeaders.clear()
    views.PlayerLeaders.clear()


