import unittest
from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub
from google.appengine.api import memcache

from models import *

class TestPickem(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()
    # Create a consistency policy that will simulate the High Replication consistency model.
    self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
    # Initialize the datastore stub with this policy.
    self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

  def tearDown(self):
    self.testbed.deactivate()

  def test_OFLParser_GetMatchesFromHTML_matchCount(self):
    # Create a stub map so we can build App Engine mock stubs.
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

    # Register App Engine mock stubs.
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())
    parser = OFLScheduleParser()
    data=[]
    data = parser.parse(10,1) #Get matches from old season/week.
    self.assertEqual(20*11, len(data)) #Return 20 * 11 pieces of data
    
  def test_OFLMatchTracker_ConvertRawDataToPlayedMatch_ValidMatch(self):
    #input data
    data=['background-color:#CC7528', 'images/icons/Logo_Neutre_Lazarus.png', 'Miasmic Misery', 'Lazarus', 'Nurgle', '2 - 1', 'background-color:#274A06', 'images/icons/Logo_Neutre_Killabruh4.png', 'Hood Rats', 'killabruh', 'Skaven']
    season = 10
    week = 1
    ofl_week_key = db.Key.from_path('OFL_Week', '%s:%s' % (season, week))
    match_list = OFL_Match_Tracker.get_match_list(season, week,data)    
    db.put(match_list)
    self.assertEqual(True, match_list[0].gamePlayed)
    self.assertEqual(1, len(match_list))
    self.assertEqual(1, OFL_Match.all().ancestor(ofl_week_key).count(2))
    
  def test_OFLMatchTracker_ConvertRawDataToUnplayedMatch_ValidMatch(self):
    data=['background-color:#800000', 'images/icons/Logo_Neutre_Orabbi3.png', 'OFL RAGE QUIT', 'orabbi', 'Chaos Dwarf', 'images/vs.gif', 'background-color:#F601E5', 'images/icons/Logo_Neutre_Rauni.png', 'Nebraskull HornHuskers', 'RaUni', 'Dark Elf']  
    season = 10
    week = 1
    ofl_week_key = db.Key.from_path('OFL_Week', '%s:%s' % (season, week))
    match_list = OFL_Match_Tracker.get_match_list(season, week, data)
    db.put(match_list)
    self.assertEqual(False, match_list[0].gamePlayed)
    self.assertEqual(1, len(match_list))
    self.assertEqual(1, OFL_Match.all().ancestor(ofl_week_key).count(2))
    
  def test_PTracker_CreatePredictions_Create20(self):
    #inputs
    season = 10
    week = 1
    ofl_week = OFL_Week(key_name="%s:%s"%(season,week)).put()
    coach = Coach(key_name="mardaed").put()
    data = ['background-color:#CC7528', 'images/icons/Logo_Neutre_Lazarus.png', 'Miasmic Misery', 'Lazarus', 'Nurgle', '2 - 1', 'background-color:#274A06', 'images/icons/Logo_Neutre_Killabruh4.png', 'Hood Rats', 'killabruh', 'Skaven', 'background-color:#B70001', 'images/icons/Logo_Neutre_Astrospider16.png', 'Servants of Saruman', 'Astrospider', 'Orc', '0 - 1', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Voltron2.png', 'Vindictive', 'Voltron', 'Amazon', 'background-color:#F5FF00', 'images/icons/Logo_Neutre_Bob1524.png', 'Stout Lagerhead AllStars', 'bob152', 'Dwarf', '0 - 1', 'background-color:#F50000', 'images/icons/Logo_Neutre_Viajero.png', 'Clumsy Dodgers', 'Viajero', 'Pro Elf', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Slam.png', 'Cereal Killers', 'Slam', 'Chaos Pact', '1 - 0', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Belasco.png', 'A Nightmare on Elf Street', 'Sunhawk8044', 'Dark Elf', 'background-color:#590052', 'images/icons/Logo_Neutre_Jako3.png', 'Snotbloods TastyTreats', 'Jako', 'Circus', '1 - 1', 'background-color:#800000', 'images/icons/Logo_Neutre_Orabbi3.png', 'OFL RAGE QUIT', 'orabbi', 'Chaos Dwarf', 'background-color:#FF55F3', 'images/icons/Logo_Amazon_Pink_Spades.png', 'Pink Spades', 'damek', 'Amazon', '0 - 3', 'background-color:#1B023C', 'images/icons/Logo_Neutre_Wraith2.png', 'Orkemon', 'The Wraith', 'Orc', 'background-color:#6D6D6D', 'images/icons/Logo_Neutre_Toast2.png', 'Clan Venom', 'Toast', 'Skaven', '0 - 2', 'background-color:#4600AB', 'images/icons/Logo_Neutre_Timdog6.png', 'Testicular Elephantitis', 'timdog', 'Chaos Dwarf', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_GeneralKale2.png', 'Soup to Nuts', 'General Kale', 'Chaos Pact', '1 - 3', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_TrickIce5.png', 'Coolswamp Bogcrocs', 'TrickIce', 'Lizardmen', 'background-color:#00FF01', 'images/icons/Logo_Neutre_Belasco2.png', 'Woodstock Warriors', 'Belasco', 'Wood Elf', '2 - 1', 'background-color:#9E55FE', 'images/icons/Logo_Neutre_BloodedCat.png', 'Shakespears Encore', 'bloodedcat', 'Undead', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Hammertime4.png', 'SPINAL SNAP', 'HammerTime', 'Orc', '3 - 0', 'background-color:#B70001', 'images/icons/Logo_Neutre_papadrgon2.png', 'Clan Dragonbane', 'papadragon', 'Dwarf', 'background-color:#5FC809', 'images/icons/Logo_Neutre_elessar92.png', 'Warp Factor Eleven', 'elessar9', 'Underworld', '0 - 2', 'background-color:#CC7528', 'images/icons/Logo_Neutre_Jasfoz4.png', 'Grimm Moor Bullies', 'jasfoz22', 'Necromantic', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Thul3.png', 'Oblivion Knights', 'Thul', 'Chaos', '1 - 1', 'background-color:#00FF01', 'images/icons/Logo_Human_Fist.png', 'FI$T FIR$T', 'Jackal', 'Human', 'background-color:#800000', 'images/icons/Logo_Neutre_Astrospider.png', 'Red Heck Rejects', 'Blitzkreig', 'Chaos', '0 - 3', 'background-color:#F601E5', 'images/icons/Logo_Neutre_Rauni.png', 'Nebraskull HornHuskers', 'RaUni', 'Dark Elf', 'background-color:#022D24', 'images/icons/Logo_Neutre_Squall2.png', 'Cactuar Calamity', 'Squall', 'Skaven', '1 - 2', 'background-color:#4600AB', 'images/icons/Logo_Neutre_OPHare.png', 'Zerg Rush', 'OPHare', 'Chaos', 'background-color:#F601E5', 'images/icons/Logo_Neutre_Gymbo.png', 'Real Hussies of Bloodbowl', 'Gym-Bo', 'Halfling', '0 - 2', 'background-color:#8C4E1D', 'images/icons/Logo_Neutre_Tlsjr5.png', 'The Circus', 'tlsjr117', 'Nurgle', 'background-color:#4A0001', 'images/icons/Logo_Neutre_Mumbles.png', 'IronTree Hurlers', 'Nimrokon', 'Wood Elf', '1 - 2', 'background-color:#341E09', 'images/icons/Logo_Neutre_Nimrokon.png', 'Undermountain Hammerhands', 'BSUCardinalfan', 'Chaos Dwarf', 'background-color:#4A0001', 'images/icons/Logo_Neutre_Norse3.png', 'Nehekhara Nightmare', 'Norse', 'Khemri', '1 - 1', 'background-color:#0E0E0E', 'images/icons/Logo_Neutre_Sabonnel3.png', 'Creeping Death', 'sabonnel', 'Nurgle', 'background-color:#800000', 'images/icons/Logo_Neutre_Wildfire403.png', 'Hexoatl Hurricanes', 'Wildfire40', 'Lizardmen', '3 - 0', 'background-color:#1B023C', 'images/icons/Logo_Neutre_pdarby2.png', 'Heroes of Lore', 'pdarby', 'Necromantic', 'background-color:#55A9FF', 'images/icons/logo_lizardman_08.png', 'Brackish Brawlers', 'Darken-Rahl', 'Lizardmen', '2 - 2', 'background-color:#4A0001', 'images/icons/Logo_Neutre_Voltron.png', 'Phoenix Kings', 'Mardaed', 'High Elf', 'background-color:#9E0095', 'images/icons/Logo_Neutre_Cullen3.png', 'Maelstrom Marauders', 'Cullen', 'Chaos Pact', '0 - 3', 'background-color:#800000', 'images/icons/Logo_Neutre_Sleazy.png', 'Neverland Thrillers', 'michaels', 'Undead']
    match_list = OFL_Match_Tracker.get_match_list(season, week, data)
    db.put(match_list)

    p_list = OFL_Prediction_Tracker.create_predictions(match_list, coach)
    #check that list is properly populated
    self.assertEqual(20, len(p_list))
    db.put(p_list)
    #now check that a db.put can be called again
    self.assertEqual(20, OFL_Prediction.all().ancestor(ofl_week).count(25))  

  def test_PTracker_DisqualifiesPredictionIfMatchPlayed(self):
    data=['background-color:#CC7528', 'images/icons/Logo_Neutre_Lazarus.png', 'Miasmic Misery', 'Lazarus', 'Nurgle', '2 - 1', 'background-color:#274A06', 'images/icons/Logo_Neutre_Killabruh4.png', 'Hood Rats', 'killabruh', 'Skaven']
    season = 10
    week = 1
    ofl_week = OFL_Week(key_name="%s:%s"%(season,week))
    coach = Coach(key_name="mardaed")
    match_list = OFL_Match_Tracker.get_match_list(season, week,data)    
    p_list = OFL_Prediction_Tracker.create_predictions(match_list, coach)
    self.assertEqual(True,p_list[0].disqualified)

  def test_PTracker_NoDisqualifyIfMatchNotPlayed(self):
    data=['background-color:#CC7528', 'images/icons/Logo_Neutre_Lazarus.png', 'Miasmic Misery', 'Lazarus', 'Nurgle', 'images/vs.gif', 'background-color:#274A06', 'images/icons/Logo_Neutre_Killabruh4.png', 'Hood Rats', 'killabruh', 'Skaven']
    season = 10
    week = 1
    ofl_week = OFL_Week(key_name="%s:%s"%(season,week))
    coach = Coach(key_name="mardaed")
    match_list = OFL_Match_Tracker.get_match_list(season, week,data)    
    p_list = OFL_Prediction_Tracker.create_predictions(match_list, coach)
    self.assertEqual(False,p_list[0].disqualified)
    
  def test_PTracker_CreatePredictions_Return1PredictionEachFor2Coaches(self):
    #inputs
    season = 10
    week = 1
    ofl_week = OFL_Week(key_name="%s:%s"%(season,week)).put()
    coach = Coach(key_name="mardaed").put()
    coach2 = Coach(key_name="bob152").put()
    data=['background-color:#800000', 'images/icons/Logo_Neutre_Orabbi3.png', 'OFL RAGE QUIT', 'orabbi', 'Chaos Dwarf', 'images/vs.gif', 'background-color:#F601E5', 'images/icons/Logo_Neutre_Rauni.png', 'Nebraskull HornHuskers', 'RaUni', 'Dark Elf']  
    match_list = OFL_Match_Tracker.get_match_list(season, week, data)
    self.assertEqual(1, len(match_list))
    db.put(match_list)
    p_list = OFL_Prediction_Tracker.create_predictions(match_list, coach)
    db.put(p_list)
    #Checking output is correct and as expected.
    self.assertEqual(1,len(p_list))
    self.assertEqual("mardaed", p_list[0].coach.key().name())
    #making second entry
    p_list2 = OFL_Prediction_Tracker.create_predictions(match_list, coach2)
    db.put(p_list2)
    self.assertEqual(1,len(p_list2))
    self.assertEqual("bob152", p_list2[0].coach.key().name())
    #Now checking DB entries can be retrived
    self.assertEqual(1, OFL_Prediction.all().ancestor(ofl_week).filter("coach =", coach).count(25))
    self.assertEqual(1, OFL_Prediction.all().ancestor(ofl_week).filter("coach =", coach2).count(25))
    self.assertEqual(2, OFL_Prediction.all().ancestor(ofl_week).count(25))       
    
  def test_OFL_Prediction_Score_Match_NoWagerNothingDone(self):
    prediction = OFL_Prediction(wager = 0, selection = 0)
    prediction.scoreMatch(2,2)
    self.assertEqual(0, prediction.points) 

  def test_OFL_Prediction_Score_Match_WagerRightAndAddedToPoints(self):
    prediction = OFL_Prediction(wager = 10, selection = -1)
    prediction.scoreMatch(3,2)
    self.assertEqual(10, prediction.points) 

  def test_OFL_Prediction_Score_Match_WagerWrongAndNoPoints(self):
    prediction = OFL_Prediction(wager = 10, selection = -1)
    prediction.scoreMatch(2,2)
    self.assertEqual(0, prediction.points)    
    
  def test_OFL_Prediction_Score_Match_NewMatchResultWrongToRightPointsAdded(self):
    prediction = OFL_Prediction(wager = 10, selection = 0, points = 0)
    prediction.scoreMatch(2,2)
    self.assertEqual(10, prediction.points)    
    
  def test_OFL_Prediction_Score_Match_NewMatchResultRightToWrongPointsSubtracted(self):
    prediction = OFL_Prediction(wager = 10, selection = -1, points = 10)
    prediction.scoreMatch(2,3)
    self.assertEqual(0, prediction.points)  
  
  def test_OFL_Match_Tracker_query_match_list_pulls_from_cache(self):
    match_list = []
    
    self.assertEqual(1, len(match_list))  
  
  def test_PTracker_UpdatePredictions_UpdatesPredictionForMatch_PointsTalliedForBoth(self):
    data=['background-color:#CC7528', 'images/icons/Logo_Neutre_Lazarus.png', 'Miasmic Misery', 'Lazarus', 'Nurgle', '2 - 1', 'background-color:#274A06', 'images/icons/Logo_Neutre_Killabruh4.png', 'Hood Rats', 'killabruh', 'Skaven']
    season = 10
    week = 1
    ofl_week = OFL_Week(key_name="%s:%s"%(season,week))
    match_list = OFL_Match_Tracker.get_match_list(season, week,data)  
    match = match_list[0]
    coach = Coach(key_name="mardaed")
    coach2 = Coach(key_name="bob152")
    prediction = OFL_Prediction(coach = coach, wager = 10, selection = -1, parent = ofl_week).put()
    prediction2 = OFL_Prediction(coach = coach2, wager = 20, selection = -1, parent = ofl_week).put()
    OFL_Prediction_Tracker.update_predictions(match)
    prediction = OFL_Prediction.all().ancestor(ofl_week).filter("coach =", coach)
    prediction2 = OFL_Prediction.all().ancestor(ofl_week).filter("coach =", coach2)
    self.assertEqual(10, prediction.score)
    self.assertEqual(20, prediction2.score)
  
  def testEventuallyConsistentGlobalQueryResult(self):
    class TestModel(db.Model):
      pass

    user_key = db.Key.from_path('User', 'ryan')
    # Put two entities
    db.put([TestModel(parent=user_key), TestModel(parent=user_key)])

    # Global query doesn't see the data.
    self.assertEqual(0, TestModel.all().count(3))
    # Ancestor query does see the data.
    self.assertEqual(2, TestModel.all().ancestor(user_key).count(3))

if __name__ == '__main__':
    unittest.main()