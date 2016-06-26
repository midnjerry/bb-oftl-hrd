
from google.appengine.ext import webapp
from operator import attrgetter
import math, datetime

import models
import misc, views
from misc.table import Table, Column


class GeneralStatistics(views.CachedView):

  def get(self):

    # check for a cached version
    #--------------------------------------------------------------------#

    if self.emit(self.response.out):
      return

    # not cached or evicted from cache; regenerate
    #--------------------------------------------------------------------#

    def name_getter(racestats):
      return racestats.race.key().name()

    def race_getter(racestats):
      return "<img title='%s' src='%s' />" % (
          racestats.race.key().name(), racestats.race.get_image_src(thumb=True))

    def awp_getter(racestats):
      return "%0.3f" % racestats.awp

    def percent_getter(attr):
      def ave_getter(racestats):
        if (racestats.matches > 0):
          return "%.1f" % (float(getattr(racestats, attr)) * 100 / racestats.matches)
        return 0
      return ave_getter

    def get_ave_getter(attr):
      def ave_getter(racestats):
        if (racestats.matches > 0):
          return "%.1f" % (float(getattr(racestats, attr)) / racestats.matches)
        return 0
      return ave_getter

    tables = {}
    label = "active"
    tables[label] = Table(
          columns = [
            # profile
            Column(" ",         "Logo",                      race_getter, center=True),
            Column("Race",      "Race",                      name_getter, divider=True),
            Column("#Teams",    "Number of Teams",             attrgetter("num_of_teams")),
            Column("Matches",        "Matches played",           attrgetter("matches")),
            Column("Wins",         "Wins",                      attrgetter("wins")),
            Column("Draws",         "Draws",                     attrgetter("draws")),
            Column("Losses",         "Losses",                    attrgetter("losses")),
            Column("AWP",       "Adjusted Win Percentage",   awp_getter),
            Column("Win%",         "Win Percentage",           percent_getter("wins")),
            Column("Draw%",         "Draw Percentage",          percent_getter("draws")),
            Column("Loss%",         "Loss Percentage",          percent_getter("losses")),
            Column("TPts",      "Tournament Points",         attrgetter("tpts"), divider=True),

            ],
          query = models.RaceStats.all().order("-awp"),
          id = "race-standings-table",
          cls = "tablesorter",
          )

    label = "average"
    tables[label] = Table(
          columns = [
            # profile
            Column(" ",         "Logo",                      race_getter, center=True),
            Column("Race",      "Race",                      name_getter, divider=True),
            Column("#Tm",    "Number of Teams",             attrgetter("num_of_teams")),
            Column("AWP",       "Adjusted Win Percentage",   awp_getter, divider=True),
            Column("TD+", "Average Touchdowns",                      get_ave_getter("tds_for")),
            Column("P+",  "Average Pass completions",                get_ave_getter("passes_for")),
            Column("YP+", "Average Yards passing",                   get_ave_getter("pyards_for")),
            Column("R+",  "Average Pass receptions",                 get_ave_getter("rec_for")),
            Column("YR+", "Average Yards rushing",                   get_ave_getter("ryards_for")),
            Column("K+",  "Average Kills",                           get_ave_getter("kills_for")),
            Column("C+",  "Average Casualties",                      get_ave_getter("cas_for")),
            Column("KO+", "Average Knock outs",                      get_ave_getter("ko_for")),
            Column("S+",  "Average Stuns",                           get_ave_getter("stun_for")),
            Column("T+",  "Average Tackles",                         get_ave_getter("tckl_for")),
            Column("I+",  "Average Interceptions",                   get_ave_getter("int_for"), divider=True),
            Column("TD-", "Average Touchdowns",                      get_ave_getter("tds_against")),
            Column("P-",  "Average Pass completions",                get_ave_getter("passes_against")),
            Column("YP-", "Average Yards passing",                   get_ave_getter("pyards_against")),
            Column("R-",  "Average Pass receptions",                 get_ave_getter("rec_against")),
            Column("YR-", "Average Yards rushing",                   get_ave_getter("ryards_against")),
            Column("K-",  "Average Kills",                           get_ave_getter("kills_against")),
            Column("C-",  "Average Casualties",                      get_ave_getter("cas_against")),
            Column("KO-", "Average Knock outs",                      get_ave_getter("ko_against")),
            Column("S-",  "Average Stuns",                           get_ave_getter("stun_against")),
            Column("T-",  "Average Tackles",                         get_ave_getter("tckl_against")),
            Column("I-",  "Average Interceptions",                   get_ave_getter("int_against")),
            ],
          query = models.RaceStats.all().order("-awp"),
          id = "race-average-table",
          cls = "tablesorter",
          )

    label = "stats"
    tables[label] = Table(
          columns = [
            # profile
            Column(" ",         "Logo",                      race_getter, center=True),
            Column("Race",      "Race",                      name_getter, divider=True),
            Column("#Tm",    "Number of Teams",              attrgetter("num_of_teams")),
            Column("AWP",       "Adjusted Win Percentage",   awp_getter, divider=True),
            Column("TD+", "Average Touchdowns",              attrgetter("tds_for")),
            Column("P+",  "Average Pass completions",        attrgetter("passes_for")),
            Column("YP+", "Average Yards passing",           attrgetter("pyards_for")),
            Column("R+",  "Average Pass receptions",         attrgetter("rec_for")),
            Column("YR+", "Average Yards rushing",           attrgetter("ryards_for")),
            Column("K+",  "Average Kills",                   attrgetter("kills_for")),
            Column("C+",  "Average Casualties",              attrgetter("cas_for")),
            Column("KO+", "Average Knock outs",              attrgetter("ko_for")),
            Column("S+",  "Average Stuns",                   attrgetter("stun_for")),
            Column("T+",  "Average Tackles",                 attrgetter("tckl_for")),
            Column("I+",  "Average Interceptions",           attrgetter("int_for"), divider=True),
            Column("TD-", "Average Touchdowns",              attrgetter("tds_against")),
            Column("P-",  "Average Pass completions",        attrgetter("passes_against")),
            Column("YP-", "Average Yards passing",           attrgetter("pyards_against")),
            Column("R-",  "Average Pass receptions",         attrgetter("rec_against")),
            Column("YR-", "Average Yards rushing",           attrgetter("ryards_against")),
            Column("K-",  "Average Kills",                   attrgetter("kills_against")),
            Column("C-",  "Average Casualties",              attrgetter("cas_against")),
            Column("KO-", "Average Knock outs",              attrgetter("ko_against")),
            Column("S-",  "Average Stuns",                   attrgetter("stun_against")),
            Column("T-",  "Average Tackles",                 attrgetter("tckl_against")),
            Column("I-",  "Average Interceptions",           attrgetter("int_against")),
            ],
          query = models.RaceStats.all().order("-awp"),
          id = "race-stats-table",
          cls = "tablesorter",
          )
    # render and update
    #--------------------------------------------------------------------#

    general_statistics = misc.render('general_statistics.html', locals())
    self.update(general_statistics)

    self.response.out.write(general_statistics)

