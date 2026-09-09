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

Egyik modell sem "a valódi": mindkettő ugyanarra a kódra és adatra épül, csak más véletlenszerű train/test felosztást kapott, ezért az eredmény csak egy pontbecslés, nem a modell tényleges, megbízható teljesítménye.

Ami ténylegesen változott: a random seed a train_test_split belső véletlenszám-generátorát vezérli, tehát más seed más 576/192 sort tesz a train, illetve test halmazba. Nem a modell logikája vagy a betanítási algoritmus változott, hanem az, hogy pontosan mely betegek kerültek melyik halmazba.

Ez azért probléma egy production csapatnak, mert ha csak egyetlen futás eredményét jelentik ("0.73 accuracy"), az félrevezető lehet: a szám nagyrészt a véletlen split miatti zajt tükrözi, nem a modell valódi képességét, ami megnehezíti a modellek objektív összehasonlítását és azt eldönteni, hogy egy "jobb" eredmény valódi javulás-e vagy csak szerencse.

Tanulság: érdemes több különböző futás eredményét vizsgálni különböző random seed-ekkel, és az átlagot/szórást nézni egyetlen szám helyett.

## Exercise 2

- Kipróbált beállítások és F1 eredményeik:
  - Alap (hangolatlan) `RandomForestClassifier`: F1 = 0.6066
  - Kézi hangolás (`n_estimators=300, max_depth=8`): F1 = 0.6032
  - `RandomizedSearchCV` (5-fold CV, F1 szerint optimalizálva, 25 kombináció): F1 = 0.5854

- Tapasztalat: a RandomizedSearchCV adta a legrosszabb eredményt a hármuk közül, pedig módszertanilag ez a legmegalapozottabb megközelítés. Az ok, hogy a keresés a train-halmazon belüli cross-validation F1-et optimalizálja, nem közvetlenül a végső test-halmaz eredményét — egy ilyen kis (768 soros) adathalmazon ez a két szám könnyen szétcsúszik, így egy jól sikerült kézi próbálkozás vagy akár az alap paraméterezés is felülmúlhatja a szisztematikus keresést.

- Végül a kézi `n_estimators=300, max_depth=8` beállítást tartottam meg (F1 = 0.6032), de ez is jól mutatja a feladat végén feszegetett problémát: már három próbálkozás után is papírra kellett írnom, melyik szám melyik beállításhoz tartozik.

## Exercise 3

- A `test_split_ratios` teszt (`tests/test_data.py`) a `build_dataset` (train/test split) helyességét ellenőrzi:
  - betölti a settings-et (`load_settings()`), a teljes adatot (`load_dataframe(settings)`) és a splitet (`build_dataset(settings)`)
  - `assert len(x_train) + len(x_test) == len(frame)`: nem vész el és nem duplázódik sor a split során
  - `assert actual_test_fraction == pytest.approx(settings.test_size, abs=0.01)`: a test halmaz aránya kb. megegyezik a `settings.test_size` értékkel (`pytest.approx` kell, mert a split kerekítéssel dolgozik, 768 sor x 0.25 nem kerek szám)

- A `@pytest.mark.skip` sor törölve, `uv run pytest tests/ -v` most **4 passed** eredményt ad.

## Exercise 4

- `.env` fájlban `PIPELINE_TEST_SIZE=1.5`-re állítva, majd `uv run python src/main.py` futtatva. A hiba:

```
Traceback (most recent call last):
  File ".../src/main.py", line 5, in <module>
    main()
  File ".../src/week_01_env_setup/cli.py", line 14, in main
    settings = load_settings()
  File ".../src/week_01_env_setup/config.py", line 35, in load_settings
    _validate(settings)
  File ".../src/week_01_env_setup/config.py", line 41, in _validate
    raise ValueError("PIPELINE_TEST_SIZE must be between 0 and 1 (exclusive).")
ValueError: PIPELINE_TEST_SIZE must be between 0 and 1 (exclusive).
```

- A `config.py` modul `_validate` függvénye dobja a hibát, még a `load_settings()` hívás alatt, tehát mielőtt bármilyen adat betöltődne vagy modell tanulna.

- Ez azért jobb, mintha a hiba a `train_test_split`-en belül bukna el: a validáció a program legelején, egyértelmű, konkrét hibaüzenettel jelzi a problémát ("PIPELINE_TEST_SIZE must be between 0 and 1"), pontosan megnevezve a hibás beállítást. Ha ez csak mélyen a `scikit-learn` belsejében derülne ki, a hibaüzenet kevésbé lenne informatív, és nehezebb lenne visszavezetni a gyökérokot (a konfigurációs értéket) a stack trace alapján.

- Visszaállítva `PIPELINE_TEST_SIZE=0.25`-re, a pipeline utána megint hibamentesen fut.
