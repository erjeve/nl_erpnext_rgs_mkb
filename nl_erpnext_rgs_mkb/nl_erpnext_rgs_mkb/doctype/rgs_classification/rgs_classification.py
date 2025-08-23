# Copyright (c) 2025, Your Organization and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RGSClassification(Document):
    """RGS Classification Tree for Dutch Chart of Accounts compliance"""
    
    def validate(self):
        """Validate RGS Classification entry"""
        self.validate_rgs_code()
        self.validate_nivo()
        self.set_parent_based_on_code()
        
    def validate_rgs_code(self):
        """Validate RGS code format"""
        if not self.rgs_code:
            frappe.throw("RGS Code is required")
            
        # Basic RGS code validation
        if not (self.rgs_code.startswith('B') or self.rgs_code.startswith('W')):
            frappe.throw("RGS Code must start with 'B' (Balance) or 'W' (Winst & Verlies)")
            
    def validate_nivo(self):
        """Validate RGS Nivo level"""
        if not self.rgs_nivo or self.rgs_nivo < 1 or self.rgs_nivo > 5:
            frappe.throw("RGS Nivo must be between 1 and 5")
            
        # Set is_group based on nivo
        self.is_group = self.rgs_nivo < 5
        
    def set_parent_based_on_code(self):
        """Set parent based on RGS code hierarchy"""
        if self.rgs_nivo <= 1:
            self.parent_rgs_classification = None
            return
            
        # Find parent by removing the last segment
        parent_code = self.get_parent_code(self.rgs_code)
        if parent_code:
            parent = frappe.db.get_value("RGS Classification", {"rgs_code": parent_code}, "name")
            if parent:
                self.parent_rgs_classification = parent
                
    def get_parent_code(self, rgs_code):
        """Determine parent RGS code based on hierarchy rules"""
        if len(rgs_code) <= 1:
            return None
            
        # Simple hierarchy: remove last 3 characters if longer than 4
        if len(rgs_code) > 4:
            return rgs_code[:-3]
        elif len(rgs_code) > 1:
            return rgs_code[0]  # Return B or W
        
        return None
        
    def create_account(self, company):
        """Create an Account based on this RGS Classification"""
        if frappe.db.exists("Account", {"rgs_code": self.rgs_code, "company": company}):
            frappe.throw(f"Account with RGS Code {self.rgs_code} already exists for {company}")
            
        # Create new account
        account = frappe.new_doc("Account")
        account.account_name = self.rgs_description
        account.company = company
        account.account_type = self.account_type or "Asset"
        account.is_group = self.is_group
        
        if self.balance_must_be:
            account.balance_must_be = self.balance_must_be
            
        # Set RGS fields
        account.rgs_code = self.rgs_code
        account.rgs_nivo = self.rgs_nivo
        account.rgs_referentienummer = self.rgs_reference_number
        
        # Find parent account
        if self.parent_rgs_classification:
            parent_rgs = frappe.get_doc("RGS Classification", self.parent_rgs_classification)
            parent_account = frappe.db.get_value("Account", {
                "rgs_code": parent_rgs.rgs_code,
                "company": company
            })
            if parent_account:
                account.parent_account = parent_account
                
        account.insert()
        return account
        
    @frappe.whitelist()
    def generate_chart_for_entity(self, entity_type="ZZP", company=None):
        """Generate Chart of Accounts for specific entity type"""
        if not company:
            frappe.throw("Company is required")
            
        entity_field = f"applicable_{entity_type.lower()}"
        if not hasattr(self, entity_field):
            frappe.throw(f"Invalid entity type: {entity_type}")
            
        applicable_value = getattr(self, entity_field)
        if applicable_value not in ["J", "P"]:
            frappe.throw(f"This RGS code is not applicable for {entity_type}")
            
        return self.create_account(company)
