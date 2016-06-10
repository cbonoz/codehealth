import compare
import unittest

class PreprocessFilesTestCase(unittest.TestCase):
    def test_additions(self):
        t1 = ('def foo():\n'
              '    print \'foo\'\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'foo\'\n'
              '    print \'bar\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        additions, deletions = compare.preprocess_files(t1, t2)
        self.assertEqual(len(additions), 2)
        self.assertTrue(not deletions)
        self.assertEqual(additions[0], 3)
        self.assertEqual(additions[1], 4)
        
    def test_deletions(self):
        t1 = ('def foo():\n'
              '    print \'foo\'\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'foo\'\n'
              '    print \'bar\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        additions, deletions = compare.preprocess_files(t2, t1, 2)
        self.assertTrue(not additions)
        self.assertEqual(len(deletions), 2) 
        self.assertEqual(deletions[0], 4)
        
         # Notice here that `    print 'baz'` is expected to be on line 3.
        self.assertEqual(deletions[1], 4) 

    def test_modification(self):
        t1 = ('def foo():\n'
              '    print \'foo\'\n'
              '    print \'bar\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'chaos\'\n'
              '    print \'foo\'\n'
              '    print \'monkey\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        additions, deletions = compare.preprocess_files(t1, t2, 3)
        self.assertEqual(len(additions), 2)
        self.assertEqual(len(deletions), 1) 
        self.assertEqual(additions[0], 4)
        self.assertEqual(additions[1], 6)
        self.assertEqual(deletions[0], 6) 

class CompareTestCase(unittest.TestCase):
    def test_additions(self):
        t1 = ('def foo():\n'
              '    print \'foo\' # (1)\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'foo\' # (1)\n'
              '    print \'bar\'\n'
              '    print \'baz\' # (2)\n'
              '    '            
             )
             
        result = compare.compare(t1, t2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].left_bounds(), (2, 16))
        self.assertEqual(result[0].right_bounds(), (2, 21))
        self.assertEqual(result[0].score(), 98)
        self.assertEqual(result[1].left_bounds(), (4, 16))
        self.assertEqual(result[1].right_bounds(), (4, 21))
        self.assertEqual(result[1].score(), 100)
        
    def test_deletions_before(self):
        t1 = ('def foo():\n'
              '    print \'baz\' # (1)\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'foo\'\n'
              '    print \'bar\'\n'
              '    print \'baz\' # (1)\n'
              '    '            
             )
             
        result = compare.compare(t2, t1, 4)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].left_bounds(), (2, 16))
        self.assertEqual(result[0].right_bounds(), (2, 21))
        
        # Same idea here: both deletions on the same line.
        self.assertEqual(result[0].score(), 92)
        
    def test_deletions_after(self):
        t1 = ('def foo():\n'
              '    print \'foo\' # (1)\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'foo\' # (1)\n'
              '    print \'bar\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        result = compare.compare(t2, t1, 4)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].left_bounds(), (2, 16))
        self.assertEqual(result[0].right_bounds(), (2, 21))
        
        # Same idea here: both deletions on the same line.
        self.assertEqual(result[0].score(), 92)

    def test_modification(self):
        t1 = ('def foo():\n'
              '    print \'foo\' # (2)\n'
              '    print \'bar\'\n'
              '    print \'baz\'\n'
              '    '            
             )
             
        t2 = ('def foo():\n'
              '    print \'chaos\' # (1)\n' # -8
              '    print \'foo\' # (2)\n'
              '    print \'monkey\'\n'      # -16
              '    print \'baz\'\n'
              '    '            
             )
             
        result = compare.compare(t1, t2, 8)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].left_bounds(), (3, 16))
        self.assertEqual(result[0].right_bounds(), (3, 21))
        self.assertEqual(result[0].score(), 76)
        self.assertEqual(result[1].left_bounds(), (2, 18))
        self.assertEqual(result[1].right_bounds(), (2, 23))
        self.assertEqual(result[1].score(), 100)  