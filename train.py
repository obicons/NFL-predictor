import asyncio
import common
import glob
import os.path
import pandas as pd
import re
import sklearn.ensemble
import sklearn.model_selection
import sklearn.metrics
import sklearn.svm
import sys
from typing import Dict, List, Optional

_PATH = 'data/team_stats'

async def main(args: List[str]):
  data_set: Dict[str, pd.DataFrame] = {}
  for csv in glob.glob(os.path.join(_PATH, '*.csv')):
    df = pd.read_csv(csv)
    team_code = _filename_to_team_code_name(csv)
    if team_code is None:
      print(f'Bad team filename: {csv}. Should be in format "[team name]_[year].csv".')
      continue
    data_set[team_code] = df

  processed_data_set = []
  for _, stats in data_set.items():
    processed_data_set += df_to_fn_examples(stats, data_set)

  processed_data_set_pd = pd.concat(processed_data_set)
  y = processed_data_set_pd['result']
  x = processed_data_set_pd.drop(['result'], axis=1)

  kf = sklearn.model_selection.KFold(shuffle=True, random_state=42)
  classifiers = []
  for train_index, test_index in kf.split(x):
    x_train, x_test = x.iloc[train_index], x.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    clf = sklearn.ensemble.AdaBoostClassifier()
    clf = clf.fit(x_train, y_train)
    y_pred = clf.predict(x_test)
    classifiers.append(clf)
    print(f'Adaboost: {sklearn.metrics.classification_report(y_test, y_pred)}')

    svm = sklearn.svm.LinearSVC(max_iter=200000)
    svm = svm.fit(x_train, y_train)
    y_pred = svm.predict(x_test)
    print(f'SVM: {sklearn.metrics.classification_report(y_test, y_pred)}', flush=True)

def df_to_fn_examples(team_data: pd.DataFrame,
                      data_set: Dict[str, pd.DataFrame]) -> List[pd.DataFrame]:
  """
  Converts the team_data into a sequence of win/loss records.
  """
  opponent_columns = [column for column in team_data.columns if re.match(r'week_.+_opponent', column)]
  won_columns = [column for column in team_data.columns if re.match(r'week_.+_won', column)]
  team_data_without_record = team_data.drop(opponent_columns + won_columns, axis=1)

  outcomes: List[pd.DataFrame] = []
  for opponent in opponent_columns:
    week_no = re.match(r'week_(.+)_opponent', opponent)[1]
    opponent_code_name = team_data[opponent].iloc[0]
    outcome = team_data[f'week_{week_no}_won'].iloc[0]
    opponent_stats = data_set[opponent_code_name].copy()
    opponent_stats.drop(
      [column for column in opponent_stats.columns if re.match(r'week_.*', column)],
      axis=1,
      inplace=True,
    )
    opponent_stats.columns = [f'__opponent_{col}' for col in list(opponent_stats.columns)]
    outcomes.append(
      pd.concat(
        (team_data_without_record, opponent_stats, pd.DataFrame.from_dict([{'result': outcome}])),
        axis=1,
      ),
    )
  return outcomes

def _filename_to_team_code_name(filename: str) -> Optional[str]:
  if match := re.match(r'(.*/)?(.*)_[0-9]+\.csv', filename):
    return common.TEAM_NAMES_TO_ABR[match[2]]
  return None

if __name__ == '__main__':
  asyncio.run(main(sys.argv))