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
        
        
    # Multiple unit tests for CIK_merge_cleanup
    def test_cik_merge_cleanup_standard_append(self):
        #Tests that values are concatenated with '|' when they differ.
        data = {
            '_merge': ['both'],
            'standardized_names': ['Apple Inc'],
            'std_name': ['Apple'],
            'aliases': ['AAPL'],
            'alias_col': ['Apple_Alias'],
            'ticker': ['AAPL'],
            'ticker_col': ['AAPL_NEW'],
            'sources': ['CRSP']
        }
        df = pd.DataFrame(data)

        CIK_merge_cleaup(df, 'alias_col', 'Compustat', 'ticker_col')

        self.assertEqual(df.loc[0, 'standardized_names'], 'Apple Inc|Apple')
        self.assertEqual(df.loc[0, 'aliases'], 'AAPL|Apple_Alias')
        self.assertEqual(df.loc[0, 'ticker'], 'AAPL|AAPL_NEW')
        self.assertEqual(df.loc[0, 'sources'], 'CRSP,Compustat')
        self.assertEqual(df.loc[0, 'matching_type'], 'cik_id_match')


    def test_cik_merge_cleanup_no_duplicates(self):
        # Tests that the function does not append if the value is already identical.
        data = {
            '_merge': ['both'],
            'standardized_names': ['Microsoft'],
            'std_name': ['Microsoft'],
            'aliases': ['MSFT'],
            'alias_col': ['MSFT'],
            'ticker': ['MSFT'],
            'ticker_col': ['MSFT'],
            'sources': ['']
        }
        df = pd.DataFrame(data)

        CIK_merge_cleaup(df, 'alias_col', 'Compustat', 'ticker_col')

        self.assertEqual(df.loc[0, 'standardized_names'], 'Microsoft')
        self.assertEqual(df.loc[0, 'aliases'], 'MSFT')
        self.assertEqual(df.loc[0, 'sources'], 'Compustat')

    def test_cik_merge_cleanup_nan_handling(self):
        # Tests that NaNs are filled with the new value rather than prepending a pipe.
        data = {
            '_merge': ['both'],
            'standardized_names': [np.nan],
            'std_name': ['New Corp'],
            'aliases': [None],
            'alias_col': ['NEW_ALIAS'],
            'ticker': [pd.NA],
            'ticker_col': ['NEW_TICK'],
            'sources': [np.nan]
        }
        df = pd.DataFrame(data)

        CIK_merge_cleaup(df, 'alias_col', 'SEC', 'ticker_col')

        self.assertEqual(df.loc[0, 'standardized_names'], 'New Corp')
        self.assertEqual(df.loc[0, 'aliases'], 'NEW_ALIAS')
        self.assertEqual(df.loc[0, 'ticker'], 'NEW_TICK')
        self.assertEqual(df.loc[0, 'sources'], 'SEC')


    def test_cik_merge_cleanup_masking(self):
        # Tests that sources and matching_type only update for '_merge == both'.
        data = {
            '_merge': ['left_only', 'both'],
            'standardized_names': ['A', 'B'],
            'std_name': ['A_new', 'B_new'],
            'aliases': ['A1', 'B1'],
            'alias_col': ['A2', 'B2'],
            'ticker': ['TA', 'TB'],
            'ticker_col': ['TXA', 'TXB'],
            'sources': [np.nan, np.nan]
        }
        df = pd.DataFrame(data)

        CIK_merge_cleaup(df, 'alias_col', 'SRC', 'ticker_col')

        # Row 0 (left_only)
        self.assertTrue(pd.isna(df.loc[0, 'sources']))
        # Row 1 (both)
        self.assertEqual(df.loc[1, 'sources'], 'SRC')
        self.assertEqual(df.loc[1, 'matching_type'], 'cik_id_match')


    def test_cik_merge_cleanup_naics(self):
        # Tests logic for NAICS column cleanup.
        data = {
            '_merge': ['both'],
            'standardized_names': ['Test'],
            'std_name': ['Test'],
            'aliases': ['T'],
            'alias_col': ['T'],
            'ticker': ['T'],
            'ticker_col': ['T'],
            'sources': [''],
            'naics': [111],
            'naics_new': [222]
        }
        df = pd.DataFrame(data)

        CIK_merge_cleaup(df, 'alias_col', 'SRC', 'ticker_col', naics_column_name='naics_new')

        self.assertEqual(df.loc[0, 'naics'], '111|222')

if __name__ == '__main__':
    unittest.main()