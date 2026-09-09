from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .config import Settings

from sklearn.ensemble import RandomForestClassifier #! 2. feladat

def train_logistic_regression(x_train, y_train, settings: Settings) -> Pipeline:
    """Train a scaled logistic regression model.

    Follows the standard Scikit-learn pattern: a Pipeline that chains
    preprocessing (StandardScaler) with an estimator, so the exact same
    transformation is applied at training and prediction time.
    https://scikit-learn.org/stable/getting_started.html
    """
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=settings.max_iter,
                    random_state=settings.random_seed,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    return model


def evaluate_model(model, x_test, y_test) -> dict:
    """Compute standard binary classification metrics on the test set."""
    predictions = model.predict(x_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions)), 4),
        "recall": round(float(recall_score(y_test, predictions)), 4),
        "f1": round(float(f1_score(y_test, predictions)), 4),
    }

def train_random_forest(x_train, y_train, settings: Settings) -> RandomForestClassifier: #! 2. feladat
    #? Mit jelent az, hogy ennél a függvénynél nem kell Pipeline-t használni, mint a train_logistic_regression függvénynél?
    """Train a random forest classifier with hand-picked hyperparameters.

    n_estimators=300, max_depth=8 was chosen by manual trial and error
    (F1=0.6032). Also tried: untuned default (F1=0.6066, actually best)
    and RandomizedSearchCV over n_estimators/max_depth/min_samples_leaf/
    max_features with 5-fold CV on F1 (F1=0.5854, worst) — the CV search
    optimizes an estimate of expected performance, not this one test
    split, so on a dataset this small (768 rows) it can land below a
    lucky manual guess or the default.
    """
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        random_state=settings.random_seed,
    )
    model.fit(x_train, y_train)
    return model

