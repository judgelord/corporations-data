import unittest
import pandas as pd
import numpy as np
import sys
from helper_functions import *

class TestOrgNameProcessing(unittest.TestCase):

    # Tests for get_longest_common_substring
    def test_longest_common_substring(self):
        s1 = "Apple Inc"
        s2 = "Apple Corp"
        self.assertEqual(get_longest_common_substring(s1, s2, len(s1), len(s2)), "Apple ")
        
        # Test no common substring
        self.assertEqual(get_longest_common_substring("ABC", "XYZ", 3, 3), "")
        
        # Test full match
        self.assertEqual(get_longest_common_substring("Test", "Test", 4, 4), "Test")

    # Tests for basicHash
    def test_basicHash(self):
        self.assertEqual(basicHash("Apple & Co."), "apple and co")
        self.assertEqual(basicHash("  Spaces  "), "spaces")
        self.assertEqual(basicHash("Punc'tua.tion!"), "punctuation")

    # Tests for corpHash
    def test_corpHash(self):
        # Should remove "The" and corporate suffixes
        self.assertEqual(corpHash("The Apple Inc"), "apple")
        self.assertEqual(corpHash("Goldman Sachs Group"), "goldman sachs")
        # Should handle internal "and" conversion via basicHash
        self.assertEqual(corpHash("A & B LLC"), "a and b")

    # Tests for to_standardized_name
    def test_to_standardized_name(self):
        # Testing metadata stripping (comma)
        self.assertEqual(to_standardized_name("Goldman Sachs, New York"), "goldman sachs")
        
        # Testing PDF pattern removal
        self.assertEqual(to_standardized_name("Report 10 kb pdf"), "report")
        
        # Testing stopword and non-financial removal
        # "University" is in NON_FINANCIAL_ORG_TERMS
        self.assertEqual(to_standardized_name("Stanford University"), "stanford")
        
        # Test None/NA handling
        self.assertEqual(to_standardized_name(None), "")
        self.assertEqual(to_standardized_name("NA"), "")

    # Tests for clean_corporate_suffix
    def test_clean_org_alias(self):
        self.assertEqual(clean_org_alias("Apple Inc."), "apple")
        self.assertEqual(clean_org_alias("Micro-soft Corp"), "micro soft")        
        self.assertEqual(clean_org_alias("AIR, A SERIES OF HUMANITY EQUITY, LLC"),
                                                "air a series of humanity equity")

    # Tests for normalize_to_list
    def test_normalize_to_list(self):
        # Single value
        self.assertEqual(normalize_to_list(123), [123])
        # NA handling
        self.assertEqual(normalize_to_list(np.nan), [])

    # Tests for clean_cik
    def test_clean_cik(self):
        # Basic float to string int
        self.assertEqual(clean_cik(12345.0), "12345")
        # String representation
        self.assertEqual(clean_cik("000123"), "123")
        # List handling (takes first element)
        self.assertEqual(clean_cik([9876, 5432]), "9876")
        # Empty/NA handling
        self.assertEqual(clean_cik(""), "")
        self.assertEqual(clean_cik(np.nan), "")

if __name__ == '__main__':
    unittest.main()