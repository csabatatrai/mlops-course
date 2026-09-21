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
