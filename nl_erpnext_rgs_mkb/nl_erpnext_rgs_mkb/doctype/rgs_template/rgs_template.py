# Copyright (c) 2025, Your Organization and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class RGSTemplate(Document):
    """RGS Template for generating Chart of Accounts based on entity type"""
    
    def validate(self):
        """Validate RGS Template"""
        self.validate_generation_rules()
        
    def validate_generation_rules(self):
        """Validate generation rules JSON"""
        if self.generation_rules:
            try:
                json.loads(self.generation_rules)
            except json.JSONDecodeError:
                frappe.throw("Generation Rules must be valid JSON")
                
    @frappe.whitelist()
    def generate_chart_of_accounts(self, company):
        """Generate Chart of Accounts for a company based on this template"""
        if not company:
            frappe.throw("Company is required")
            
        # Get generation rules
        rules = self.get_generation_rules()
        
        # Get applicable RGS codes
        applicable_codes = self.get_applicable_rgs_codes()
        
        created_accounts = []
        errors = []
        
        # Sort by nivo to ensure proper hierarchy
        sorted_codes = sorted(applicable_codes, key=lambda x: x.get('nivo', 1))
        
        for rgs_data in sorted_codes:
            try:
                account = self.create_account_from_rgs(rgs_data, company, rules)
                if account:
                    created_accounts.append(account.name)
            except Exception as e:
                errors.append(f"Error creating account for {rgs_data.get('rgs_code', 'Unknown')}: {str(e)}")
                
        return {
            'created_accounts': created_accounts,
            'errors': errors,
            'total_created': len(created_accounts)
        }
        
    def get_generation_rules(self):
        """Get generation rules as dictionary"""
        default_rules = {
            'include_starting_balances': False,
            'enforce_balance': True,
            'include_inactive': False,
            'only_mkb_standard': True
        }
        
        if self.generation_rules:
            try:
                custom_rules = json.loads(self.generation_rules)
                default_rules.update(custom_rules)
            except json.JSONDecodeError:
                pass
                
        return default_rules
        
    def get_applicable_rgs_codes(self):
        """Get RGS codes applicable for this template's entity type"""
        entity_field = f"applicable_{self.entity_type.lower()}"
        
        # Query RGS Classifications that are applicable for this entity
        rgs_classifications = frappe.get_all(
            "RGS Classification",
            filters={
                entity_field: ["in", ["J", "P"]],
                "rgs_nivo": ["<=", self.max_nivo or 5],
                "rgs_status": "A"  # Only active
            },
            fields=["*"]
        )
        
        # Filter by include_detail_level
        if self.include_detail_level:
            rgs_classifications = [
                rgs for rgs in rgs_classifications 
                if rgs.rgs_nivo <= self.include_detail_level
            ]
            
        return rgs_classifications
        
    def create_account_from_rgs(self, rgs_data, company, rules):
        """Create an Account from RGS Classification data"""
        # Check if account already exists
        existing = frappe.db.get_value("Account", {
            "rgs_code": rgs_data.rgs_code,
            "company": company
        })
        
        if existing:
            return frappe.get_doc("Account", existing)
            
        # Create new account
        account = frappe.new_doc("Account")
        account.account_name = rgs_data.rgs_description
        account.company = company
        account.account_type = rgs_data.account_type or "Asset"
        account.is_group = rgs_data.is_group
        
        # Format account number (5 digits with leading zeros)
        if rgs_data.rgs_reference_number and rgs_data.rgs_reference_number != "0":
            account.account_number = str(rgs_data.rgs_reference_number).zfill(5)
        
        # Set balance requirement
        if rgs_data.balance_must_be and rules.get('enforce_balance'):
            account.balance_must_be = rgs_data.balance_must_be
            
        # Set RGS custom fields
        account.rgs_code = rgs_data.rgs_code
        account.rgs_nivo = rgs_data.rgs_nivo
        account.rgs_referentienummer = rgs_data.rgs_reference_number
        
        # Find parent account
        parent_account = self.find_parent_account(rgs_data, company)
        if parent_account:
            account.parent_account = parent_account
        else:
            # Set root account based on account type
            account.parent_account = self.get_root_account(rgs_data.account_type, company)
            
        account.insert()
        return account
        
    def find_parent_account(self, rgs_data, company):
        """Find parent account for RGS classification"""
        if rgs_data.rgs_nivo <= 1:
            return None
            
        # Find parent RGS code
        parent_rgs_code = self.get_parent_rgs_code(rgs_data.rgs_code)
        
        if parent_rgs_code:
            parent_account = frappe.db.get_value("Account", {
                "rgs_code": parent_rgs_code,
                "company": company
            })
            return parent_account
            
        return None
        
    def get_parent_rgs_code(self, rgs_code):
        """Get parent RGS code based on hierarchy"""
        if len(rgs_code) <= 1:
            return None
            
        # Remove last 3 characters if longer than 4
        if len(rgs_code) > 4:
            return rgs_code[:-3]
        elif len(rgs_code) > 1:
            return rgs_code[0]  # Return B or W
            
        return None
        
    def get_root_account(self, account_type, company):
        """Get root account for account type"""
        root_mapping = {
            'Asset': 'Assets',
            'Liability': 'Liabilities',
            'Equity': 'Equity',
            'Income': 'Income',
            'Expense': 'Expenses'
        }
        
        root_type = root_mapping.get(account_type, 'Assets')
        
        root_account = frappe.db.get_value("Account", {
            "account_name": root_type,
            "company": company,
            "is_group": 1
        })
        
        return root_account
