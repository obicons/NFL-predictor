import aiofile
import aiohttp
import argparse
import asyncio
import bs4
import common
import logging
import os
import sys
from typing import List

_logger = logging.getLogger()

async def main(args: List[str]):
  logging.basicConfig(level=logging.INFO)

  parser = argparse.ArgumentParser(args[0])
  parser.add_argument(
    '-o',
    '--output',
    type=str,
    dest='output',
    help='directory to store data',
    required=True,
  )
  parser.add_argument(
    '-y',
    '--year',
    type=int,
    dest='year',
    help='year',
    required=True,
  )
  parsed_args = parser.parse_args()

  connector = aiohttp.TCPConnector(ssl=False)
  timeout = aiohttp.ClientTimeout(10)
  async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
    downloads = [
      _download_and_save(parsed_args.output, team, parsed_args.year, session)
      for team in common.TEAM_NAMES_TO_ABR
    ]
    await asyncio.gather(*downloads)

async def _download_and_save(output: str, team: str, year: int, session: aiohttp.ClientSession):
  while True:
    try:
      stats = await _download_stats(team, year, session)
      break
    except asyncio.TimeoutError:
      _logger.error(f'Timeout getting stats for {team}. Retrying.')
  await _write_csv(os.path.join(output, f'{team}_{year}.csv'), stats)

async def _write_csv(output_filename: str, data: dict):
  async with aiofile.async_open(output_filename, 'w') as file:
    sep = ''
    for key in data:
      await file.write(f'{sep}{key}')
      sep = ','
    await file.write('\n')

    sep = ''
    for _, v in data.items():
      await file.write(f'{sep}{v}')
      sep = ','
    await file.write('\n')


async def _download_stats(team_name: str,
                          year: int,
                          session: aiohttp.ClientSession) -> dict:
  assert team_name in common.TEAM_NAMES_TO_ABR
  async with session.get(_make_advanced_stat_url(team_name, year)) as adv_response:
    async with session.get(_make_url(team_name, year)) as stat_response:
      adv_soup = bs4.BeautifulSoup(await adv_response.text(), features='html.parser')
      stat_soup = bs4.BeautifulSoup(await stat_response.text(), features='html.parser')
      passing_stats = extract_passing_stats(adv_soup)
      rushing_stats = extract_rushing_stats(adv_soup)
      defensive_stats = extract_defensive_stats(adv_soup)
      overall_stats = extract_overall_stats(stat_soup)
      return common.merge_dicts(passing_stats, rushing_stats, defensive_stats, overall_stats)

def extract_overall_stats(soup: bs4.BeautifulSoup) -> dict:
  table = soup.find(id='team_stats')
  rows = table.find_all('tr')
  allowed_yards_per_carry = float(rows[3].find_all('td')[17].text)
  offense_rank = int(rows[4].find_all('td')[0].text)
  defense_rank = int(rows[5].find_all('td')[0].text)
  plays_for = int(rows[2].find_all('td')[0].text)
  plays_against = int(rows[3].find_all('td')[0].text)
  turnovers_given = int(rows[2].find_all('td')[4].text)
  turnovers_taken = int(rows[3].find_all('td')[4].text)
  penalties_committed = int(rows[2].find_all('td')[19].text)
  pts_per_drive = float(rows[2].find_all('td')[29].text)
  pts_per_drive_allowd = float(rows[3].find_all('td')[29].text)
  return common.merge_dicts(
    {
      'allowed_yards_per_carry': allowed_yards_per_carry,
      'offense_rank': offense_rank,
      'defense_rank': defense_rank,

      # These turnover numbers reduced accuracy.
      # 'turnovers_given_per_play': turnovers_given / plays_for,
      # 'turnovers_taken_per_pay': turnovers_taken / plays_against,

      # Penalties also hurt accuracy.
      # 'penalties_per_play': penalties_committed / plays_for,

      # Points also hurt accuracy.
      # 'pts_per_drive': pts_per_drive,
      # 'allowed_pts_per_drive': pts_per_drive_allowd,
    },
    extract_record(soup),
  )

def extract_record(soup: bs4.BeautifulSoup) -> dict:
  games_table = soup.find(id='games')
  games_rows = games_table.find_all('tr')[2:]
  record = {}
  for i in range(len(games_rows)):
    data = list(games_rows[i].children)
    week_result = f'week_{data[0].text}_won'
    outcome = data[5].text
    if outcome == '':
      continue
    record[week_result] = 1 if outcome == 'W' else 0

    try:
      opp_elmt = data[9]
      opp_code_name = opp_elmt.find('a')['href'].split('/')[2]
      oponent_column = f'week_{data[0].text}_opponent'
      record[oponent_column] = opp_code_name
    except:
      pass

  return record

def extract_passing_stats(soup: bs4.BeautifulSoup) -> dict:
  total_cmps = 0
  total_atts = 0
  total_yards = 0
  air_yards_table = soup.find(id='advanced_air_yards')
  for stat_line in air_yards_table.find_all('tr')[2:]:
    stats = stat_line.find_all('td')
    total_cmps += int(stats[5].text)
    total_atts += int(stats[6].text)
    total_yards += int(stats[7].text)
  return {
    'completion_percent': total_cmps / total_atts,
    'yards_per_pass': total_yards / total_atts,
  }

def extract_rushing_stats(soup: bs4.BeautifulSoup) -> dict:
  all_advanced_rushing = soup.find(id='all_advanced_rushing')
  div_comment = all_advanced_rushing.find(string=lambda text: isinstance(text, bs4.Comment))
  div_soup = bs4.BeautifulSoup(div_comment, features='html.parser')
  totals = div_soup.find('tfoot').find_all('td')
  atts = int(totals[5].text)
  yards = int(totals[6].text)
  return {
    'yards_per_carry': yards / atts,
  }

def extract_defensive_stats(soup: bs4.BeautifulSoup) -> dict:
  all_advanced_defense = soup.find(id='all_advanced_defense')
  div_comment = all_advanced_defense.find(string=lambda text: isinstance(text, bs4.Comment))
  div_soup = bs4.BeautifulSoup(div_comment, features='html.parser')
  totals = div_soup.find('tfoot').find_all('td')
  ints = int(totals[5].text)
  atts = int(totals[6].text)
  cmps = int(totals[7].text)
  sacks = float(totals[20].text)
  return {
    'taken_ints_per_pass': ints / atts,
    'allowed_completion_percent': cmps / atts,
    'inflicted_sacks_per_pass': sacks / atts,
  }

def _make_advanced_stat_url(team_name: str, year: int) -> str:
  assert team_name in common.TEAM_NAMES_TO_ABR
  return f'https://www.pro-football-reference.com/teams/{common.TEAM_NAMES_TO_ABR[team_name]}/{year}_advanced.htm'

def _make_url(team_name: str, year: int) -> str:
  assert team_name in common.TEAM_NAMES_TO_ABR
  return f'https://www.pro-football-reference.com/teams/{common.TEAM_NAMES_TO_ABR[team_name]}/{year}.htm'

if __name__ == '__main__':
  asyncio.run(main(sys.argv))