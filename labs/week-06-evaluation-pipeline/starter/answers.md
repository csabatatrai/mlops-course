# Week 6 — written answers

## Exercise 2

A `make slices` kimenete (192 tesztsor, 67 pozitív, 34.9% prevalencia):

```text
  aggregate      accuracy 0.7656  precision 0.6964  recall 0.5821  f1 0.6341  roc_auc 0.8345

  slice: age_band
  group                 n  pos     acc      f1  recall roc_auc     sel     fpr
  21-29                94   21  0.8511  0.6316  0.5714  0.8656  0.1809  0.0685
  30-39                48   22  0.6875  0.5946  0.5000  0.7832  0.3125  0.1538
  40-49                31   17  0.7419  0.7500  0.7059  0.8571  0.4839  0.2143
  50+                  19    7  0.5789  0.5000  0.5714  0.6071  0.4737  0.4167

  slice: bmi_band
  under_normal         30    1  0.9667  0.0000  0.0000  1.0000  0.0000  0.0000
  overweight           48    9  0.8125  0.4000  0.3333  0.7692  0.1250  0.0769
  obese               112   57  0.6964  0.6792  0.6316  0.7818  0.4375  0.2364
  missing               2    0  0.5000  0.0000  0.0000     —    0.5000  0.5000

  slice: insulin_missing
  insulin_present     104   42  0.7308  0.6111  0.5238  0.8041  0.2885  0.1290
  insulin_missing      88   25  0.8068  0.6667  0.6800  0.8775  0.2955  0.1429
```

### 1. The worst group, and how far to trust the gap

A modell az **`50+` korcsoporton** a leggyengébb: a ROC AUC **0.6071** az aggregált
**0.8345** helyett, ez **−0.227**. Az accuracy is itt a legrosszabb (0.5789 a 0.7656
helyett), és az F1 is (0.5000 a 0.6341 helyett). A legfeltűnőbb a téves riasztások
aránya: az `fpr` **0.4167**, a `21-29` csoport 0.0685-ével szemben ez körülbelül
**hatszoros**. Az idősebb, nem diabéteszes páciensek közel felét betegnek jósolja.

**A különbségben csak korlátozottan bízhatunk**, mert a csoport nagyon kicsi:

- `n = 19`, ebből 7 pozitív és 12 negatív. A ROC AUC mindössze 7 × 12 = 84
  pozitív–negatív párból áll, így egyetlen páciens átsorolása is több századot mozdít
  rajta. A 95%-os konfidenciaintervallum ekkora mintán nagyjából ±0.2–0.25 széles, vagyis
  összeér az aggregált értékkel.
- Az `fpr` 12 negatív páciensből jön: 0.4167 = 5/12. Egy-két páciensen múlik.
- A gyanút erősíti viszont, hogy az irány egyenletes. Az életkorral az `fpr`
  folyamatosan nő (0.0685 → 0.1538 → 0.2143 → 0.4167), és a ROC AUC a `40-49` kivételével
  csökken. Ez inkább valódi tendenciára utal, mint egyetlen kis csoport véletlenére.

Összegezve: a `50+` eredménye **figyelmeztető jel**, nem bizonyított hiba. Kiugrónak
tűnik, de 19 páciensből nem mérhető elég pontosan ahhoz, hogy erre alapozzunk döntést.

### 2. What to do now, and what is needed before acting

**Amit most megtehetünk:**

- Dokumentáljuk, és a modell kísérő leírásában (model card) feltüntetjük, hogy idősebb
  pácienseken kevésbé megbízható, és több a téves riasztás.
- A gate-be **support-szabályt** teszünk: egy ilyen kis csoportot a gate jelöljön
  `SKIPPED`-nek („túl kicsi a megítéléshez”), ne `pass`-nak, és ne is `fail`-nek. Így
  látszik, hogy ezt nem ellenőriztük, de egy zajos szám sem buktat el egy modellt.
  (Ez a 3. feladat `min_support` szabálya.)
- Szólunk az orvosi felhasználóknak: a `50+` csoportban egy pozitív jóslat kevesebbet
  ér, mert nagyobb a téves riasztás esélye.

**Amire szükség van, mielőtt beavatkozunk** (pl. külön küszöb vagy külön modell az
idősebbeknek, vagy több adat gyűjtése):

- **Több adat**: elsősorban több 50 év feletti páciens, hogy a mérés pontos legyen.
- **Megbízhatósági intervallum**: bootstrap-pal vagy keresztvalidációval meg kell nézni,
  hogy a különbség más train/test felosztáson is megmarad-e, vagy csak ennek a 19
  páciensnek a sajátja.
