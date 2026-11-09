import tempfile
import unittest
from pathlib import Path
import library

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/'test.sqlite')
        library.initialize(self.path)
        self.book=library.add_book(self.path,'Example',1)
        self.a=library.add_member(self.path,'A')
        self.b=library.add_member(self.path,'B')
    def tearDown(self):self.tmp.cleanup()
    def test_borrow_return_and_overdue(self):
        loan=library.borrow(self.path,self.book,self.a,'2026-11-01')
        self.assertEqual(library.snapshot(self.path,'2026-11-02')['loans'][0]['overdue'],1)
        self.assertEqual(library.snapshot(self.path)['books'][0]['available'],0)
        library.return_loan(self.path,loan)
        self.assertEqual(library.snapshot(self.path)['books'][0]['available'],1)
        with self.assertRaises(ValueError):library.return_loan(self.path,loan)
    def test_out_of_stock_rolls_back(self):
        library.borrow(self.path,self.book,self.a,'2026-11-01')
        with self.assertRaises(ValueError):library.borrow(self.path,self.book,self.b,'2026-11-01')
        self.assertEqual(len(library.snapshot(self.path)['loans']),1)
    def test_invalid_values(self):
        for value in [0,-1,True,'3']:
            with self.assertRaises(ValueError):library.add_book(self.path,'X',value)
        with self.assertRaises(ValueError):library.borrow(self.path,self.book,self.a,'2026-02-30')
        with self.assertRaises(ValueError):library.add_member(self.path,' ')
