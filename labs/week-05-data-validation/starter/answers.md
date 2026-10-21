# Week 5 — written answers

## Exercise 2

A `make validate-broken` riportja (`RawMeasurements` v1.0.0, `broken_batch.csv`, 60 sor):

```text
  7 failure case(s)

    row  column             check                            failure_case
  -----  ------------------ -------------------------------- ------------------------
      —  RawMeasurements    column_in_schema                 notes
      3  glucose            coerce_dtype('float64')          unknown
      3  glucose            dtype('float64')                 unknown
     23  bmi                less_than_or_equal_to(100.0)     280.0
      7  age                less_than_or_equal_to(120)       250
      —  glucose            greater_than_or_equal_to(0)      TypeError("'>=' not supp
      —  glucose            less_than_or_equal_to(400.0)     TypeError("'<=' not supp
```

### 1. The `notes` column

**Döntés: felvenném a contractba**, opcionális, nullázható szöveges oszlopként
(`notes: Optional[Series[str]] = pa.Field(nullable=True)`), és a `SCHEMA_VERSION`-t
`1.0.0`-ról `1.1.0`-ra emelném. Ez visszafelé kompatibilis bővítés: a régi, `notes`
nélküli batch-ek továbbra is átmennek. A `notes` nem kerül a `ModelInput`-ba, tehát a
modell nem látja. A `ModelInput` `strict = True`, ezért ott külön el kell dobni.

A másik két lehetőséget elvetném:

- **Eldobni validáció előtt:** a contract ekkor már nem azt írja le, ami a klinikáról
  ténylegesen érkezik. Ha a klinika egyszer egy valódi új mezőt is így küld, azt is
  szó nélkül eldobnánk. A `strict = True` épp azt garantálja, hogy egy ismeretlen
  oszlop nem csúszik át észrevétlenül.
- **Továbbra is elutasítani:** a klinika jelezte, hogy ezentúl minden batch-ben jön,
  így minden éjszakai futás elbukna, miközben az adat maga rendben van.

**Kinek kell jóváhagynia:** a contract két fél megállapodása. Kell hozzá a klinika
adatgazdája / data engineere, aki küldi és vállalja a formátumot, és az ML-csapat
(a contract tulajdonosa), amelyik fogadja. Mivel szabad szöveges mezőről van szó, amely
betegadatot (nevet, diagnózist) is tartalmazhat, az adatvédelmi felelőst (DPO) is be
kell vonni: tárolhatjuk-e egyáltalán Gitben / DVC-ben, vagy anonimizálni kell.

### 2. The four faults

A Pandera `row` értéke 0-tól számol, és nem számolja a fejlécet: a CSV-ben a sor száma
`row + 2`.

| # | row | CSV-sor | oszlop | rossz érték | megsértett szabály |
|---|---|---|---|---|---|
| 1 | — (egész tábla) | fejléc | `notes` | `imported from lab system v2` (nem deklarált oszlop) | `column_in_schema` (`strict = True`) |
| 2 | 3 | 5. | `glucose` | `unknown` | `coerce_dtype('float64')` |
| 3 | 7 | 9. | `age` | `250` | `less_than_or_equal_to(120)` |
| 4 | 23 | 25. | `bmi` | `280.0` | `less_than_or_equal_to(100.0)` |

**A `glucose = "unknown"` hiba okozott több sort, összesen négyet.** A lánc:

1. `coerce_dtype('float64')`: a `"unknown"` szöveget nem lehet float-tá alakítani.
2. `dtype('float64')`: emiatt az oszlop `object` típusú marad, nem `float64`, így a
   típusellenőrzés is elbukik ugyanarra a sorra.
3. és 4. `greater_than_or_equal_to(0)` és `less_than_or_equal_to(400.0)`: a két
   értékellenőrzés egy szöveget is tartalmazó `object` oszlopon fut le. A `>=` / `<=`
   összehasonlítás `str` és `int` között `TypeError`-t dob, ezért az egész ellenőrzés
   elbukik. Ezért áll `—` a `row` oszlopban: nem egy sor bukott el, hanem maga a check
   nem tudott lefutni az oszlopon.

A másik három hiba egy-egy sort ad, így jön ki a 4 hibából a 7 sor. A tanulság: egy
riport sorainak száma nem azonos a hibák számával. Egy típushiba továbbgyűrűzik az
ugyanarra az oszlopra vonatkozó összes többi ellenőrzésre, ezért mindig az oszloponkénti
első, `coerce_dtype` sort érdemes először javítani.

## Exercise 4

### 1. Without the gate, where did the row with `age = 250` go?

Gate nélkül (`make gate-fail` az Exercise 4 előtt) a `dvc repro` mindhárom stage-et
lefuttatta, hiba nélkül. A rossz sor ezeket a fájlokat érte el:

| fájl | mi történt vele | ki / mi használná |
|---|---|---|
| `data/processed/train.csv` (vagy a `test.csv`, a split dönti el) | a sor bekerült; a `train.csv` md5-je `d9eba76c…` → `267b4f5e…` | a `train` stage |
| `models/model.pkl` | újratanított modell, amely egy 250 éves páciensen is tanult | az `evaluate`, majd a `make register` / `promote`, végül a serving |
| `metrics/metrics.json` | új metrikák: accuracy 0.7656 → 0.7604, F1 0.6154 → 0.6102 | a `dvc metrics show`, a modellt összehasonlító / jóváhagyó ember |
| `dvc.lock` | rögzítette a hibás adat, a modell és a metrikák hash-ét | a következő commit: a hibás állapot „hiteles” verzióként kerülne a Gitbe |

