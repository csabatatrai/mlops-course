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

## Exercise 7

A README a 3-as verziót tekinti hibásnak, nálam viszont a 4-es volt az aktív, ezért
a 4-esről gördítettem vissza:

```text
make rollback VERSION=1 REASON="v4 misbehaves in staging"
Refused: Version 1 was never promoted, so it is not a known-good rollback target.

make rollback VERSION=2 REASON="v4 misbehaves in staging"
Rolled back from version 4 to version 2.
Version 2 now carries aliases: ['champion', 'staging']
```

Az 1-es verziót a rendszer elutasította, mert sosem volt promotálva: nincs `promoted_at`
tagje, így senki sem nézte át, és egy "rollback" rá valójában egy át nem nézett promóció
lenne.

A registry alias-táblája a rollback után:

```text
        name         |  alias   | version
---------------------+----------+---------
 diabetes-classifier | staging  |       2
 diabetes-classifier | champion |       2
```

### 1. Mi változott a rollbackkel, és mi nem?

**Változott:** két pointer. A `staging` és a `champion` alias a 4-es verzióról a 2-esre
került, és a 4-es verzió kapott három taget (`rolled_back_at`, `rolled_back_to = 2`,
`rollback_reason = "v4 misbehaves in staging"`).

**Nem változott:** minden más. Egyik verzió sem módosult és egyik sem törlődött, a
modellfájlok a MinIO-ban ugyanazok, a runok, a paraméterek és a metrikák érintetlenek.
A 4-es verzió is megmaradt, bármikor vissza lehet rá állni.

Egy szerver, amely a `models:/diabetes-classifier@champion` URI-ból tölt, a saját kódján
és konfigurációján semmit sem változtat, a **következő betöltéskor** mégis a 2-es verziót
kapja, mert az alias egy szerepet nevez meg, nem egy verziót. Ami már a memóriában van,
az viszont nem cserélődik magától: egy szerver, amely korábban betöltötte a 4-est, addig
azt szolgálja ki, amíg újra nem tölti a modellt. Ez a rollback registry-oldali fele, a
kiszolgáló oldali átállás a 10. hét témája.

### 2. Hogyan tudná meg egy auditor egy hónap múlva, hogy a 4-es volt a champion?

A registry magától **nem tárol alias-történetet**. A `registered_model_aliases` tábla csak a
jelenlegi állapotot ismeri (`champion → 2`), abból semmi sem utal arra, hogy a 4-es valaha
aktív volt. Az auditor csak a verzió-tagekből rakhatja össze:

- a 4-es verzión a `promoted_at = 2026-09-27T16:42:06+00:00` mutatja, mikor lett aktív;
- a `rolled_back_at = 2026-09-27T16:49:37+00:00`, a `rolled_back_to = 2` és a
  `rollback_reason` mutatja, mikor, mire és miért vették le.

Ha a `roll_back` nem írna tageket, csak a `promoted_at` maradna, vagyis az auditor annyit
látna, hogy a 4-es valamikor promotálva lett, de azt nem, hogy meddig volt aktív, és hogy
miért nem az már.

A saját registrym ennél jobban meg is mutatja a rést. A 3-as verzió 16:37:58-tól 16:42:06-ig
szintén champion volt, de mivel a 4-es promóciója nem írt semmit a 3-asra (a
`promote_to_staging` csak az új verziót tageli), erre ma **semmi sem utal közvetlenül**.
Csak abból lehetne kikövetkeztetni, hogy a 3-as és a 4-es `promoted_at` értéke 4 perc
különbséggel követi egymást. Egy valódi audit trailhez a promóciónak is tagelnie kellene az
általa leváltott verziót, vagy az alias-mozgatásokat egy külön eseménynaplóba kellene írni.

### 3. Biztonságos rollback-cél volt a 2-es verzió?

Nem igazán. A rollback utáni `make trace` 4. sora:

```text
4. Git commit:  2814c63  (tree state not recorded: nothing says this commit is the code that ran)
```

