############# 
# Standard Python imports. 
import os 
import sys 
import logging 
#import gaepdb 
# Remove the standard version of Django 
#for k in [k for k in sys.modules if k.startswith('django')]: 
#    del sys.modules[k] 
############# 
os.environ['DJANGO_SETTINGS_MODULE']='settings'
#from google.appengine.dist import use_library
#use_library('django', '1.2')
from google.appengine.ext import webapp
#from django import template
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import grappl.handlers, views, cron, misc
import callbacks.tournaments
import callbacks.coachs_page
import callbacks.ofl_pickem_page


application = webapp.WSGIApplication([
  # main tabs
  ('/recent_matches',      views.RecentMatches),
  ('/league_standings',    views.LeagueStandings),
  ('/general_statistics',  views.GeneralStatistics),
  ('/coach_leaders',       views.CoachLeaders),  
  ('/team_leaders',        views.TeamLeaders),
  ('/player_leaders',      views.PlayerLeaders),
  ('/tournaments',         views.Tournaments),
  ('/coachs_page',         views.CoachsPage),
  ('/ofl_pickem_page',     views.OFL_Pickem),

  # overlay boxes
  ('/team',                views.TeamBox),
  ('/coach',               views.CoachBox),
  ('/player',              views.PlayerBox),
  ('/match',               views.MatchBox),
  ('/tournament',          views.TournamentBox),
  ('/schedule',            views.OFL_PickemBox),

  
  # tournament callbacks
  ('/get_trophy',          callbacks.tournaments.GetTrophy),
  ('/create_tournament',   callbacks.tournaments.Create),
  ('/enroll_team',         callbacks.tournaments.Enroll),
  ('/withdraw_team',       callbacks.tournaments.Withdraw),
  ('/force_withdraw',      callbacks.tournaments.ForceWithdraw),
  ('/start_tournament',    callbacks.tournaments.Start),
  ('/get_seeds',           callbacks.tournaments.GetSeeds),
  ('/seed_tournament',     callbacks.tournaments.SeedAndStart),
  ('/cancel_tournament',   callbacks.tournaments.Cancel),
  ('/forfeit_team',        callbacks.tournaments.Forfeit),

  # coach's page callbacks
  ('/register',            callbacks.coachs_page.Register),
  ('/claim_team',          callbacks.coachs_page.ClaimTeam),
  ('/get_bio',             callbacks.coachs_page.GetBio),
  ('/get_pic',             callbacks.coachs_page.GetPic),
  ('/get_logo',            callbacks.coachs_page.GetLogo),
  ('/change_bio',          callbacks.coachs_page.ChangeBio),
  ('/change_pic',          callbacks.coachs_page.ChangePic),
  ('/change_logo',         callbacks.coachs_page.ChangeLogo),
  ('/preregister_team',    callbacks.coachs_page.PreRegister),
  ('/retire_team',         callbacks.coachs_page.Retire),
  ('/clear_team_for_OFL',  callbacks.coachs_page.ClearForOFL),

  # ofl_pickem callbacks
  ('/save_predictions',    callbacks.ofl_pickem_page.SavePredictions),
  ('/get_schedule',        callbacks.ofl_pickem_page.GetSchedule),
  ('/get_wager_pic',       callbacks.ofl_pickem_page.GetWagerPic),
  ('/submit_match_result.gif', callbacks.ofl_pickem_page.NotifyMatch),
  
  # GRAPPL handlers
  ('/grappl/submit',       grappl.handlers.Submit),
  ('/grappl/tasks/submit', grappl.handlers.SubmitTask),
  ('/grappl/tasks/update', grappl.handlers.UpdateTask),
  ('/grappl/bblog',        grappl.handlers.GetBBLog),

  ('/update/UpdatePlayerStandings', grappl.handlers.UpdatePlayerStandings),
  #('/update/UpdatePlayerStandings2', misc.UpdatePlayerStandings2),
  
  # cron jobs
  #('/cron/retire_teams',   cron.RetireTeams),
  #('/cron/retire_coaches', cron.RetireCoaches),
  ('/cron/update_oflpickem',cron.OFLPickemRefresh),
  ], debug=True)


def main():
  webapp.template.register_template_library('templatetags.ttags')
  run_wsgi_app(application)


if __name__ == "__main__":
  main()


