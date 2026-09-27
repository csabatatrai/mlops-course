# Answers

## Exercise 4

A legutóbbi sweep (parent: `cc7f1ed1acbe411d998833facfe8e753`) hat gyerek runja, a teszthalmazon (192 páciens, ebből 67 diabéteszes).
A TN/FP/FN/TP értékek az egyes runok `plots/confusion_matrix.png` artifactjairól származnak (MLflow UI → run → Artifacts):

| run | F1 | ROC-AUC | recall | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `rf-n_estimators=300` | **0.6240** | 0.8172 | **0.5821** | 106 | 19 | **28** | 39 |
| `rf-n_estimators=100` | 0.6066 | 0.8161 | 0.5522 | 107 | 18 | 30 | 37 |
| `logreg-C=10.0` | 0.5785 | 0.8318 | 0.5224 | 106 | 19 | 32 | 35 |
| `logreg-C=1.0` | 0.5785 | **0.8320** | 0.5224 | 106 | 19 | 32 | 35 |
| `logreg-C=0.1` | 0.5714 | 0.8301 | 0.5075 | 107 | 18 | 33 | 34 |
| `logreg-C=0.01` | 0.5047 | 0.8208 | 0.4030 | 112 | 13 | 40 | 27 |

### 1. Ugyanazt a győztest választja az F1 és a ROC-AUC?

Nem. F1 szerint az `rf-n_estimators=300` nyer (0.6240), ROC-AUC szerint a `logreg-C=1.0`
(0.8320). A sorrend szinte megfordul: ROC-AUC szerint mind a négy logreg megelőzi mindkét
forestet.

A két metrika mást mér. Az F1 egyetlen döntési küszöbön (a `predict` által használt 0.5-ön)
méri a precision és a recall egyensúlyát, vagyis azt, hogy a modell ténylegesen kiadott
döntései mennyire jók. A ROC-AUC küszöbfüggetlen: azt méri, mennyire jól rangsorolja a modell
a diabéteszes pácienseket az egészségesek elé, az összes lehetséges küszöbön átlagolva.
A logreg valószínűségei tehát jobb rangsort adnak, de a 0.5-ös küszöb nekik rosszul áll
(túl kevés pozitívot jósolnak, alacsony a recall). A forest rangsora valamivel gyengébb,
de az alapértelmezett küszöbön több beteget talál meg.

### 2. Melyik runt promotálnám?

**`59b107029f2d4c1284e18005fcefaf43`** (`rf-n_estimators=300`).

Diabétesz-szűrésnél a false negative (beteg, akit egészségesnek mondunk) sokkal drágább
hiba, mint a false positive, mert a kiszűrt betegség kezeletlen marad, míg egy téves
pozitív csak egy további vizsgálatba kerül. A confusion matrixok alapján ez a modell a
legjobb logreghez (`C=1.0`) képest ugyanannyi false positive mellett (19) 4-gyel kevesebb
beteget téveszt el (28 vs. 32 FN), vagyis a jelenlegi küszöbön szigorúan jobb döntéseket hoz.
A logreg magasabb ROC-AUC-ja csak akkor érne többet, ha a küszöböt külön hangolnánk, ez
viszont egy újabb, még nem mért kísérlet lenne.

### 3. Mit rögzített az MLflow, amire nem kellett emlékeznem?

A `mlflow.parentRunId` rendszer-taget: minden gyerek run automatikusan megkapta a szülő sweep
azonosítóját, ez teszi lehetővé, hogy a `search_sweep_runs` pontosan egy sweep gyerekeit
kérdezze le. Emellett magától rögzítette a teljes git commit hash-t
(`mlflow.source.git.commit`), a futtató felhasználót (`mlflow.user`), a belépési pontot
(`mlflow.source.name = src/main.py`) és a runok kezdési/befejezési idejét.

## Exercise 6

A registry állapota a feladat végén (`diabetes-classifier`):

| verzió | forrás-run | a run `git_commit`-ja | tree állapota | promotálva |
| --- | --- | --- | --- | --- |
| 1 | `59b10702…` | `2814c63` | nincs rögzítve | nem |
| 2 | `59b10702…` | `2814c63` | nincs rögzítve | igen |
| 3 | `80577d46…` | `af138ea` | `git_dirty=true` | igen |
| 4 | `07851a8d…` | `ee794dc` | `git_dirty=false` | igen, jelenleg `@staging` és `@champion` |

A 3-as verzió forrás-runja azért dirty, mert a commit után, de még a `make sweep` előtt
javítottam egy kommentet a `tests/test_tracking.py`-ban. A `git_dirty()` ezt is észrevette,
ezért még egyszer commitoltam, és újrafuttattam a láncot (sweep → register → promote), így
lett a 4-es verzió.

### 1. A traceability lánc lépésenként

Kiindulás: `models:/diabetes-classifier@staging`.

1. **alias → verzió:** `client.get_model_version_by_alias("diabetes-classifier", "staging")`
   → 4-es verzió.
2. **verzió → run:** a `ModelVersion.run_id` mező (a regisztráció rögzítette, mert
   `runs:/<run_id>/model` URI-ból regisztráltunk) → `07851a8d48ee4a00921d1e4063538bb9`.
   Ha üres lenne, a lánc itt megszakadna.
3. **run → bizonyítékok:** `client.get_run(run_id)` → `run.data.params`, `run.data.metrics`,
   `run.data.tags`. Ebből jön a `git_commit` (`ee794dc`) és a `git_dirty` (`false`) tag.
