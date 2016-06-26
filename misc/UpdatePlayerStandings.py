from google.appengine.api.labs import taskqueue
from google.appengine.api import users
from google.appengine.ext import db
############# 
# Standard Python imports. 
import os 
import sys 
import logging 
from models import *
import views

from grappl import submit


players = Player.all()
update_player_leaders(players)

views.PlayerLeaders.clear()