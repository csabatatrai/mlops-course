# Answers

## Exercise 4

- Ellenőrzés a MinIO oldalán (`mc ls --recursive minio/mlflow-artifacts`):

```
[2026-09-21 01:00:04 UTC]   683B STANDARD 1/models/m-3e619e6abf4146a9a56b8c1ac661393b/artifacts/MLmodel
[2026-09-21 01:00:04 UTC] 2.6KiB STANDARD 1/models/m-3e619e6abf4146a9a56b8c1ac661393b/artifacts/conda.yaml
[2026-09-21 01:00:04 UTC] 1.5KiB STANDARD 1/models/m-3e619e6abf4146a9a56b8c1ac661393b/artifacts/model.pkl
[2026-09-21 01:00:03 UTC]    98B STANDARD 1/models/m-3e619e6abf4146a9a56b8c1ac661393b/artifacts/python_env.yaml
[2026-09-21 01:00:03 UTC] 2.1KiB STANDARD 1/models/m-3e619e6abf4146a9a56b8c1ac661393b/artifacts/requirements.txt
```

- Ellenőrzés a Postgres oldalán (`SELECT run_uuid, status, start_time FROM runs LIMIT 5;`):

```
             run_uuid             |  status  |  start_time
----------------------------------+----------+---------------
 5a5510d5a53445cfaadf9cd78fd4d96a | FINISHED | 1789952401813
 6c87c24bee374bdba8b9a6737ee71553 | FINISHED | 1789952641333
```

**Melyik storage plane melyik adatot tárolja, és miért nincsenek a modellfájlok a Postgres-ben?**

A Postgres a strukturált, kis méretű, gyakran lekérdezett metaadatot tárolja: run azonosítók, paraméterek, metrikák, tag-ek (a `runs`, `params`, `metrics`, `tags` táblák). Ezekre gyors, indexelt keresést és szűrést akarunk tudni futtatni — pl. "melyik run-nak volt 0.7-nél nagyobb az accuracy-ja" —, ami pontosan egy relációs adatbázis erőssége.

A MinIO ezzel szemben nagy, bináris, strukturálatlan blobokat tárol — itt a betanított `model.pkl`-t és a hozzá tartozó metafájlokat (`MLmodel`, `conda.yaml`, `requirements.txt`). Ezeket sosem kérdezzük le SQL-lel, csak egészben töltjük fel/le. Elméletileg a Postgres is el tudna tárolni bináris adatot (pl. `BYTEA` oszlopként), de ez rossz döntés lenne: feleslegesen felduzzasztaná az adatbázis méretét és a mentéseit, lassítaná a metaadat-lekérdezéseket, és a DB nincs is optimalizálva nagy fájlok hatékony, streamelt ki-beolvasására — egy objektumtár (MinIO/S3) pont erre a feladatra lett tervezve: HTTP-alapú, horizontálisan skálázható, olcsó tárolás nagy, ritkán módosuló fájlokhoz.

## Exercise 5

- Ugyanazzal a seed=42-vel háromszor lefuttatva a pipeline-t (`uv run python src/main.py`), majd `PIPELINE_RANDOM_SEED=7`-re állítva és még egyszer lefuttatva, az MLflow-ban lekérdezett run-ok:

```
seed= 42  accuracy=0.7344  f1=0.5785  run_id=5a5510d5
seed= 42  accuracy=0.7344  f1=0.5785  run_id=6c87c24b
seed= 42  accuracy=0.7344  f1=0.5785  run_id=a1b1196c
seed=  7  accuracy=0.7812  f1=0.6500  run_id=5f58238a
```

A három seed=42-es run metrikái bit-pontosan megegyeznek, a seed=7-es run pedig eltér — pontosan úgy, ahogy a 1. heti kísérletben is (ott is 0.7344/0.5785 vs. 0.7812/0.65 volt a két seed eredménye).

**Mit tudok most megválaszolni, amit 1. heti labor után nem tudtam?**

Első heti laborban a futás eredménye csak a terminál kimenetében élt: ha másnap megkérdezik, "mi volt a pontos accuracy a 42-es seed-del futtatott modellnek", csak akkor tudom megválaszolni, ha véletlenül elmentettem/lecsőztem a terminál kimenetét, és akkor sem tudom bizonyítani, hogy pontosan melyik kóddal/adattal futott. Ha két futtatás más eredményt adott, nem volt semmi, ami megmondja, hogy tényleg más seed miatt, vagy mert időközben módosítottam valamit a kódban vagy az adatban.

Most, hogy a run-ok az MLflow-ban központilag, a Postgres-ben rögzítve vannak:

- **Reprodukálhatóság:** minden run mellé el van tárolva a pontos paraméterezés (`random_seed`, `test_size`, `max_iter`), tehát bármikor visszakereshető, hogy egy adott metrika-érték pontosan milyen beállítással jött ki — nem kell megbíznom a memóriámban vagy egy elgépelt jegyzetben.
- **Megoszthatóság:** a `MLFLOW_TRACKING_URI`-t ismerő bárki (csapattárs, lab leader) megnyithatja ugyanazt a run-t a böngészőjében, konkrét run ID-val hivatkozva rá — nem kell a terminál-kimenetemet másolgatnom neki.
- **Összehasonlíthatóság:** az MLflow UI-ban a run-ok egymás mellé rendezve, oszloponként összehasonlíthatók (pl. seed=42 vs. seed=7 metrikái), és az is látszik, hogy a három seed=42-es run azonos eredményt adott — ami direkt bizonyíték arra, hogy a pipeline determinisztikus, és a különbség tényleg a seed-től jön, nem valamilyen rejtett véletlenszerűségtől vagy kódváltozástól.