4. **commit → kód:** ez már nem MLflow-hívás, hanem git:
   `git diff --stat ee794dc -- .` (vagy `git checkout ee794dc`). Az üres diff azt jelenti,
   hogy a mostani kód azonos azzal, ami futott.

### 2. Mit adott a hop 4 a 2. részben, és mit javított a `git_dirty`?

A 2. részben a trace a `2814c63` commitra mutatott. A `git diff --stat 2814c63 -- .`
szerint azóta 5 fájl változott, 125 sor hozzáadással, és abban a commitban a `registry.py`
még 4 befejezetlen `TODO(student)`-ot tartalmazott. Ennél is rosszabb: a sweep-ciklust
(Exercise 3) csak később, a `75e2ca9` commitban commitoltam. A runt tehát olyan kód hozta
létre, amit a hozzá rögzített commit **nem is tartalmaz**. A hop 4 konkrétan azt adta, hogy
kiderült: a `git_commit` tag ebben a formában nem bizonyíték, csak egy közelítés.

A `git_dirty` tag ezt javította: most már maga a run mondja meg, hogy a commit igaz-e.
A `false` azt jelenti, hogy a commit pontosan az a kód, ami futott, a `true` pedig, hogy
nem, és ezt a `make trace` ki is írja. Amit viszont nem ad meg:

- dirty esetben nem mondja meg, **mi** volt a különbség, mert a diff nincs elmentve, így a
  3-as verzió kódját ma már nem lehet pontosan helyreállítani;
- a kódon kívüli bemeneteket nem fedi le: az adatfájl tartalmát, a futtatókörnyezetet és
  a `.env` beállításait (ez utóbbi git-ignorált);
- nem akadályoz meg semmit, csak rögzít: a dirty 3-as verziót ugyanúgy lehetett promotálni.

### 3. Utasítsa-e el a `promote_to_staging` a dirty forrás-runból származó verziót?

**Igen, utasítsa el.** A promóció egy olyan pont, ahol azt állítjuk, hogy ez a verzió
ellenőrzött és visszakövethető. Egy dirty runnál ez az állítás hamis, mert a futott kódot
senki sem tudja reprodukálni. A 3-as verzióm jó példa: a rendszer gond nélkül promotálta,
pedig a forrás-runja nem a commitolt kódból futott. Ha egy ilyen verzió gyártásba kerül és
hibázik, a hiba okát nem lehet a kódban megkeresni. Kísérletezni továbbra is lehet dirty
treeből, csak promotálni nem.

**Az ára:** minden promóció előtt commitolni kell, majd újra kell tanítani a commitolt
kódból. Ez lassítja az iterációt, és néha feleslegesen szigorú: nálam egyetlen
kommentjavítás miatt kellett a teljes sweepet újrafuttatni, pedig az a modellt nem
befolyásolta. Kell egy döntés az `unknown` állapotról is (gitrepón kívüli futás), amit
szintén el kellene utasítani, ez pedig például egy notebookból történő gyors próbát is
kizár a promócióból.

### 4. Mit tud egy alias, amit egy fix `Staging` stage nem?

- **Egy verzión több alias is lehet egyszerre.** A 4-es verzión most a `staging` és a
  `champion` is ott van. Egy verzió viszont egyszerre csak egy stage-ben lehetett.
- **Egy alias pontosan egy verzióra mutat**, ezért a `models:/diabetes-classifier@champion`
  URI mindig egyértelmű. `Production` stage-ben viszont egyszerre több verzió is lehetett,
  és akkor nem volt egyértelmű, melyiket kell kiszolgálni.
- **A neveket mi választjuk.** Nem kell a `None/Staging/Production/Archived` állapotgépbe
  illeszkedni: lehet `champion`, `challenger`, vagy akár ügyfelenkénti alias.
- **Az alias áthelyezése nem módosítja a verziót.** A promóció és a rollback csak egy
  pointer áthelyezése, a verzió immutable marad, a stage-váltás viszont a verzió állapotát
  írta át.

### 5. A lánc vége: `data/diabetes.csv`

A lánc legvégén a `data_path` param áll, értéke `diabetes.csv`, vagyis csak egy
**fájlnév**. Ez nem mondja meg, milyen bájtok voltak a fájlban a tanításkor. Ha valaki
módosít benne egy sort, a fájlnév ugyanaz marad, és minden rögzített metrika (például a
`validation_f1 = 0.6240` a 4-es verzión) csendben elavul, anélkül hogy az MLflow-ban bármi
figyelmeztetne.

Ebben a laborban ezt véletlenül a git elfedi: a `data/diabetes.csv` a repóban van, ezért
a clean tree + commit hash technikailag az adatot is rögzíti. Ez azonban csak azért
működik, mert a fájl kicsi (768 sor). Valódi projektekben az adat túl nagy a githez,
külső tárolóban van (például MinIO-ban vagy adatbázisban), és ott a commit hash semmit sem
mond róla. A metrikák tehát csak annyira megbízhatóak, amennyire feltételezzük, hogy az adat
nem változott.

A rés lezárásához az adatot is verziózni kellene: az adatfájl tartalom-hash alapú
azonosítója (például DVC-vel, MinIO-val mint tárolóval) kerüljön be a run paraméterei vagy
tagjei közé, így a lánc a fájlútvonal helyett egy konkrét adat-snapshotnál érne véget, amit
vissza is lehet állítani.
