import json
import os
import webbrowser

import pandas as pd

from resources.dependencies.yql3 import *
from resources.dependencies.yql3.storage import FileTokenStore


# noinspection SqlDialectInspection
class YqlQuery(object):

    def __init__(self, config, league_id, save_bool, dev_bool, league_test_dir):

        self.league_id = league_id
        self.save_bool = save_bool
        self.dev_bool = dev_bool
        self.league_test_dir = league_test_dir
        self.league_key = None
        self.league_name = None

        command_line_only = config.getboolean("OAuth_Settings", "command_line_only")

        if not self.dev_bool:
            # yahoo oauth api (consumer) key and secret
            with open("./authentication/private.txt", "r") as auth_file:
                auth_data = auth_file.read().split("\n")
            consumer_key = auth_data[0]
            consumer_secret = auth_data[1]

            # yahoo oauth process
            self.y3 = ThreeLegged(consumer_key, consumer_secret)
            _cache_dir = config.get("OAuth_Settings", "yql_cache_dir")
            if not os.access(_cache_dir, os.R_OK):
                os.mkdir(_cache_dir)

            token_store = FileTokenStore(_cache_dir, secret="sasfasdfdasfdaf")
            stored_token = token_store.get("foo")

            if not stored_token:
                request_token, auth_url = self.y3.get_token_and_auth_url()

                if command_line_only:
                    print("Visit url %s and get a verifier string" % auth_url)
                else:
                    webbrowser.open(auth_url.decode('utf-8'))

                verifier = input("Enter the code: ")
                self.token = self.y3.get_access_token(request_token, verifier)
                token_store.set("foo", self.token)

            else:
                print("Verifying token...")
                self.token = self.y3.check_token(stored_token)
                if self.token != stored_token:
                    print("Setting stored token!")
                    token_store.set("foo", self.token)

    def yql_query(self, query):
        # print("Executing query: %s\n" % query)
        return self.y3.execute(query, token=self.token).rows

    def get_league_key(self):

        if not self.dev_bool:
            # get fantasy football game info
            game_data = self.yql_query("select * from fantasysports.games where game_key='nfl'")
            # unique league key composed of this year's yahoo fantasy football game id and the unique league id
            # self.league_key = game_data[0].get("game_key") + ".l." + self.league_id

            # print(game_data)
            # print("-" * 50)
            df = pd.DataFrame(game_data)
            # print(df.to_string())
            # print()
            self.league_key = df.loc[0, "game_key"] + ".l." + self.league_id
        else:
            with open(self.league_test_dir +
                      "/" +
                      "game_data.json", "r") as gd_file:
                game_data = json.load(gd_file)

            self.league_key = game_data[0].get("game_key") + ".l." + self.league_id

        if self.save_bool:
            with open(self.league_test_dir +
                      "/" +
                      "game_data.json", "w") as gd_file:
                json.dump(game_data, gd_file)

        return self.league_key

    def get_league_standings_data(self):

        if not self.dev_bool:
            # get data for all league standings
            league_standings_data = self.yql_query(
                "select * from fantasysports.leagues.standings where league_key='" + self.league_key + "'")
            self.league_name = league_standings_data[0].get("name")
            # TODO: incorporate winnings into reports
            # entry_fee = league_standings_data[0].get("entry_fee")
        else:
            with open(self.league_test_dir +
                      "/" +
                      "league_standings_data.json", "r") as lsd_file:
                league_standings_data = json.load(lsd_file)

            self.league_name = league_standings_data[0].get("name")

        if self.save_bool:
            with open(self.league_test_dir +
                      "/" +
                      "league_standings_data.json", "w") as lsd_file:
                json.dump(league_standings_data, lsd_file)

        return league_standings_data

    def get_roster_data(self):

        if not self.dev_bool:
            # get individual league roster
            roster_data = self.yql_query(
                "select * from fantasysports.leagues.settings where league_key='" + self.league_key + "'")
        else:
            with open(self.league_test_dir +
                      "/" +
                      "roster_data.json", "r") as rd_file:
                roster_data = json.load(rd_file)

        if self.save_bool:
            with open(self.league_test_dir +
                      "/" +
                      "roster_data.json", "w") as rd_file:
                json.dump(roster_data, rd_file)

        return roster_data

    def get_teams_data(self):

        if not self.dev_bool:
            # get data for all teams in league
            teams_data = self.yql_query(
                "select * from fantasysports.teams where league_key='" + self.league_key + "'")
        else:
            with open(self.league_test_dir +
                      "/" +
                      "teams_data.json", "r") as td_file:
                teams_data = json.load(td_file)

        if self.save_bool:
            with open(self.league_test_dir +
                      "/" +
                      "teams_data.json", "w") as td_file:
                json.dump(teams_data, td_file)

        return teams_data

    def get_matchups_data(self, chosen_week):

        if not self.dev_bool:
            result = self.yql_query(
                "select * from fantasysports.leagues.scoreboard where league_key='{0}' and week='{1}'".format(
                    self.league_key, chosen_week))
        else:
            with open(self.league_test_dir +
                      "/week_" + chosen_week + "/" +
                      "result_data.json", "r") as rsd_file:
                result = json.load(rsd_file)

        if self.save_bool:
            with open(self.league_test_dir +
                      "/week_" + chosen_week + "/" +
                      "result_data.json", "w") as rsd_file:
                json.dump(result, rsd_file)

        return result[0].get("scoreboard").get("matchups").get("matchup")

    def get_roster_stats_data(self, team, team_name, chosen_week):

        if not self.dev_bool:
            # get data for this individual team
            roster_stats_data = self.yql_query(
                "select * from fantasysports.teams.roster.stats where team_key='" + self.league_key + ".t." +
                team + "' and week='" + chosen_week + "'")
        else:
            with open(self.league_test_dir +
                      "/week_" + chosen_week + "/roster_data/" +
                      str(team_name, "utf-8").replace(" ", "-") +
                      "_roster_data.json", "r") as trd_file:
                roster_stats_data = json.load(trd_file)

        if self.save_bool:
            with open(self.league_test_dir +
                      "/week_" + chosen_week + "/roster_data/" +
                      str(team_name, "utf-8").replace(" ", "-") +
                      "_roster_data.json", "w") as trd_file:
                json.dump(roster_stats_data, trd_file)

        return roster_stats_data
