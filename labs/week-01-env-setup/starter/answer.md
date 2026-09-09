# Answers

## Exercise 1 

- 2-szeri futtatás kimenetei, azonosak, mert a seed nem változott:

tatraicsaba@workstation:~/Asztal/BME/mlops-course/labs/week-01-env-setup/starter$ uv run python src/main.py
Week 1 — Diabetes prediction baseline
=====================================
Dataset:        diabetes.csv (768 patients)
Diabetes rate:  34.9%
Random seed:    42
Training rows:  576
Test rows:      192

Logistic Regression metrics:
{
  "accuracy": 0.7344,
  "precision": 0.6481,
  "recall": 0.5224,
  "f1": 0.5785
}
tatraicsaba@workstation:~/Asztal/BME/mlops-course/labs/week-01-env-setup/starter$ uv run python src/main.py
Week 1 — Diabetes prediction baseline
=====================================
Dataset:        diabetes.csv (768 patients)
Diabetes rate:  34.9%
Random seed:    42
Training rows:  576
Test rows:      192

Logistic Regression metrics:
{
  "accuracy": 0.7344,
  "precision": 0.6481,
  "recall": 0.5224,
  "f1": 0.5785
}

- .env fájlban PIPELINE_RANDOM_SEED=7 -re állítva, majd `uv run python src/main.py` paranccsal futtatás kimenete:

andom seed: 42 → accuracy 0.7344, f1 0.5785
Random seed: 7 → accuracy 0.7812, f1 0.65

Tehát a 7-es random seed hatására pontosabb eredményt adott.
Más seed más véletlenszerű felosztást ad train/test halmazra,
modell "logikája" változott, hanem hogy pontosan mely 576/192 sor került a train/test halmazba.

Tanulság: érdemes több kölönböző futás eredményét vizsgálni különböző random seed-ekkel.

## Exercise 2

- Kipróbált beállítások és F1 eredményeik:
  - Alap (hangolatlan) `RandomForestClassifier`: F1 = 0.6066
  - Kézi hangolás (`n_estimators=300, max_depth=8`): F1 = 0.6032
  - `RandomizedSearchCV` (5-fold CV, F1 szerint optimalizálva, 25 kombináció): F1 = 0.5854

- Tapasztalat: a RandomizedSearchCV adta a legrosszabb eredményt a hármuk közül, pedig módszertanilag ez a legmegalapozottabb megközelítés. Az ok, hogy a keresés a train-halmazon belüli cross-validation F1-et optimalizálja, nem közvetlenül a végső test-halmaz eredményét — egy ilyen kis (768 soros) adathalmazon ez a két szám könnyen szétcsúszik, így egy jól sikerült kézi próbálkozás vagy akár az alap paraméterezés is felülmúlhatja a szisztematikus keresést.

- Végül a kézi `n_estimators=300, max_depth=8` beállítást tartottam meg (F1 = 0.6032), de ez is jól mutatja a feladat végén feszegetett problémát: már három próbálkozás után is papírra kellett írnom, melyik szám melyik beállításhoz tartozik.

