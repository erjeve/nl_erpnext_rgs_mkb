#!/usr/bin/env python3
"""
Enhanced RGS to ERPNext Root Type Mapping
Multi-factor analysis for accurate account classification

This script implements intelligent root_type derivation using:
1. RGS Code structure analysis (B vs W prefix, hierarchical patterns)
2. Debit/Credit indicators (rgsDc field)
3. Account descriptions and Dutch accounting terminology
4. Concept mappings from labels.csv (supporting evidence)
5. General accounting principles and Dutch GAAP standards

Author: ERPNext RGS MKB Project
Date: August 2025
"""

import json
import csv
import re
from pathlib import Path

class RGSToERPNextMapper:
    """
    Comprehensive mapper for RGS codes to ERPNext account structure
    """
    
    def __init__(self):
        self.balance_sheet_assets = {
            'patterns': [
                r'BIva',  # Immateriële vaste activa (Intangible assets)
                r'BMva',  # Materiële vaste activa (Tangible assets)
                r'BFin',  # Financiële vaste activa (Financial assets)
                r'BVor',  # Vorderingen (Receivables)
                r'BEff',  # Effecten (Securities)
                r'BLiq',  # Liquide middelen (Cash and equivalents)
                r'BKas',  # Kas (Cash)
                r'BBan',  # Bank (Bank accounts)
                r'BGir',  # Giro (Giro accounts)
                r'BSpaa', # Spaarrekening (Savings accounts)
                r'BVoo',  # Voorraden (Inventory)
            ],
            'keywords': [
                'activa', 'vorderingen', 'liquide', 'kas', 'bank', 'giro', 
                'spaar', 'effecten', 'aandelen', 'obligaties', 'voorraden',
                'debiteuren', 'inventaris', 'machines', 'gebouwen', 'goodwill'
            ]
        }
        
        self.balance_sheet_liabilities = {
            'patterns': [
                r'BLas',  # Langlopende schulden (Long-term liabilities)
                r'BKor',  # Kortlopende schulden (Current liabilities)
                r'BKre',  # Crediteuren (Trade creditors)
                r'BVer',  # Verschuldigde (Accrued liabilities)
                r'BVoo.*[Ss]chuld',  # Voorzieningen (Provisions)
                r'BBel',  # Belastingen (Tax liabilities)
                r'BHyp',  # Hypotheken (Mortgages)
                r'BLen',  # Leningen (Loans)
            ],
            'keywords': [
                'schulden', 'crediteuren', 'verschuldigd', 'voorziening',
                'belasting', 'btw', 'hypotheek', 'lening', 'rente',
                'pensioen', 'sociale lasten', 'leveranciers'
            ]
        }
        
        self.balance_sheet_equity = {
            'patterns': [
                r'BEig',  # Eigen vermogen (Equity)
                r'BKap',  # Kapitaal (Capital)
                r'BRes',  # Reserves (Reserves)
                r'BWin',  # Winst (Retained earnings)
                r'BVer.*verlies',  # Accumulated losses
            ],
            'keywords': [
                'eigen vermogen', 'kapitaal', 'reserve', 'winst', 'verlies',
                'aandelen', 'inbreng', 'resultaat', 'bestemming'
            ]
        }
        
        self.income_patterns = {
            'patterns': [
                r'WOmz',  # Omzet (Revenue/Sales)
                r'WOpb',  # Opbrengsten (Income)
                r'WVer.*verkoop',  # Sales income
                r'WBed',  # Bedrijfsopbrengsten (Operating income)
                r'WFin.*baten',  # Financial income
            ],
            'keywords': [
                'omzet', 'verkoop', 'opbrengst', 'inkomsten', 'honorarium',
                'subsidie', 'rente baten', 'dividend', 'huur ontvangen'
            ]
        }
        
        self.expense_patterns = {
            'patterns': [
                r'WKos',  # Kosten (Costs/Expenses)
                r'WAfs',  # Afschrijvingen (Depreciation)
                r'WBed.*kosten',  # Operating expenses
                r'WFin.*lasten',  # Financial expenses
                r'WBel',  # Belastingen (Tax expenses)
                r'WLoo',  # Loonkosten (Personnel costs)
                r'WHui',  # Huisvestingskosten (Housing costs)
            ],
            'keywords': [
                'kosten', 'uitgaven', 'afschrijving', 'salaris', 'loon',
                'huur', 'energie', 'telefoon', 'verzekering', 'rente lasten',
                'belasting', 'boekhouding', 'kantoor', 'auto'
            ]
        }

    def determine_root_type(self, rgs_record, concept_mappings=None):
        """
        Determine ERPNext root_type using multi-factor analysis
        
        Args:
            rgs_record: Dict containing RGS classification data
            concept_mappings: List of concept identifiers from labels.csv
            
        Returns:
            str: ERPNext root_type (Asset, Liability, Equity, Income, Expense)
        """
        rgs_code = rgs_record.get('rgsCode', '')
        rgs_desc = (rgs_record.get('rgsOmskort', '') or '').lower()
        rgs_dc = rgs_record.get('rgsDc', '')
        
        # Primary classification: B (Balance Sheet) vs W (P&L)
        if rgs_code.startswith('B'):
            return self._classify_balance_sheet_account(rgs_code, rgs_desc, rgs_dc, concept_mappings)
        elif rgs_code.startswith('W'):
            return self._classify_pnl_account(rgs_code, rgs_desc, rgs_dc, concept_mappings)
        
        # Fallback for unknown patterns
        return self._fallback_classification(rgs_code, rgs_desc, rgs_dc)

    def _classify_balance_sheet_account(self, rgs_code, rgs_desc, rgs_dc, concept_mappings):
        """Classify Balance Sheet accounts (B prefix)"""
        
        # Check concept mappings first (most reliable)
        if concept_mappings:
            for concept in concept_mappings:
                if 'liability' in concept.lower() or 'liabilities' in concept.lower():
                    return "Liability"
                elif 'equity' in concept.lower():
                    return "Equity"
                elif 'asset' in concept.lower():
                    return "Asset"
        
        # Pattern-based classification
        if self._matches_patterns(rgs_code, rgs_desc, self.balance_sheet_liabilities):
            return "Liability"
        elif self._matches_patterns(rgs_code, rgs_desc, self.balance_sheet_equity):
            return "Equity"
        elif self._matches_patterns(rgs_code, rgs_desc, self.balance_sheet_assets):
            return "Asset"
        
        # Debit/Credit analysis for Balance Sheet
        if rgs_dc == 'D':  # Debit normal balance
            # Most B-accounts with debit balance are assets
            return "Asset"
        elif rgs_dc == 'C':  # Credit normal balance
            # Credit balance could be liability or equity
            if any(keyword in rgs_desc for keyword in ['eigen', 'kapitaal', 'reserve', 'winst']):
                return "Equity"
            else:
                return "Liability"
        
        # Default for unclassified B accounts (conservative approach)
        return "Asset"

    def _classify_pnl_account(self, rgs_code, rgs_desc, rgs_dc, concept_mappings):
        """Classify Profit & Loss accounts (W prefix)"""
        
        # Check concept mappings
        if concept_mappings:
            for concept in concept_mappings:
                if 'income' in concept.lower() or 'revenue' in concept.lower():
                    return "Income"
                elif 'expense' in concept.lower() or 'cost' in concept.lower():
                    return "Expense"
        
        # Pattern-based classification
        if self._matches_patterns(rgs_code, rgs_desc, self.income_patterns):
            return "Income"
        elif self._matches_patterns(rgs_code, rgs_desc, self.expense_patterns):
            return "Expense"
        
        # Debit/Credit analysis for P&L
        if rgs_dc == 'C':  # Credit normal balance
            # Credit balance in P&L typically indicates income
            return "Income"
        elif rgs_dc == 'D':  # Debit normal balance
            # Debit balance in P&L typically indicates expense
            return "Expense"
        
        # Description-based fallback
        if any(keyword in rgs_desc for keyword in ['omzet', 'opbrengst', 'inkomst']):
            return "Income"
        else:
            return "Expense"

    def _matches_patterns(self, rgs_code, rgs_desc, pattern_dict):
        """Check if RGS code or description matches known patterns"""
        
        # Check regex patterns
        for pattern in pattern_dict['patterns']:
            if re.search(pattern, rgs_code, re.IGNORECASE):
                return True
        
        # Check keyword matches in description
        for keyword in pattern_dict['keywords']:
            if keyword in rgs_desc:
                return True
        
        return False

    def _fallback_classification(self, rgs_code, rgs_desc, rgs_dc):
        """Fallback classification for unknown patterns"""
        
        # Conservative defaults based on debit/credit
        if rgs_dc == 'D':
            if rgs_code.startswith('W'):
                return "Expense"
            else:
                return "Asset"
        elif rgs_dc == 'C':
            if rgs_code.startswith('W'):
                return "Income"
            else:
                return "Liability"
        
        # Ultimate fallback
        return "Asset" if rgs_code.startswith('B') else "Expense"

    def determine_account_type(self, rgs_record, root_type, concept_mappings=None):
        """
        Determine specific ERPNext account_type based on root_type and RGS data
        """
        rgs_code = rgs_record.get('rgsCode', '')
        rgs_desc = (rgs_record.get('rgsOmskort', '') or '').lower()
        
        if root_type == "Asset":
            return self._determine_asset_type(rgs_code, rgs_desc)
        elif root_type == "Liability":
            return self._determine_liability_type(rgs_code, rgs_desc)
        elif root_type == "Equity":
            return "Equity"  # ERPNext has generic Equity type
        elif root_type == "Income":
            return self._determine_income_type(rgs_code, rgs_desc)
        elif root_type == "Expense":
            return self._determine_expense_type(rgs_code, rgs_desc)
        
        return ""

    def _determine_asset_type(self, rgs_code, rgs_desc):
        """Determine specific asset account type"""
        
        # Bank and cash accounts
        if any(keyword in rgs_desc for keyword in ['bank', 'kas', 'giro', 'liquide']):
            return "Bank"
        
        # Receivables
        if any(keyword in rgs_desc for keyword in ['vordering', 'debiteur']):
            return "Receivable"
        
        # Fixed assets
        if any(keyword in rgs_code for keyword in ['Iva', 'Mva']) or \
           any(keyword in rgs_desc for keyword in ['vast', 'machine', 'gebouw', 'inventaris']):
            return "Fixed Asset"
        
        # Stock/Inventory
        if any(keyword in rgs_desc for keyword in ['voorraad', 'inventaris']):
            return "Stock"
        
        # Default to Current Asset
        return "Current Asset"

    def _determine_liability_type(self, rgs_code, rgs_desc):
        """Determine specific liability account type"""
        
        # Tax liabilities
        if any(keyword in rgs_desc for keyword in ['belasting', 'btw', 'loonheffing']):
            return "Tax"
        
        # Trade creditors
        if any(keyword in rgs_desc for keyword in ['crediteur', 'leverancier']):
            return "Payable"
        
        # Default to Current Liability
        return "Current Liability"

    def _determine_income_type(self, rgs_code, rgs_desc):
        """Determine specific income account type"""
        return "Income Account"

    def _determine_expense_type(self, rgs_code, rgs_desc):
        """Determine specific expense account type"""
        
        # Depreciation
        if any(keyword in rgs_desc for keyword in ['afschrijving']):
            return "Depreciation"
        
        # Tax expenses
        if any(keyword in rgs_desc for keyword in ['belasting']):
            return "Tax"
        
        # Default to Expense Account
        return "Expense Account"

    def determine_report_type(self, rgs_code):
        """Determine ERPNext report_type from RGS code"""
        if rgs_code.startswith('B'):
            return "Balance Sheet"
        elif rgs_code.startswith('W'):
            return "Profit and Loss"
        return ""

    def map_balance_must_be(self, rgs_dc):
        """Map RGS rgsDc to ERPNext balance_must_be"""
        if rgs_dc == 'D':
            return "Debit"
        elif rgs_dc == 'C':
            return "Credit"
        return ""


