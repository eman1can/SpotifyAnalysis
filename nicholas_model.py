import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold

from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, f1_score
from imblearn.over_sampling import SMOTE

def cv_score(model, x, y, n_folds=5, scorer=f1_score):
    folds = KFold(n_splits=n_folds, shuffle=True, random_state=0)
    scores = []
    # Oversample
    resampler = SMOTE()
    for train_index, test_index in folds.split(x):
        kf_x_train = x[train_index]
        kf_y_train = y[train_index]
        kf_x_test = x[test_index]
        kf_y_test = y[test_index]

        kf_x_train, kf_y_train = resampler.fit_resample(kf_x_train, kf_y_train)

        model.fit(kf_x_train, kf_y_train)
        kf_yh = model.predict(kf_x_test)

        score = scorer(kf_y_test, kf_yh)
        scores.append(score)
        print('.', end='')

    return np.mean(scores)

def regularize(A):
    mean = np.mean(A) 
    stdev = np.std(A)
    return (A - mean) / stdev

df = pd.read_csv('listened_data.csv')

# Prune columns
drop_cols = [df.columns[0], 'Artist Name', 'Track Name']
#drop_cols = [df.columns[0], 'Artist Name', 'Track Name', 'ms Played', 'Listen Count', 'Key']
df.drop(drop_cols, axis=1, inplace=True)  # remove index column

# Regularize columns
reg_cols = ['Loudness', 'Tempo', 'Listen Count', 'ms Played', 'Key']
for c in reg_cols:
    df.loc[:, c] = regularize(df.loc[:, c])

# Retrieve output column
y_all = df.loc[:, 'Liked'].astype(int)
y_all = y_all.to_numpy().reshape(-1)  # convert pd Series to ndarray
df.drop('Liked', axis=1, inplace=True)

print(df)

# Convert to Numpy
x_all = df.to_numpy()
print(*df.columns, sep=', ')

# Split
x_train, x_test, y_train, y_test = train_test_split(x_all, y_all,
   test_size=.20, stratify=y_all, random_state=0, shuffle=True)

# Models
models = dict()
#models['mlp'] = MLPClassifier(max_iter=100)
models['logreg'] = LogisticRegression(max_iter=100)
models['forest'] = RandomForestClassifier(n_estimators=10)
models['tree'] = DecisionTreeClassifier(criterion='gini')

folds = KFold(n_splits=5, shuffle=True, random_state=0)
cv_scores = {k: [] for k in models}
best_scores = {k: [] for k in models}
for train_index, test_index in folds.split(x_train):
    kf_x_train = x_train[train_index]
    kf_y_train = y_train[train_index]
    kf_x_test = x_train[test_index]
    kf_y_test = y_train[test_index]

    print('-'*40)

    best_m = None
    best_s = -1
    # Test regular models
    for m, model in models.items():
        # Nested CV
        print(f'{m}[', end='')
        s = cv_score(model, kf_x_train, kf_y_train)
        print(f']')
        #print(f'] {s:6.3f}')
        cv_scores[m].append(s)
        if s > best_s:
            best_s = s
            best_m = m

    # Recalculate best score and save
    models[best_m].fit(kf_x_train, kf_y_train)
    kf_yh = models[best_m].predict(kf_x_test)
    best_scores[best_m].append(f1_score(kf_y_test, kf_yh))

print('ALL CV SCORES')
for m, scores in cv_scores.items():
    print(f'{m:10}', end='')
    for s in scores:
        print(f'{s:6.3f}', end='')
    print()

print('BEST SCORES')
for m, scores in best_scores.items():
    print(f'{m:10}', end='')
    for s in scores:
        print(f'{s:6.3f}', end='')
    print()

resampler = SMOTE()
x_train, y_train = resampler.fit_resample(x_train, y_train)

# Holdout test
print('Selecting logreg as best model')
model = models['logreg'] 

model.fit(x_train, y_train)
yh = model.predict(x_test)
holdout_score = f1_score(y_test, yh)

print(f'Holdout F1 score: {holdout_score:.3f}')
print(confusion_matrix(y_test, yh))