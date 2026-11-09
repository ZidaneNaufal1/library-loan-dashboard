"""Local SQLite lending rules; callers provide the database path."""
import datetime as dt
import sqlite3
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, total INTEGER NOT NULL CHECK(total > 0));
CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL REFERENCES books(id), member_id INTEGER NOT NULL REFERENCES members(id), due TEXT NOT NULL, returned INTEGER NOT NULL DEFAULT 0 CHECK(returned IN (0,1)));
CREATE UNIQUE INDEX IF NOT EXISTS active_loan ON loans(book_id, member_id) WHERE returned=0;
"""

def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.execute("PRAGMA foreign_keys=ON")
    return db

def initialize(path):
    with closing(connect(path)) as db, db:
        db.executescript(SCHEMA)

def name(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise ValueError("Name must be 1–160 characters")
    return value.strip()

def date(value):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        result = dt.date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError()
        return value
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD") from None

def add_book(path, title, total):
    if isinstance(total, bool) or not isinstance(total, int) or not 1 <= total <= 10000:
        raise ValueError("Copies must be an integer from 1 to 10000")
    with closing(connect(path)) as db, db:
        return db.execute("INSERT INTO books(title,total) VALUES (?,?)", (name(title),total)).lastrowid

def add_member(path, member):
    with closing(connect(path)) as db, db:
        return db.execute("INSERT INTO members(name) VALUES (?)", (name(member),)).lastrowid

def borrow(path, book_id, member_id, due):
    if any(isinstance(x,bool) or not isinstance(x,int) or x<1 for x in (book_id,member_id)):
        raise ValueError("Invalid IDs")
    due = date(due)
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        book = db.execute("SELECT total FROM books WHERE id=?", (book_id,)).fetchone()
        if not book or not db.execute("SELECT 1 FROM members WHERE id=?", (member_id,)).fetchone():
            raise ValueError("Book or member not found")
        active = db.execute("SELECT count(*) FROM loans WHERE book_id=? AND returned=0", (book_id,)).fetchone()[0]
        if active >= book[0]:
            raise ValueError("No copies available")
        try:
            return db.execute("INSERT INTO loans(book_id,member_id,due) VALUES (?,?,?)",(book_id,member_id,due)).lastrowid
        except sqlite3.IntegrityError:
            raise ValueError("Member already has this book") from None

def return_loan(path, loan_id):
    if isinstance(loan_id,bool) or not isinstance(loan_id,int) or loan_id<1:
        raise ValueError("Invalid loan ID")
    with closing(connect(path)) as db, db:
        updated = db.execute("UPDATE loans SET returned=1 WHERE id=? AND returned=0", (loan_id,)).rowcount
        if not updated:
            raise ValueError("Active loan not found")

def snapshot(path, today=None):
    today = date(today or dt.date.today().isoformat())
    with closing(connect(path)) as db, db:
        db.row_factory=sqlite3.Row
        books=[dict(x) for x in db.execute("SELECT b.id,b.title,b.total,b.total-(SELECT count(*) FROM loans l WHERE l.book_id=b.id AND l.returned=0) available FROM books b ORDER BY b.id")]
        members=[dict(x) for x in db.execute("SELECT id,name FROM members ORDER BY id")]
        loans=[dict(x) for x in db.execute("SELECT l.id,b.title book,m.name member,l.due,CASE WHEN l.due < ? THEN 1 ELSE 0 END overdue FROM loans l JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id WHERE l.returned=0 ORDER BY l.due,l.id",(today,))]
    return {"books":books,"members":members,"loans":loans}
