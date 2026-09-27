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
