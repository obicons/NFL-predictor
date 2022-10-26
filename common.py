TEAM_NAMES_TO_ABR = {
  'cardinals': 'crd',
  'falcons': 'atl',
  'ravens': 'rav',
  'bills': 'buf',
  'panthers': 'car',
  'bears': 'chi',
  'bengals': 'cin',
  'browns': 'cle',
  'cowboys': 'dal',
  'broncos': 'den',
  'lions': 'det',
  'packers': 'gnb',
  'texans': 'htx',
  'colts': 'clt',
  'jaguars': 'jax',
  'chiefs': 'kan',
  'raiders': 'rai',
  'chargers': 'sdg',
  'rams': 'ram',
  'dolphins': 'mia',
  'vikings': 'min',
  'patriots': 'nwe',
  'saints': 'nor',
  'giants': 'nyg',
  'jets': 'nyj',
  'eagles': 'phi',
  'steelers': 'pit',
  '49ers': 'sfo',
  'seahawks': 'sea',
  'buccaneers': 'tam',
  'titans': 'oti',
  'commanders': 'was',
}

ABR_TO_TEAM_NAME = {
  v: k for k, v in TEAM_NAMES_TO_ABR.items()
}

def merge_dicts(*dict_args) -> dict:
    """
    Given any number of dictionaries, shallow copy and merge into a new dict,
    precedence goes to key-value pairs in latter dictionaries.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result