- **Orvosi szempont**: mennyibe kerül egy téves riasztás (felesleges vizsgálat), és
  mennyibe egy kihagyott beteg az idősebbeknél. Ettől függ, hogy a magas `fpr`
  egyáltalán gond-e.
- A beavatkozásnak egyeztetett, verziózott elfogadási kritériumot kell kapnia
  (`criteria_version` emelése), nem egyszeri kézi döntést.

### 3. F1 = 0.0000 and ROC AUC = 1.0000 on the same group

Ez a **`bmi_band` / `under_normal`** csoport: `n = 30`, ebből **1 pozitív**, és a
`sel` = 0.0000, vagyis a modell egyetlen pácienst sem jósolt betegnek.

Mindkét szám helyes, csak mást mér:

- **Az F1 a 0.5-ös küszöbön mér.** A modell senkit nem jósolt pozitívnak, így az egyetlen
  beteg páciens is kimaradt: TP = 0, a recall 0, a precision definiálatlan (a
  `zero_division=0` miatt 0). Ezért az F1 = 0.
- **A ROC AUC nem használ küszöböt, csak a rangsort nézi.** Az 1.0 azt jelenti, hogy az
  egyetlen beteg páciens nagyobb valószínűséget kapott, mint mind a 29 egészséges. A
  rangsor tehát tökéletes, csak a beteg valószínűsége is 0.5 alatt maradt.

**Mit mond ez a csoportról?** Gyakorlatilag semmi megbízhatót nem tudunk meg belőle. Az
F1 egyetlen páciensen múlik, a ROC AUC pedig mindössze 1 × 29 = 29 páron áll. A 3%-os
prevalencia azt mutatja, hogy normál BMI mellett ritka a diabétesz, a modell pedig ehhez
igazodva alacsony valószínűségeket ad. Ez akár jó viselkedés is lehet. Az egyetlen beteg
kihagyása viszont azt jelzi, hogy ebben a csoportban a 0.5-ös küszöb túl magas lehet. A
két szám együtt nem rossz modellt jelez, hanem túl kevés pozitív esetet: a csoportban a
**`pos`** (1) határozza meg, mennyit ér bármelyik metrika. Ezért a gate-nek a minimális
pozitív esetszámot is meg kell követelnie (`min_positives`), különben ilyen csoportokon
véletlen „pass” vagy „fail” születik. Hasonló a `missing` BMI-csoport (`n = 2`, 0
pozitív), ahol a ROC AUC nem is értelmezhető (—).

## Exercise 4

A `make gate-fail` (`train.C` 1.0 → 0.005) eredménye: az `evaluate` accuracy 0.7448,
precision 0.7500, recall 0.4030, **F1 0.5243**, **ROC AUC 0.8427** értéket írt ki, a
`gate` stage pedig leállította a `dvc repro`-t:

```text
NO-GO. 3 acceptance criteria failed: minimum.f1, regression.f1, slice.age_band.30-39.
```

A `models/model.pkl` a lemezen maradt, a `register` és a `promote` is ezt írta ki:
`The recorded verdict is NO-GO (criteria v1.0.0): ... Refusing to release.`
(A `fairness.age_band.tpr_gap` itt még nem szerepel, mert a fairness-szabályokat az
Exercise 5 adja hozzá.)

### 1. Why Week 5's trick cannot work here, and what replaces it

A Week 5-ös gate azért működött, mert **utána még jött egy stage**: a `prepare` dep-ként
olvasta a `reports/validation.json`-t, és a `_require_validated` a kódban is ellenőrizte.
A validáció az adatot ellenőrzi, és az adatra épül minden további lépés, így volt kit
megállítani.

A model gate a pipeline **végén** áll: a modell már elkészült és ki is értékeltük, mire a
gate dönt. A DVC-pipeline-ban nincs utána stage, amit dep-pel meg lehetne állítani. Ha
mégis lenne (pl. egy `register` stage `deps: reports/gate.json`-nel), az sem segítene:
egy dep csak azt nézi, hogy a fájl létezik-e és változott-e, azt nem, hogy GO vagy NO-GO
van-e benne. Ráadásul a release (registry, alias) nem DVC-lépés, hanem egy külön
`make register` / `make promote` parancs.

**Ami helyettesíti, két dolog:**

- A `gate` stage **nem nulla kóddal lép ki NO-GO esetén**. Így a `dvc repro` hibával
  áll le, és a pipeline futása látványosan piros.
- **A release-lépések maguk olvassák el a verdiktet.** A `register_best_model` és a
  `promote_to_staging` is meghívja a `require_go`-t, amely beolvassa a
  `reports/gate.json`-t, és `GateFailed`-et dob, ha az hiányzik vagy nem GO. A
  szabály tehát ott van, ahol a kár keletkezne.

### 2. What if `register` does not call `require_go`?

