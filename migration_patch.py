#!/usr/bin/env python3
"""
Migration patch to import RGS Classifications using ERPNext pattern
This will be executed as a proper Frappe migration
"""

import json
import frappe
from frappe.utils.nestedset import rebuild_tree

def execute():
    """
    Import RGS Classifications using ERPNext's proven tree pattern
    Called by Frappe migration system
    """
    
    print("🌲 Starting RGS Classification Migration (ERPNext Pattern)")
    
    # Check if already imported
    existing_count = frappe.db.count("RGS Classification")
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing RGS records. Skipping import.")
        return
    
    # Load the RGS fixture data
    import os
    fixture_path = os.path.join(
        frappe.get_app_path("nl_erpnext_rgs_mkb"), 
        "fixtures", 
        "rgs_classification.json.disabled"
    )
    
    try:
        with open(fixture_path, 'r') as f:
            rgs_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ RGS fixture file not found at: {fixture_path}")
        return
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    if not rgs_data:
        print("❌ No RGS data found")
        return
        
    print(f"📊 Found {len(rgs_data)} RGS records to import")
    
    # ✅ CRITICAL: Follow ERPNext pattern exactly
    # Disable NestedSet tree validation during creation
    frappe.local.flags.ignore_update_nsm = True
    
    try:
        # Sort by hierarchy level (parents must be created first)
        rgs_data_sorted = sorted(rgs_data, key=lambda x: int(x.get('rgs_nivo', 1)))
        
        created_count = 0
        errors = []
        
        # Create documents level by level (like ERPNext _import_accounts)
        for level in range(1, 5):  # RGS has 4 levels
            level_records = [r for r in rgs_data_sorted if int(r.get('rgs_nivo', 1)) == level]
            
            if not level_records:
                continue
                
            print(f"📝 Processing Level {level}: {len(level_records)} records")
            
            for record in level_records:
                try:
                    # Prepare document data (mirror ERPNext account creation)
                    doc_data = {
                        'doctype': 'RGS Classification',
                        'rgs_code': record['rgs_code'],
                        'rgs_description': record.get('rgs_omskort', ''),  # Use correct field name
                        'rgs_description_en': record.get('rgs_description_en', ''),
                        'rgs_nivo': int(record.get('rgs_nivo', 1)),  # Convert string to int
                        'is_group': 1 if record.get('is_group') else 0,  # Ensure int type
                        'rgs_status': record.get('rgs_status', 'A'),
                        'rgs_version': record.get('rgs_version', '3.7')
                    }
                    
                    # Add parent relationship if exists
                    if record.get('parent_rgs_classification'):
                        doc_data['parent_rgs_classification'] = record['parent_rgs_classification']
                    
                    # Add optional fields with type conversion
                    optional_fields = [
                        'account_type', 'balance_must_be', 'rgs_branch', 
                        'rgs_reknr', 'rgs_zzp', 'rgs_ez', 'rgs_bv', 'rgs_svc'  # Updated field names
                    ]
                    
                    for field in optional_fields:
                        if record.get(field):
                            doc_data[field] = record[field]
                    
                    # Create document (like ERPNext)
                    doc = frappe.get_doc(doc_data)
                    
                    # Set flags like ERPNext does
                    doc.flags.ignore_permissions = True
                    doc.flags.ignore_mandatory = True
                    
                    # Insert document
                    doc.insert()
                    
                    created_count += 1
                    
                    if created_count % 100 == 0:
                        print(f"  ✅ Created {created_count} records...")
                        frappe.db.commit()
                
                except Exception as e:
                    error_msg = f"Failed to create {record.get('rgs_code', 'UNKNOWN')}: {str(e)}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
        
        # Commit all document creation
        frappe.db.commit()
        
        # ✅ CRITICAL: Rebuild tree structure (like ERPNext)
        print("🔨 Rebuilding RGS tree structure...")
        rebuild_tree("RGS Classification", "parent_rgs_classification")
        frappe.db.commit()
        
        print(f"🎉 Migration Complete!")
        print(f"   ✅ Successfully created: {created_count} records")
        if errors:
            print(f"   ❌ Errors encountered: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
                
    except Exception as e:
        print(f"💥 Critical error during migration: {e}")
        frappe.db.rollback()
        raise
        
    finally:
        # ✅ CRITICAL: Re-enable tree validation (like ERPNext)
        frappe.local.flags.ignore_update_nsm = False
