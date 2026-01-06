
from ingestion.parsers import ColumnMapping, BaseParser
from ingestion.models import TransactionSource
import unittest
import os

class TestColumnMappingValidation(unittest.TestCase):
    def test_validate_valid_mapping(self):
        # Case 1: Date and Amount
        mapping = ColumnMapping(date="Date", amount="Amount")
        errors = mapping.validate()
        self.assertEqual(len(errors), 0, f"Expected no errors, got {errors}")

        # Case 2: Posting Date and Debit/Credit
        mapping = ColumnMapping(posting_date="Posting Date", debit="Debit", credit="Credit")
        errors = mapping.validate()
        self.assertEqual(len(errors), 0, f"Expected no errors, got {errors}")

    def test_validate_invalid_mapping(self):
        # Case 1: Missing Date
        mapping = ColumnMapping(amount="Amount")
        errors = mapping.validate()
        self.assertIn("Missing date column mapping (need 'date' or 'posting_date')", errors)

        # Case 2: Missing Amount/Debit/Credit
        mapping = ColumnMapping(date="Date")
        errors = mapping.validate()
        self.assertIn("Missing value column mapping (need 'amount' or both 'debit' and 'credit')", errors)
        
        # Case 3: Missing Both
        mapping = ColumnMapping()
        errors = mapping.validate()
        self.assertEqual(len(errors), 2)

class TestparserValidation(unittest.TestCase):
    def test_parser_validation_call(self):
        # Create a dummy CSV file
        with open("test_dummy.csv", "w") as f:
            f.write("col1,col2\nval1,val2")
            
        parser = BaseParser(TransactionSource.BANK, ColumnMapping(date="col1")) # Invalid mapping (missing amount)
        
        try:
            with self.assertRaises(ValueError) as cm:
                parser.parse_file("test_dummy.csv")
            self.assertIn("Invalid column mapping", str(cm.exception))
        finally:
            if os.path.exists("test_dummy.csv"):
                os.remove("test_dummy.csv")

if __name__ == '__main__':
    unittest.main()