A pipeline zöld volt, semmi nem jelezte a hibát. A modellt a következő lépésben
regisztrálhattuk és élesíthettük volna (`make register && make promote`), a gyengébb
metrikát pedig könnyen „zajnak” lehetne nézni.

A gate-tel (`make gate-fail` az Exercise 4 után) a `validate` stage `ValidationFailed`-del
kilépett (`measurements.csv broke RawMeasurements with 1 failure case(s)`). A DVC ezután
a `prepare`, `train` és `evaluate` stage-et nem futtatta. A `train.csv` md5-je előtte és
utána is `d9eba76c…`, egyetlen fájlt ért el a rossz sor: a `reports/validation.json`
riportot, amely megnevezi a hibát.

### 2. A teammate runs `prepare` by hand after a failed `validate`

A `prepare` azonnal megáll `ValidationFailed`-del (`The last validation failed with 1
failure case(s). Fix the data before you train on it.`), és nem ír `train.csv`-t /
`test.csv`-t. Ezt a `pipeline.py` `prepare` függvényének első sora okozza:

```python
    _require_validated(settings)
```

Ez beolvassa a `reports/validation.json`-t. Ha hiányzik, `FileNotFoundError`-t dob, ha
`"passed": false`, akkor `ValidationFailed`-et. Mivel a `validate` a riportot a leállás
**előtt** írja ki, egy elbukott validáció után a riport létezik, és `passed: false`.

A `dvc.yaml`-ban lévő él (`reports/validation.json` a `prepare` deps-ében) önmagában
nem elég, mert azt csak a `dvc repro` olvassa és tartatja be. A
`uv run python src/main.py prepare` közvetlenül hívja a Python-kódot, a DVC kimarad, így
a gráfról és a függőségekről semmit nem tud. Ráadásul a DVC dep csak azt nézi, hogy a
fájl létezik-e és változott-e, azt nem, hogy mi van benne: egy `"passed": false` riport
is érvényes dep lenne. A gate-nek ezért a kódban is benne kell lennie, nem csak a
pipeline leírásában.

### 3. Raising `MAX_AGE` from 120 to 125

**Jóslat:** a `MAX_AGE` a `schemas.py`-ban van. Ez a fájl a `validate`, a `train` és az
`evaluate` deps-ében szerepel, a `prepare`-ében nem. Ezért a `validate`, a `train` és az
`evaluate` lefut, a `prepare` kimarad.

**`make repro` a `MAX_AGE = 125`-tel:**

| stage | eredmény | miért |
|---|---|---|
| `validate` | **lefutott** | a dep-je, a `schemas.py` megváltozott |
| `prepare` | kimaradt (`didn't change, skipping`) | a deps-e: `measurements.csv`, `pipeline.py`, `data.py`, `reports/validation.json`. Egyik sem változott: a `validate` ugyanazt a riportot írta, mert a riportban nincs benne a `MAX_AGE`, és a 768 sor ugyanúgy átment (a legidősebb páciens 81 éves). A riport hash-e tehát ugyanaz, és a gate-en keresztül nem indul újra semmi. |
| `train` | **lefutott** | a `schemas.py` a közvetlen dep-je |
| `evaluate` | **lefutott** | a `schemas.py` a közvetlen dep-je. A metrikák bitre azonosak (accuracy 0.7656, F1 0.6154, ROC AUC 0.8183) |

A jóslat bejött.

**`make repro` a `MAX_AGE = 120` visszaállítása után:**

| stage | eredmény | miért |
|---|---|---|
| `validate` | **lefutott** | a `schemas.py` megint változott. A DVC run-cache-e ezt a deps-kombinációt már látta, de a `validate` kimenete egy sima `cache: false` out (`reports/validation.json`), amit a run-cache nem tud visszaállítani, ezért újra kell futtatni |
| `prepare` | kimaradt | ugyanaz a riport, ugyanaz a hash, mint fent |
| `train` | **lefutott** | ugyanazért, mint a `validate`: a `models/mlflow_run_id.json` sima `cache: false` out, így a run-cache nem használható |
| `evaluate` | **a run-cache-ből jött** (`is cached - skipping run, checking out outputs`) | ezt a deps-kombinációt (eredeti `schemas.py`, ugyanaz a `model.pkl` és `test.csv`) a DVC már futtatta. A kimenete egy `metrics` fájl, amelyet a run-cache a `cache: false` ellenére is vissza tud állítani |

**Kellett-e újratanítani a modellt? Nem.** A `MAX_AGE` csak az ingestion contract egyik
szabálya. Sem a tanítóadat (`train.csv` változatlan, a `prepare` nem futott), sem a
modell hiperparaméterei nem változtak, és a `random_seed` miatt a tanítás determinisztikus.
Ugyanaz a modell és ugyanazok a metrikák jöttek ki. A `train` és az `evaluate` csak azért
futott, mert a `dvc.yaml` a teljes `schemas.py` fájlt sorolja fel dep-ként, így a DVC nem
tudja megkülönböztetni a `RawMeasurements` egy határának változását a `ModelInput`
(a `train` által ténylegesen használt contract) változásától. Ez a fájlszintű függőség
ára. Finomabb gráfhoz a két contractot külön fájlba kellene tenni, és a `train`-nek csak
a `ModelInput`-ét felvenni dep-ként.
