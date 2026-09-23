# Khanza Schema Migrator

**Khanza Schema Migrator** adalah tool untuk membandingkan struktur database SQL **Existing** dengan struktur database **Khanza**, kemudian menghasilkan file SQL migration berdasarkan perbedaan schema.

Tool ini dirancang untuk membantu proses sinkronisasi schema database Khanza yang telah memiliki modifikasi/custom dengan schema Khanza versi lain.

Aplikasi tersedia dalam bentuk **standalone application** untuk Linux, Windows, dan macOS, sehingga pengguna akhir tidak perlu menginstall Python atau dependency tambahan.

Untuk kebutuhan development, core generator juga dapat digunakan langsung melalui Python dan CLI.

---

## Fitur

* Membandingkan struktur tabel Existing dan Khanza.
* Mendeteksi:

  * Table baru
  * Column baru
  * Column yang berubah
  * Column yang dihapus
  * Index
  * Primary Key
  * Foreign Key
* Menghasilkan SQL migration secara otomatis.
* Menangani dependency antar tabel.
* Mendeteksi dependency cycle.
* Conflict resolution:

  * Keep Existing
  * Use Khanza
  * Skip
* Mode conflict:

  * **Manual Decision**
  * **Use Khanza for All**
* Remember decision untuk seluruh conflict pada tabel tertentu.
* GUI berbasis PySide6.
* Summary hasil migration.
* Daftar conflict setelah migration selesai.
* Filter conflict berdasarkan:

  * Type
  * Decision
  * Nama tabel
* Detail perbedaan antara Existing dan Khanza.
* Core generator tetap dapat digunakan melalui Python tanpa GUI.

---

# Download

Untuk pengguna umum, **tidak perlu menginstall Python, pip, PySide6, atau dependency lainnya**.

Gunakan package sesuai sistem operasi:

| Platform            | Package                                                                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linux x64           | [KhanzaSchemaMigrator-linux-x64.tar.gz](https://github.com/ThoriqFathu/khanza-schema-migrator/releases/download/v1.0.0/KhanzaSchemaMigrator-linux-x64.tar.gz) |
| Windows x64         | [KhanzaSchemaMigrator-windows-x64.zip](https://github.com/ThoriqFathu/khanza-schema-migrator/releases/download/v1.0.0/KhanzaSchemaMigrator-windows-x64.zip)   |
| macOS Apple Silicon | [KhanzaSchemaMigrator-macos-arm64.zip](https://github.com/ThoriqFathu/khanza-schema-migrator/releases/download/v1.0.0/KhanzaSchemaMigrator-macos-arm64.zip)   |

Setelah package didownload, extract terlebih dahulu.


### Linux

Extract archive kemudian jalankan:

```bash
./KhanzaSchemaMigrator
```

### Windows

Extract ZIP kemudian jalankan:

```text
KhanzaSchemaMigrator.exe
```

### macOS

Extract ZIP kemudian buka:

```text
KhanzaSchemaMigrator.app
```

> Build macOS pada release ini ditujukan untuk **Apple Silicon (ARM64)**.

---

# Menjalankan GUI

GUI menyediakan tiga bagian utama:

```text
Summary
Conflicts
Log
```

## Input

GUI menerima dua file schema SQL:

```text
Existing Schema
Khanza Schema
```

Kemudian tentukan file output:

```text
Output SQL
```

Migration dapat dibatasi menggunakan field:

```text
Search
```

Contoh:

```text
lab
dokter
billing
```

Jika Search diisi, proses schema dapat difokuskan pada objek yang relevan dengan pencarian tersebut.

---

# Conflict Resolution

Ketika ditemukan perbedaan schema antara Existing dan Khanza, tool akan membuat conflict.

Contoh:

```text
Conflict: column / dokter / nm_dokter
```

Conflict dapat diselesaikan menggunakan dua mode.

## Manual Decision

Pada mode manual, setiap conflict akan ditampilkan dalam dialog:

```text
Existing:

...

Khanza:

...

[Keep Existing]

[Use Khanza]

[Skip]
```

Tersedia juga pilihan untuk mengingat keputusan:

```text
Gunakan keputusan ini untuk semua
conflict pada tabel ini
```

Jika dipilih, conflict berikutnya pada tabel yang sama akan menggunakan keputusan tersebut secara otomatis.

### Jenis keputusan

```text
E = Keep Existing
K = Use Khanza
S = Skip
```

---

## Use Khanza for All

Pada mode ini, semua conflict secara otomatis menggunakan definisi Khanza.

Mode ini berguna ketika tujuan migration adalah menyelaraskan schema Existing dengan schema Khanza tanpa menentukan keputusan satu per satu.

Tetap lakukan review terhadap migration SQL sebelum menjalankannya pada database.

---

# Hasil Migration

Setelah proses selesai, GUI menampilkan Summary.

Contoh:

```text
Existing tables       : 1185
Khanza tables         : 1182

CREATE TABLE          : 87
DROP FOREIGN KEY      : 9
DROP COLUMN           : 17
ADD COLUMN            : 145
MODIFY COLUMN         : 146
DROP INDEX            : 0
ADD / REPLACE INDEX   : 27
ADD FOREIGN KEY       : 162

CONFLICTS             : 163
KEPT                  : 1095
```

File migration SQL akan ditulis ke lokasi output yang dipilih.

---

# Conflict List

Setelah migration selesai, seluruh conflict dapat dilihat melalui tab:

```text
Conflicts
```

Contoh:

```text
Type          Table                         Name          Decision
------------------------------------------------------------------
column        audit_bundle_iadp             apd           K
column        dokter                         nm_dokter     K
foreign key   toko_surat_pemesanan           ...ibfk_2     K
column        audit_sterilisasi_alat         audit1        E
```

Conflict dapat difilter berdasarkan:

```text
Type
Decision
Table
```

Detail conflict juga dapat dilihat dengan memilih row:

```text
Existing:

<schema Existing>

Khanza:

<schema Khanza>
```

---

# CLI / Python API

Core generator tetap dapat digunakan tanpa GUI.

Contoh penggunaan melalui `MigrationService`:

```python
from schema_generator.application.migration_service import (
    MigrationService,
)

service = MigrationService()

result = service.generate(
    existing_file="existing.sql",
    khanza_file="khanza.sql",
    output_file="migration.sql",
)
```

Conflict callback dapat digunakan untuk menentukan keputusan secara programmatic.

Contoh:

```python
from schema_generator.conflict import (
    ConflictDecision,
)


def conflict_handler(
    object_type,
    table,
    name,
    existing,
    khanza,
):
    return ConflictDecision(
        decision="K",
        remember_for_table=False,
    )
```

Kemudian:

```python
result = service.generate(
    existing_file="existing.sql",
    khanza_file="khanza.sql",
    output_file="migration.sql",
    conflict_callback=conflict_handler,
)
```

---

# Development

Bagian ini hanya diperlukan jika ingin menjalankan atau mengembangkan source code.

## Requirements

* Python 3.10+
* PySide6 6.8+

Dependency Python tersedia di:

```text
requirements.txt
requirements-dev.txt
```

`requirements-dev.txt` juga menyediakan dependency untuk proses build aplikasi menggunakan PyInstaller.

## Installation

Clone repository:

```bash
git clone https://github.com/ThoriqFathu/khanza-schema-migrator.git

cd khanza-schema-migrator
```

Buat virtual environment:

```bash
python3 -m venv .venv
```

Aktifkan.

### Linux dan macOS

```bash
source .venv/bin/activate
```

### Windows

```cmd
.venv\Scripts\activate
```

Install dependency:

```bash
python -m pip install -r requirements-dev.txt
```

---

## Menjalankan Source Code

Jalankan GUI:

```bash
python run_gui.py
```

Untuk menguji conflict callback:

```bash
python test_callback.py
```

---

# Build Application

Aplikasi standalone dibangun menggunakan **PyInstaller**.

Build menggunakan file:

```text
KhanzaSchemaMigrator.spec
```

Perintah:

```bash
pyinstaller KhanzaSchemaMigrator.spec
```

Hasil build berada di:

```text
dist/
```

Build harus dilakukan pada sistem operasi target masing-masing.

Contoh:

```text
Linux   → build Linux
Windows → build Windows
macOS   → build macOS
```

---

# Struktur Project

```text
khanza-schema-migrator/

├── gui/
│   ├── __init__.py
│   ├── app.py
│   ├── main_window.py
│   │
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── conflict_dialog.py
│   │   ├── conflict_list.py
│   │   ├── conflict_mode_dialog.py
│   │   ├── file_selector.py
│   │   └── summary_widget.py
│   │
│   └── workers/
│       ├── __init__.py
│       └── migration_worker.py
│
├── schema_generator/
│   ├── __init__.py
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   └── migration_service.py
│   │
│   ├── conflict.py
│   ├── dependency.py
│   ├── models.py
│   ├── parser.py
│   ├── planner.py
│   ├── sql.py
│   ├── summary.py
│   └── writer.py
│
├── run_gui.py
├── schema_generator.py
├── requirements.txt
├── requirements-dev.txt
├── KhanzaSchemaMigrator.spec
├── test_callback.py
└── README.md
```

---

# Architecture

Secara umum proses migration:

```text
Existing SQL
     │
     ▼
   Parser
     │
     ├──────────────────┐
     │                  │
     ▼                  ▼
Existing Schema     Khanza Schema
     │                  │
     └────────┬─────────┘
              ▼
          Planner
              │
              ▼
      Conflict Resolver
              │
              ▼
        Migration Plan
              │
              ▼
      Dependency Order
              │
              ▼
          SQL Writer
              │
              ▼
        migration.sql
```

GUI berada di atas core generator dan tidak menangani proses perbandingan schema secara langsung.

```text
PySide6 GUI
     │
     ▼
MigrationService
     │
     ▼
Schema Generator
```

Dengan struktur tersebut, core generator tetap dapat digunakan tanpa GUI.

---

# Modul Utama

### `parser.py`

Membaca file SQL dan mengubah definisi database menjadi model schema internal.

### `planner.py`

Membandingkan Existing schema dengan Khanza schema dan menghasilkan `MigrationPlan`.

### `conflict.py`

Menangani perbedaan schema yang membutuhkan keputusan:

```text
E = Keep Existing
K = Use Khanza
S = Skip
```

### `dependency.py`

Mengatur urutan `CREATE TABLE` berdasarkan dependency antar tabel dan mendeteksi dependency cycle.

### `writer.py`

Menghasilkan file SQL migration berdasarkan `MigrationPlan`.

### `migration_service.py`

Menjadi application layer yang mengorkestrasi:

```text
Parser
  ↓
Planner
  ↓
Conflict Resolver
  ↓
Dependency Ordering
  ↓
SQL Writer
```

---

# Migration Plan

Migration plan dapat berisi operasi:

```text
CREATE TABLE

DROP FOREIGN KEY

ADD COLUMN
DROP COLUMN
MODIFY COLUMN

DROP INDEX
ADD INDEX
REPLACE INDEX

ADD FOREIGN KEY
```

Sebelum SQL ditulis, tabel baru akan diurutkan berdasarkan dependency antar tabel.

Jika ditemukan dependency cycle, informasi cycle akan dilaporkan oleh proses migration sehingga dapat ditinjau sebelum SQL dijalankan.

---

# Catatan Penting

Tool ini bekerja pada **struktur/schema database**, bukan melakukan migrasi data.

File SQL yang dihasilkan merupakan **migration proposal** berdasarkan perbedaan antara Existing Schema dan Khanza Schema.

Sebelum menjalankan SQL migration pada database production:

1. Backup database.
2. Review file migration.
3. Periksa operasi `DROP`.
4. Periksa perubahan `MODIFY COLUMN`.
5. Periksa Primary Key dan Index.
6. Periksa Foreign Key.
7. Jalankan dan validasi pada database testing terlebih dahulu.

Khususnya untuk operasi destructive seperti:

```text
DROP COLUMN
DROP FOREIGN KEY
DROP INDEX
MODIFY COLUMN
```

hasil migration harus direview terlebih dahulu.

Tool tidak menjamin bahwa generated SQL dapat langsung diterapkan pada seluruh kondisi database tanpa pemeriksaan.

---

# Release

Release aplikasi menggunakan versioning:

```text
v1.0.0
v1.0.1
v1.1.0
...
```

Artifact release disediakan berdasarkan sistem operasi:

```text
KhanzaSchemaMigrator-linux-x64.tar.gz
KhanzaSchemaMigrator-windows-x64.zip
KhanzaSchemaMigrator-macos-arm64.zip
```

Source code dan release artifact dipisahkan. Artifact hasil build tidak disimpan sebagai bagian dari source repository.

---
## Pengembangan

Source code tersedia secara terbuka agar dapat digunakan, dipelajari, dan dikembangkan lebih lanjut oleh komunitas sesuai ketentuan lisensi project.

Untuk saat ini, pengembangan fitur dan pemeliharaan project dilakukan oleh pengembang utama. Mekanisme kontribusi dari komunitas dapat ditambahkan pada tahap berikutnya apabila diperlukan.

## Lisensi

Khanza Schema Migrator merupakan perangkat lunak open source dan dirilis menggunakan **MIT License**.

Lisensi ini memungkinkan penggunaan, modifikasi, dan distribusi ulang aplikasi sesuai dengan ketentuan yang tercantum pada file [LICENSE](LICENSE).



## Structure Builder

Aplikasi yang sama menyediakan tab **Schema Migration** dan **Structure Builder**.
Entry point tetap `run_gui.py` dan executable tetap `KhanzaSchemaMigrator`.

- **Database**: isi Host, Port, Database, Username, Password; jalankan **Test Connection**,
  tentukan output, lalu **Build Structure**.
- **Structure SQL**: pilih input dan output, lalu **Validate**. Jika path sama, file hanya
  divalidasi; jika berbeda, bytes disalin tanpa rewrite formatting.
- **Full SQL Backup**: **Analyze** menghitung tabel dan statement yang akan dibuang;
  **Extract Structure** menulis hasil ke output yang berbeda dari backup sumber.
- Setelah sukses, **Use as Existing Schema** atau **Use as Khanza Schema** mengisi input
  migration dan membuka tab tersebut. Proses migration tetap dimulai oleh pengguna.

Hasil menampilkan jumlah CREATE TABLE, ukuran file, SHA256, serta jumlah statement yang
  dibuang. Output dipublikasikan dengan atomic replace setelah staging lolos validasi.
  Kegagalan tidak mengganti output lama. Operasi berjalan di QThread; aplikasi menunggu
  operasi selesai sebelum mengizinkan window ditutup.

### Client database

Mode file tidak memerlukan dependency baru. Mode Database memerlukan client tools
MySQL/MariaDB yang dipasang terpisah, termasuk pada versi executable:

- Dump: `mysqldump` atau `mariadb-dump`.
- Test koneksi: `mysql` atau `mariadb`.

Client ditemukan lewat PATH, atau dipilih lewat field executable opsional. Gunakan client
sesuai keluarga/versi server. Client eksternal tidak dibundel oleh PyInstaller.
Test koneksi menjalankan `SELECT 1`; dump memakai `--no-data --routines --triggers --events
--skip-lock-tables --no-tablespaces`. Tidak ada import SQL maupun perubahan schema/data pada
server sumber. Gunakan akun dengan izin membaca metadata yang diperlukan untuk objek dump.

Password tidak masuk argumen proses, log, atau pesan error. Adapter membuat option file
sementara melalui `--defaults-file` (opsi pertama), lalu menghapusnya setelah client selesai.
File memakai mode 0600 pada POSIX; Windows mengikuti ACL direktori temporary pengguna.
Trade-off: credential berada sebentar di disk dan dapat tertinggal bila proses/OS berhenti
paksa. Password tidak disimpan dalam konfigurasi aplikasi. Stderr client sengaja tidak
ditampilkan karena berpotensi memuat credential; GUI memberi petunjuk pemeriksaan koneksi,
izin, dan kecocokan versi. Timeout test 20 detik dan dump 1 jam.

Referensi opsi: [MySQL mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
dan [MariaDB mariadb-dump](https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump).

### Batas format SQL

Scanner memproses bytes secara streaming, dengan statement di atas 1 MiB dialihkan ke
file temporary. Ruang temporary perlu cukup untuk statement INSERT terbesar. Scanner
mengenali strings/quoted identifiers, escapes, comments, executable version comments,
dan `DELIMITER`. CREATE/ALTER/DROP objek schema serta SET/USE dipertahankan; statement lain
(termasuk top-level INSERT/REPLACE/UPDATE/DELETE/LOAD dan LOCK/UNLOCK) dibuang saat ekstraksi.
SQL di dalam definisi trigger/procedure/function/event tetap dipertahankan karena bagian DDL.
Analysis melaporkan jumlah statement yang dibuang, bukan jumlah baris data.

Validasi bersifat dasar: input terbaca, statement terminated, quote/comment tertutup,
CREATE TABLE ditemukan, dan tidak ada top-level statement data. Ini bukan parser syntax SQL
lengkap. Dump terpotong dan mode `NO_BACKSLASH_ESCAPES` ditolak dengan pesan error.
Input diharapkan dump MySQL/MariaDB dengan terminator statement, bukan format backup biner.

Parser migration existing tetap tidak diubah: ia membaca CREATE TABLE multiline dengan
identifier backtick serta kolom/index/FK inline. Definisi VIEW/routine dan ALTER TABLE
terpisah dipertahankan dalam structure.sql tetapi belum dibandingkan oleh migration.
Validasi structure tidak menjamin semua variasi SQL dapat dikonsumsi parser migration.

### Modul dan test

Core Qt-independent ada di `structure_builder/models.py`, `service.py`, `sql_dump.py`,
dan `database.py`. `DatabaseProvider` dapat diganti fake tanpa database nyata.
Presentation ada di `gui/widgets/structure_builder_tab.py` dan worker di
`gui/workers/structure_worker.py`; composition/navigation ada di `gui/main_window.py`.

```bash
mkdir -p structure_builder tests
python -m unittest discover -s tests -v
pyinstaller KhanzaSchemaMigrator.spec
```

Test menggunakan unittest standard library; UI test menggunakan Qt offscreen. Cakupan
termasuk validasi, ekstraksi statement besar, DELIMITER/routines, keamanan credential,
output atomik, regresi MigrationService, worker error, serta kedua tombol handoff.
`test_callback.py` existing tetap merupakan contoh/test manual interaktif.
Modul baru di-import secara statis sehingga spec existing tetap dapat digunakan.
Pengujian koneksi database nyata dan build Windows/macOS perlu dilakukan pada environment target.


### Live Activity Log

Tab Structure Builder memakai area hasil existing sebagai **Activity Log** read-only.
Setiap operasi membersihkan log sebelumnya, menampilkan Starting, dan menonaktifkan
form sampai worker selesai. Pesan bertimestamp lokal `[HH:mm:ss]` ditambahkan langsung
melalui signal Qt dan auto-scroll; log tetap tersedia sesudah success/error. Maksimal
5.000 baris terbaru dipertahankan untuk membatasi memory UI.

Callback progress tersedia pada `StructureService.build`, `validate`, `analyze`,
`test_connection`, serta port `DatabaseProvider`. Semua callback opsional dan core tetap
independen dari Qt. `ProgressReader` membungkus pembacaan file tanpa mengubah parser atau
bytes output: progress byte dibatasi sekali per detik, ditambah laporan akhir. Hashing
dan copying juga melaporkan byte; jumlah statement yang dibuang dirangkum di akhir.

Adapter database menggunakan `Popen.wait` dalam worker yang sama, tanpa thread tambahan.
Setiap dua detik ia melaporkan bahwa client masih berjalan dan ukuran output yang sudah
teramati. Ini bukan progress per-table atau estimasi persentase database. Test koneksi
adalah action tersendiri; Build tidak menambahkan koneksi test terpisah. Stderr tidak
ditampilkan dan keberhasilan ditentukan oleh return code. Argumen command, environment,
credential file sementara, dan password tidak dimasukkan ke log. Worker dan presentation
juga menyamarkan password pada pesan progress/error. Error file credential sementara
diubah menjadi pesan aman tanpa path sensitif.

Test live logging ada di `tests/test_activity_log.py`, termasuk pesan sebelum completion,
throttling, auto-scroll, redaction, subprocess heartbeat/timeout, dan stderr sukses.