Akkor a gate csak **javaslat**, nem kapu. A `make register` (vagy egy kézi
`uv run python src/main.py register`) egy NO-GO modellt is gond nélkül regisztrálna új
verzióként, és a `promote` ugyanígy ráállíthatná a `staging` (rosszabb esetben a
`champion`) aliast. A pipeline piros volt, de a registryben minden zöldnek látszik.

**Ki venné észre, és mikor?** A gate-et futtató ember csak akkor, ha elolvassa a
kimenetet. Aki pénteken este beírja a `make register`-t, az nem látja. A registryben
nincs nyoma a NO-GO-nak, mert a `verdict` taget a `require_go` válasza tölti ki. A hibát
jó eséllyel csak az **éles használat** fedezné fel: amikor az orvosok azt jelzik, hogy a
modell több beteget hagy ki. A `C: 0.005` modell recallja 0.403, vagyis a diabéteszes
páciensek 60%-át kihagyná. Ha a modell lett a `champion`, a regressziós check onnantól
ehhez a rosszabb modellhez mérne, és a hiba „normálissá” válna.

### 3. F1 fell, ROC AUC rose: which one is right?

`C: 0.005`-nél az F1 **0.6341 → 0.5243** (−0.1098), a ROC AUC **0.8345 → 0.8427** (+0.0082).

Mindkét szám helyes, csak mást mér:

- A **ROC AUC** küszöbfüggetlen, a rangsort méri. Az erősen regularizált modell valamivel
  jobban rangsorol: a betegek átlagosan magasabb valószínűséget kapnak, mint az
  egészségesek.
- Az **F1** a 0.5-ös küszöbön kiadott döntéseket méri. A kis `C` a valószínűségeket a
  középérték felé húzza, így kevesebb páciens lépi át a 0.5-öt: a precision nő
  (0.6964 → 0.75), a recall viszont 0.5821 → **0.403**-ra esik.

**Melyik a „helyes” válasz, az a felhasználástól függ:**

- Ha a modell **döntést hoz** a 0.5-ös küszöbön (pl. „küldjük-e további vizsgálatra”),
  akkor az **F1** (és a recall) számít. Ekkor a `C: 0.005` modell rosszabb, mert sokkal
  több beteget hagy ki. Egy szűrőmodellnél a kihagyott beteg a drága hiba.
- Ha a modell **rangsorol** (pl. a legkockázatosabb 50 páciens behívása), vagy a küszöböt
  később kalibrálják, akkor a **ROC AUC** számít, és ez a modell egy kicsit jobb.

Ehhez tudni kell, hogy a modell kimenetét küszöbölt döntésként vagy rangsorként
használják-e, rögzített-e a 0.5-ös küszöb, és mennyibe kerül egy kihagyott beteg (FN)
egy téves riasztáshoz (FP) képest.

**Mit vállalunk az `acceptance.regression.primary_metric: f1` beállítással?** Előre és
írásban rögzítjük, hogy **a 0.5-ös küszöbön hozott döntések minősége** dönti el, jobb-e
egy modell a championnál. Egy modellt tehát akkor is elutasítunk, ha jobban rangsorol
(magasabb ROC AUC), de rosszabbul dönt. Ez a választás a csapat felelőssége, nem
egyetlen futás eredményéé. Ha a felhasználás rangsorolásra vált, a `primary_metric`-et
`roc_auc`-ra kell cserélni, és a `criteria_version`-t emelni kell. Utólag, egy kedvezőbb
metrika kedvéért nem szabad váltani. A `also_report: [accuracy, roc_auc]` miatt a ROC AUC
változása a gate kimenetében így is látszik, csak nem dönt.

## Exercise 5

A `make fairness` kimenete a két gate-elt tengelyen:

```text
  axis: age_band  [GATED]
  group                 n  pos  sel_rate     tpr     fpr
  21-29                94   21    0.1809  0.5714  0.0685
  30-39                48   22    0.3125  0.5000  0.1538
  40-49                31   17    0.4839  0.7059  0.2143
  50+                  19    7    0.4737  0.5714  0.4167
    demographic parity difference (selection-rate gap): 0.3030
    equal opportunity difference  (TPR gap)           : 0.2059
    equalized odds difference     (max of TPR/FPR gap): 0.3482

  axis: insulin_missing  [GATED]
  insulin_missing      88   25    0.2955  0.6800  0.1429
  insulin_present     104   42    0.2885  0.5238  0.1290
    demographic parity difference (selection-rate gap): 0.0070
    equal opportunity difference  (TPR gap)           : 0.1562
    equalized odds difference     (max of TPR/FPR gap): 0.1562
```

