# nl_erpnext_rgs_mkb/utils.py
"""
Utility functions for Dutch RGS MKB compliance
"""

import frappe

def boot_session(bootinfo):
    """
    Boot session hook to add RGS-specific data to the client session
    
    This function is called during user login to provide RGS-specific
    data to the client side for Dutch compliance features.
    """
    
    # Add RGS version and locale information
    bootinfo.rgs_version = "3.7"
    bootinfo.country_code = "NL" 
    bootinfo.locale = "nl_NL"
    
    # Add RGS classifications if user has access
    if frappe.has_permission("RGS Classification", "read"):
        bootinfo.rgs_classifications = frappe.get_all(
            "RGS Classification", 
            fields=["name", "rgs_code", "rgs_description", "rgs_nivo"],
            filters={"rgs_status": "A"},
            order_by="rgs_code"
        )
    
    # Add company-specific RGS settings
    if hasattr(frappe.local, 'site_config') and frappe.local.site_config.get('rgs_enabled'):
        bootinfo.rgs_enabled = True
        bootinfo.rgs_entity_type = frappe.local.site_config.get('rgs_entity_type', 'ZZP')
