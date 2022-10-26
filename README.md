# NFL Game Prediction
This repo compares SVM and decision trees with Adaboost at the task of deciding NFL game outcomes.

## Results
The best classifier is SVM:
```
SVM:               precision    recall  f1-score   support

           0       0.76      0.71      0.73        58
           1       0.72      0.77      0.74        56

    accuracy                           0.74       114
   macro avg       0.74      0.74      0.74       114
weighted avg       0.74      0.74      0.74       114
```
This model accurately predicts 74% of games.

## Running

### Initializing the repo
I suggest using a Python venv. You may run these commands:
```sh
$ python3 -m venv .venv
$ source .venv/bin/activate
$ python3 -m pip install -r requirements.txt
```

### Obtaining the training data
The training data is already included in the `data` directory. This training data is scraped from [pro football reference](https://www.pro-football-reference.com/). You can obtain it yourself with this command:
```sh
$ python3 scrape.py -y 2021 -o data/team_stats
```

### Training locally
You may run this command:
```sh
$ python3 train.py
```

### Training with Docker
You may also train in a Docker container:
```
$ docker image build -t game-predictor ./
$ docker container run game-predictor
```