A gate eredménye: `GO — 13 passed, 0 failed, 4 SKIPPED (criteria v1.0.0)`. A három
fairness-check: `fairness.age_band.tpr_gap` 0.2059 (limit 0.25),
`fairness.insulin_missing.selection_rate_gap` 0.0070 (limit 0.10) és
`fairness.insulin_missing.tpr_gap` 0.1562 (limit 0.20).

### 1. Why the large selection-rate gap on `age_band` is defensible

A selection rate azt méri, hogy a modell a csoport hány százalékát jósolja betegnek. A
demographic parity azt követelné meg, hogy ez minden korcsoportban nagyjából egyforma
legyen. **A diabétesz gyakorisága azonban a korral valóban nő.** A tesztkészletben a
prevalencia:

| korcsoport | pos / n | prevalencia | selection rate |
|---|---|---|---|
| 21-29 | 21 / 94 | 22% | 0.18 |
| 30-39 | 22 / 48 | 46% | 0.31 |
| 40-49 | 17 / 31 | 55% | 0.48 |
| 50+ | 7 / 19 | 37% | 0.47 |

A selection rate nagyjából a valódi prevalenciát követi. Egy jó diagnosztikai modellnek
**több** idősebb pácienst kell betegnek jósolnia, mert közöttük több a beteg. Ha a
selection rate-et kiegyenlítenénk, vagy sok idősebb beteget kellene kihagyni, vagy sok
fiatal egészséges pácienst tévesen riasztani. Az életkor itt legitim orvosi
kockázati tényező, nem olyan védett tulajdonság, amely alapján az eltérő bánásmód
diszkrimináció lenne.

Ami viszont számít: **ugyanakkora eséllyel találjuk-e meg a betegeket minden
korcsoportban**. Ezt az equal opportunity (TPR-különbség) méri, ezért ezt gate-eljük. A
selection rate-et csak riportoljuk.

### 2. Why the TPR limit on `age_band` is looser, and what would tighten it

Az `age_band` limitje 0.25, az `insulin_missing`-é 0.20. A különbség oka a
**csoportméret**. A TPR a csoport pozitív eseteiből számolódik:

- Az `insulin_missing` két csoportjában 42 és 25 pozitív van, így egy páciens
  0.02–0.04-gyel mozdítja a TPR-t. Itt egy szoros limit valódi különbséget mér, nem zajt.
- Az `age_band`-ben a csoportok 22, 21, 17 és 7 pozitívot tartalmaznak. A `50+` csoportban
  egyetlen páciens **0.14**-gyel, a `40-49`-ben 0.06-tal mozdítja a TPR-t. A mért 0.2059
  (0.7059 − 0.5000) néhány páciensen múlik. Egy 0.20-as limit ezért gyakran zajra
  buktatna el modelleket.

**Mi indokolná a szigorítást?**

- **Több adat**, főleg a 40 év felettiekből, hogy a TPR-ek pontosabbak legyenek.
- Ha a különbség **tartósan ugyanabba az irányba mutat** több újratanításon és több
  train/test felosztáson. Akkor nem zaj, hanem valódi egyenlőtlenség.
- **Orvosi vagy jogi követelmény**, hogy egyetlen korcsoportban se hagyjunk ki
  aránytalanul sok beteget (pl. az idősebbeknél a kihagyott diabétesznek súlyosabbak a
  következményei).

A szigorítás után a `criteria_version`-t emelni kell.

### 3. A group we cannot audit

A modellt a páciensek **neme** szerint szeretném auditálni, de nem tudom. Az adatkészlet
minden páciense nő, ráadásul Pima származású és legalább 21 éves. A modellnek így
semmilyen mérése nincs férfiakra, más etnikumokra vagy fiatalabbakra, és az ő
csoportjaikon a teljesítménye ismeretlen. Ugyanez igaz a **jövedelemre / biztosítási
státuszra** és a **klinikára / kórházra** is: egyik oszlop sincs meg az adatban.

**Minek kellett volna történnie, és mikor?** Ezeket az attribútumokat **az adatgyűjtéskor**
kellett volna rögzíteni, a vizsgálat megtervezésekor: a beleegyező nyilatkozatban, a
gyűjtési protokollban és az adatszerződésben (a mi esetünkben a `RawMeasurements`
sémában). Utólag nem pótolható. Egy fairness-audit nem tud olyan csoportot vizsgálni,
amelyet senki nem rögzített. Ha a modellt más populáción akarnánk használni (pl. férfiakon
vagy egy másik klinikán), előbb onnan kellene adatot gyűjteni ezekkel az oszlopokkal, és
újra kiértékelni. Az érzékeny attribútumok gyűjtéséhez adatvédelmi (GDPR) jogalap és
etikai engedély is kell, ezért ezt a döntést nem az ML-csapat egyedül hozza meg.