A 2-es verzió átment a `roll_back` ellenőrzésén, mert promotálva volt (`promoted_at`
létezik). Ez viszont csak azt jelenti, hogy valaki egyszer jóváhagyta, azt nem, hogy
visszakövethető. A forrás-runja a Exercise 6 Part 3 előtt futott, ezért nincs `git_dirty`
tagje, és ahogy a Exercise 6/2. válaszban kiderült, a `2814c63` commit nem is tartalmazta a
sweep-ciklust, amely ezt a runt létrehozta. Ha a 2-es is hibásnak bizonyulna, a hibát nem
lehetne visszakeresni a kódban.

A modell maga valószínűleg jó (ugyanazok a metrikái, mint a clean 4-esnek, és betölthető),
de "known-good" csak a tesztelt viselkedés szempontjából, a származás szempontjából nem.
A `roll_back` gate ugyanazt a hiányosságot mutatja, mint a `promote_to_staging` (Exercise
6/3): csak a `promoted_at` taget nézi, a `git_dirty`-t nem. Ugyanígy engedte volna a
rollbacket a 3-as verzióra is, amelyről a registry kifejezetten tudja, hogy dirty treeből
futott (`git_dirty = true`). Biztonságosabb gate-nek a `git_dirty = false` feltételt is
meg kellene követelnie, ez nálam csak a 4-esre teljesül, éppen arra, amelyről visszaálltunk.

## Stretch

A lekérdezések a `diabetes-week3` experiment összes runján futnak: 25 run, ebből három sweep
(a `2814c63`, az `af138ea` és az `ee794dc` commitból) a szülőikkel és gyerekeikkel, valamint
az egyedi `make run` futások.

### 1. Minden forest, amelynek a recallja 0.55 fölött van, ROC-AUC szerint csökkenő sorrendben

```bash
make query FILTER="params.model_family = 'rf' and metrics.recall > 0.55" ORDER_BY="metrics.roc_auc DESC"
```

Eredmény: 6 run, mind a három `rf-n_estimators=300` (recall 0.5821, ROC-AUC 0.8172) és mind
a három `rf-n_estimators=100` (recall 0.5522, ROC-AUC 0.8161). Minden konfiguráció három
sweepből jön vissza azonos metrikákkal, ami a fix seed miatti reprodukálhatóságot is mutatja.
Egyetlen logreg sincs benne: a legjobb logreg recallja is csak 0.5224.

### 2. Minden run, amely dirty working treeből futott

```bash
make query FILTER="tags.git_dirty = 'true'" ORDER_BY="attributes.start_time DESC"
```

Eredmény: 6 run, a `af138ea` commitos sweep gyerekei (ebből jött a dirty 3-as verzió),
mert a sweep előtt javítottam egy kommentet a `tests/test_tracking.py`-ban.

**Miért nem találhatja meg soha a Part 3 előtti runokat?** Mert azokon a `git_dirty` tag
egyáltalán **nem létezik**, nem `'false'`, hanem hiányzik. A `tags.git_dirty = 'true'`
szűrő csak olyan runokat ad vissza, amelyeken a tag létezik és az értéke `'true'`; a
hiányzó tag nem egyenlő semmivel. A 25 runból 6 dirty, 6 clean, 13 runon pedig nincs ilyen
tag, pedig ezek mind nem commitolt kódból futottak. Ezt az információt a futás pillanatában
kellett volna rögzíteni. Utólag nem lehet pótolni, mert a working tree akkori állapota már
nincs meg sehol. A lekérdezés nem tud olyan tényt megtalálni, amit sosem jegyeztünk fel.

### 3. Kézzel hozzáadott tag keresése

A UI-ban a `07851a8d48ee4a00921d1e4063538bb9` run (a clean 4-es verzió forrása) Overview
fülén a Tags résznél kézzel hozzáadtam a `reviewed = yes` taget, majd:

```bash
make query FILTER="tags.reviewed = 'yes'"
```

Eredmény: pontosan az az egy run jön vissza. A kézzel, a UI-ból felvett tag ugyanúgy
kereshető, mint a kódból logolt, mert mindkettő ugyanabba a Postgres táblába kerül. A tag
nem csak a pipeline-é: egy ember is utólag felcímkézhet egy runt (például átnézte,
kizárandó, bemutatóra szánt), és a címke onnantól szerver-oldali lekérdezéssel
visszakereshető.
