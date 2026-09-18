# DB Compare & Migration Generator

Tool untuk membandingkan struktur database SQL **Existing** dengan struktur database **Khanza**, kemudian menghasilkan file SQL migration berdasarkan perbedaan schema.

Tool ini awalnya dibuat sebagai CLI dan kemudian dikembangkan dengan GUI berbasis **PySide6**.

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
* Daftar conflict setelah migration selesai.
* Filter conflict berdasarkan:

  * Type
  * Decision
  * Nama tabel
* Detail perbedaan Existing dan Khanza.
* Tetap mendukung penggunaan melalui CLI.

---

## Requirements

* Python 3.10+
* PySide6 6.8+

Dependency Python tersedia di:

```text
requirements.txt
```

---

## Installation

Clone repository:

```bash
git clone <repository-url>
cd db-compare
```

Buat virtual environment:

```bash
python3 -m venv .venv
```

Aktifkan:

```bash
source .venv/bin/activate
```

Install dependency:

```bash
pip install -r requirements.txt
```

---

## Menjalankan GUI

Aktifkan virtual environment terlebih dahulu:

```bash
source .venv/bin/activate
```

Kemudian:

```bash
python run_gui.py
```

GUI menyediakan tiga bagian utama:

```text
Summary
Conflicts
Log
```

### Input

GUI menerima dua file schema SQL:

```text
Existing Schema
Khanza Schema
```

Kemudian tentukan file output:

```text
Output SQL
```

Opsional, migration dapat dibatasi menggunakan:

```text
Search
```

Contoh:

```text
lab
dokter
billing
```

---

# Conflict Resolution

Ketika ditemukan perbedaan schema antara Existing dan Khanza, tool akan membuat conflict.

Contoh:

```text
Conflict: column / dokter / nm_dokter
```

GUI menyediakan dua mode.

## Manual Decision

Setiap conflict akan ditampilkan dalam dialog:

```text
Existing:
...

Khanza:
...

[Keep Existing]
[Use Khanza]
[Skip]
```

Tersedia juga pilihan:

```text
Gunakan keputusan ini untuk semua
conflict pada tabel ini
```

Jika dipilih, conflict berikutnya pada tabel yang sama akan menggunakan keputusan tersebut secara otomatis.

---

## Use Khanza for All

Semua conflict otomatis menggunakan definisi Khanza.

Mode ini berguna ketika tujuan migration memang untuk menyamakan schema Existing dengan schema Khanza tanpa perlu melakukan keputusan satu per satu.

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

# CLI

Core generator tetap dapat digunakan tanpa GUI.

Contoh penggunaan melalui service:

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

Conflict callback dapat digunakan untuk menentukan keputusan secara manual.

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

# Struktur Project

```text
db-compare/
│
├── gui/
│   ├── app.py
│   ├── main_window.py
│   │
│   ├── widgets/
│   │   ├── conflict_dialog.py
│   │   ├── conflict_list.py
│   │   ├── conflict_mode_dialog.py
│   │   ├── file_selector.py
│   │   └── summary_widget.py
│   │
│   └── workers/
│       └── migration_worker.py
│
├── schema_generator/
│   ├── application/
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
├── requirements.txt
├── test_callback.py
└── README.md
```

## Architecture

Secara umum proses migration:

```text
Existing SQL
     │
     ▼
   Parser
     │
     ├──────────────┐
     │              │
     ▼              ▼
Existing Schema   Khanza Schema
     │              │
     └──────┬───────┘
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

Mengatur urutan `CREATE TABLE` berdasarkan dependency antar tabel.

### `writer.py`

Menghasilkan file SQL migration berdasarkan `MigrationPlan`.

### `migration_service.py`

Menjadi application layer yang mengorkestrasi:

```text
Parser
→ Planner
→ Conflict Resolver
→ Dependency Ordering
→ SQL Writer
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

Sebelum SQL ditulis, tabel baru akan diurutkan berdasarkan dependency.

---

# Catatan

Tool ini bekerja pada **struktur/schema database**, bukan melakukan migrasi data.

Sebelum menjalankan SQL migration pada database production:

1. Backup database.
2. Review file migration.
3. Periksa operasi `DROP`.
4. Periksa perubahan `MODIFY COLUMN`.
5. Periksa Foreign Key.
6. Jalankan pada database testing terlebih dahulu.

Generated SQL sebaiknya dianggap sebagai **migration proposal yang harus direview**, terutama jika terdapat operasi destructive.

---

# Development

Aktifkan environment:

```bash
source .venv/bin/activate
```

Jalankan GUI:

```bash
python run_gui.py
```

Untuk menguji conflict callback:

```bash
python test_callback.py
```

---

# License

Belum ditentukan.
