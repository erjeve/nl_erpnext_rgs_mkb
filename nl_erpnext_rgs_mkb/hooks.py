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

# Custom fields for existing doctypes
custom_fields = {
    "Account": [
        {
            "fieldname": "rgs_section",
            "label": "RGS Information",
            "fieldtype": "Section Break",
            "insert_after": "account_type",
            "collapsible": 1
        },
        {
            "fieldname": "rgs_code",
            "label": "RGS Code",
            "fieldtype": "Data",
            "insert_after": "rgs_section",
            "read_only": 1,
            "description": "Reference Classification System code for Dutch financial reporting"
        },
        {
            "fieldname": "rgs_nivo",
            "label": "RGS Nivo",
            "fieldtype": "Int",
            "insert_after": "rgs_code",
            "read_only": 1,
            "description": "RGS hierarchy level (2-5)"
        },
        {
            "fieldname": "rgs_omslagcode",
            "label": "RGS Omslagcode",
            "fieldtype": "Data",
            "insert_after": "rgs_nivo",
            "read_only": 1,
            "description": "RGS code for linking debit and credit accounts"
        },
        {
            "fieldname": "column_break_rgs",
            "fieldtype": "Column Break",
            "insert_after": "rgs_omslagcode"
        },
        {
            "fieldname": "rgs_referentienummer",
            "label": "RGS Referentienummer",
            "fieldtype": "Data",
            "insert_after": "column_break_rgs",
            "read_only": 1,
            "description": "RGS reference number for official reporting"
        }
    ]
}

# Document Events
doc_events = {
    "Account": {
        "validate": "nl_erpnext_rgs_mkb.nl_erpnext_rgs_mkb.account_validation.validate_rgs_compliance"
    }
}

# Boot session
boot_session = "nl_erpnext_rgs_mkb.utils.boot_session"

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name", "in", [
                    "Account-rgs_section",
                    "Account-rgs_code", 
                    "Account-rgs_nivo",
                    "Account-rgs_omslagcode",
                    "Account-column_break_rgs",
                    "Account-rgs_referentienummer"
                ]
            ]
        ]
    }
]