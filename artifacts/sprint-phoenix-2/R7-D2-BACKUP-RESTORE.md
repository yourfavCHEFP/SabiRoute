# R7 D2 — BACKUP/RESTORE ITEMS

**Authority:** Row D, Tranche D2. **Status:** WRITTEN · NOT RUN.

## Files

- `R7-D2-backup_restore.sh` — `backup` / `restore` using `pg_dump` and `pg_restore`.
- `R7-D2-check_backup_restore.py` — local-only check: backs up, creates a post-backup sentinel
  table, restores, and asserts the sentinel is gone.

## Hard boundary

The check refuses any `PGHOST` that is not `localhost`, `127.0.0.1` or `::1`. No managed service,
production database, credential, workflow run or network push is authorised. The script was not
executed to produce this record.

## Test design

1. Create a disposable local database.
2. Create `restore_probe` with a sentinel row.
3. Run the backup action.
4. Drop `restore_probe` to simulate loss.
5. Run the restore action.
6. Assert the sentinel row is recovered.

The first draft of the check asserted that a table created *after* backup would be removed by
`pg_restore --clean`. That was wrong: `--clean` only drops objects present in the archive. The
check now proves restoration of pre-backup state instead.

## Verdict

`D2: ARTIFACTS WRITTEN · LOCAL CHECK NOT EXECUTED`
