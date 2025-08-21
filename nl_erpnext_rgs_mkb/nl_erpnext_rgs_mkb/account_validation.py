# nl_erpnext_rgs_mkb/nl_erpnext_rgs_mkb/account_validation.py
"""
Account validation hooks for Dutch RGS MKB compliance
"""

import frappe
from frappe import _

def validate_rgs_compliance(doc, method):
    """
    Validate RGS compliance when Account documents are saved
    
    This hook ensures that:
    1. RGS codes are properly formatted
    2. Account numbers follow Dutch standards
    3. Account types match RGS requirements
    """
    
    # Skip validation for non-Dutch companies or if RGS is disabled
    if not is_rgs_enabled(doc.company):
        return
    
    # Validate RGS code format if present
    if doc.get('rgs_code'):
        validate_rgs_code_format(doc)
    
    # Validate account number format for Dutch standards
    if doc.get('account_number'):
        validate_dutch_account_number(doc)
    
    # Ensure account type matches RGS classification
    if doc.get('rgs_code') and doc.get('account_type'):
        validate_account_type_rgs_match(doc)

def validate_rgs_code_format(doc):
    """Validate RGS code follows proper format"""
    rgs_code = doc.rgs_code
    
    # Basic RGS code validation
    if not rgs_code.startswith(('B', 'W')):
        frappe.throw(_("RGS code must start with 'B' (Balance Sheet) or 'W' (Profit & Loss)"))
    
    # Check if RGS code exists in classifications
    if not frappe.db.exists("RGS Classification", {"rgs_code": rgs_code}):
        frappe.throw(_("RGS code '{0}' not found in RGS Classifications").format(rgs_code))

def validate_dutch_account_number(doc):
    """Validate Dutch account number format (5 digits with leading zeros)"""
    account_number = doc.account_number
    
    # Ensure 5-digit format
    if len(account_number) != 5 or not account_number.isdigit():
        frappe.throw(_("Account number must be exactly 5 digits for Dutch RGS compliance"))
    
    # Validate number ranges based on RGS structure
    first_digit = int(account_number[0])
    if first_digit == 0:
        # Root accounts - allow
        pass
    elif first_digit not in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
        frappe.throw(_("Invalid account number range for Dutch RGS"))

def validate_account_type_rgs_match(doc):
    """Ensure account type matches RGS classification requirements"""
    rgs_classification = frappe.get_doc("RGS Classification", {"rgs_code": doc.rgs_code})
    
    if not rgs_classification:
        return
    
    # Map RGS categories to ERPNext account types
    rgs_to_account_type = {
        'BIka': ['Asset', 'Receivable'],  # Kas/Bank accounts
        'BVma': ['Asset'],                # Materiële vaste activa
        'BVor': ['Asset', 'Receivable'],  # Vorderingen
        'BEiv': ['Equity'],               # Eigen vermogen
        'BScv': ['Liability'],            # Voorzieningen
        'BSch': ['Liability', 'Payable'], # Schulden
        'WOmz': ['Income'],               # Omzet
        'WOvb': ['Income'],               # Overige bedrijfsopbrengsten
        'WInk': ['Expense'],              # Inkoopwaarde omzet
        'WPer': ['Expense'],              # Personeelskosten
        'WAfs': ['Expense'],              # Afschrijvingen
        'WOvk': ['Expense'],              # Overige bedrijfskosten
        'WFin': ['Income', 'Expense'],    # Financiële baten/lasten
        'WBel': ['Expense'],              # Belastingen
    }
    
    # Extract category from RGS code (first 4 characters)
    rgs_category = doc.rgs_code[:4] if len(doc.rgs_code) >= 4 else doc.rgs_code
    
    allowed_types = rgs_to_account_type.get(rgs_category, [])
    if allowed_types and doc.account_type not in allowed_types:
        frappe.throw(_("Account type '{0}' is not compatible with RGS category '{1}'. Allowed types: {2}")
                    .format(doc.account_type, rgs_category, ', '.join(allowed_types)))

def is_rgs_enabled(company):
    """Check if RGS compliance is enabled for the company"""
    # Check company settings or site config
    company_doc = frappe.get_doc("Company", company)
    
    # Check if company is Dutch (country = Netherlands)
    if company_doc.country != "Netherlands":
        return False
    
    # Check site configuration
    return frappe.conf.get('rgs_enabled', True)