def main():
    """Test the enhanced mapping logic"""
    mapper = RGSToERPNextMapper()
    
    # Test cases from RGS data
    test_cases = [
        {
            "rgsCode": "BBan",
            "rgsOmskort": "Bank lopende rekening",
            "rgsDc": "D"
        },
        {
            "rgsCode": "BKre",
            "rgsOmskort": "Crediteuren",
            "rgsDc": "C"
        },
        {
            "rgsCode": "BEig",
            "rgsOmskort": "Eigen vermogen",
            "rgsDc": "C"
        },
        {
            "rgsCode": "WOmz",
            "rgsOmskort": "Omzet verkoop",
            "rgsDc": "C"
        },
        {
            "rgsCode": "WKos",
            "rgsOmskort": "Kosten inkoop",
            "rgsDc": "D"
        }
    ]
    
    print("🧪 Testing Enhanced RGS to ERPNext Mapping")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        root_type = mapper.determine_root_type(test_case)
        account_type = mapper.determine_account_type(test_case, root_type)
        report_type = mapper.determine_report_type(test_case['rgsCode'])
        balance_must_be = mapper.map_balance_must_be(test_case['rgsDc'])
        
        print(f"\nTest Case {i}:")
        print(f"  RGS Code: {test_case['rgsCode']}")
        print(f"  Description: {test_case['rgsOmskort']}")
        print(f"  RGS D/C: {test_case['rgsDc']}")
        print(f"  → Root Type: {root_type}")
        print(f"  → Account Type: {account_type}")
        print(f"  → Report Type: {report_type}")
        print(f"  → Balance Must Be: {balance_must_be}")
    
    print("\n✅ Enhanced mapping logic completed successfully!")

if __name__ == "__main__":
    main()
