# nl_erpnext_rgs_mkb/hooks.py
app_name = "nl_erpnext_rgs_mkb"
app_title = "Dutch RGS MKB"
app_publisher = "Your Organization"
app_description = "Dutch RGS MKB 3.7 compliance for ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "admin@fivi.eu"
app_license = "MIT"
app_version = "0.1.0"

# Integration with ERPNext
required_apps = ["erpnext"]

# Document Events
doc_events = {
    "Account": {
        "validate": "nl_erpnext_rgs_mkb.nl_erpnext_rgs_mkb.account_validation.validate_rgs_compliance"
    }
}

# Boot session
boot_session = "nl_erpnext_rgs_mkb.utils.boot_session"

# Fixtures - Standard Frappe way for custom fields and data
# Temporarily disabled for migration
fixtures = [
    "Custom Field"
    # {
    #     "doctype": "RGS Classification", 
    #     "filters": {"rgs_status": "A"}
    # }
]