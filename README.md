# Library Desk

A small local lending dashboard for books, members, due dates and active loans. Built as a learning project with OpenAI Codex assistance.

## Run

Requires Python 3.10+. Run `python server.py --db library.sqlite3` and open the printed localhost URL. Run `python -m unittest discover -s tests -v` for domain tests.

Add a book and member, then record a loan and return it. Available copies are checked in a SQLite write transaction. A loan is marked overdue when its due date is earlier than the server's local date.

## Limits

Development server listens on 127.0.0.1 and has no authentication, authorization, HTTPS, CSRF protection, backup, or encryption. Do not expose it on a network or use real personal data. It is not production software. All loans are for one copy and dates are supplied by the operator. No edit/delete, search, fine calculation, deployment, or independent security audit is provided.

## Bahasa Indonesia

Dasbor peminjaman lokal untuk mencatat buku, anggota, tenggat dan pengembalian. Gunakan data contoh; server belum aman untuk dipublikasikan.
