#!/usr/bin/env python3
"""
Convert RGS 3.7 Classification Data to ERPNext CoA Template Format
Creates a standardized ERPNext Chart of Accounts template for Netherlands
"""

import json
from collections import defaultdict

def convert_rgs_to_erpnext_coa():
    """
    Convert flat RGS data to hierarchical ERPNext CoA template
    """
    
    print("🔄 Converting RGS 3.7 to ERPNext CoA Template format...")
    
    # Load RGS data
    try:
        with open('nl_erpnext_rgs_mkb/fixtures/rgs_classification.json.disabled', 'r') as f:
            rgs_data = json.load(f)
    except FileNotFoundError:
        print("❌ RGS fixture file not found")
        return None
    
    print(f"📊 Loaded {len(rgs_data)} RGS records")
    
    # Create lookup dictionaries
    rgs_by_code = {item['rgs_code']: item for item in rgs_data}
    children_by_parent = defaultdict(list)
    
    # Build parent-child relationships
    for item in rgs_data:
        parent = item.get('parent_rgs_classification')
        if parent:
            children_by_parent[parent].append(item['rgs_code'])
        else:
            children_by_parent[None].append(item['rgs_code'])
    
    def build_tree(parent_code=None):
        """Recursively build ERPNext tree structure"""
        tree = {}
        
        for child_code in children_by_parent.get(parent_code, []):
            child = rgs_by_code[child_code]
            
            # Prepare account properties (mirror ERPNext account creation)
            account_props = {}
            
            # Add account number (RGS code)
            account_props['account_number'] = child['rgs_code']
            
            # Add RGS-specific fields (ignored by standard ERPNext, used by RGS app)
            account_props['rgs_code'] = child['rgs_code']
            account_props['rgs_description'] = child.get('rgs_omskort', '')  # Use correct field
            account_props['rgs_nivo'] = int(child.get('rgs_nivo', 1))  # Convert string to int
            account_props['rgs_status'] = child.get('rgs_status', 'A')
            account_props['rgs_version'] = child.get('rgs_version', '3.7')
            
            # Add RGS applicability fields (convert Y/N to boolean-like for ERPNext)
            if child.get('rgs_zzp'):
                account_props['applicable_zzp'] = child['rgs_zzp']
            if child.get('rgs_ez'):
                account_props['applicable_ez'] = child['rgs_ez']  
            if child.get('rgs_bv'):
                account_props['applicable_bv'] = child['rgs_bv']
            if child.get('rgs_svc'):
                account_props['applicable_svc'] = child['rgs_svc']
            
            # Add reference fields if present
            if child.get('rgs_reknr'):
                account_props['rgs_reference_number'] = child['rgs_reknr']
            
            # Add account type mapping
            if child.get('account_type'):
                account_props['account_type'] = child['account_type']
            
            # Mark as group if it has children (convert to ERPNext format)
            if child_code in children_by_parent:
                account_props['is_group'] = 1  # ERPNext uses 1/0 not true/false
            
            # Add root type for top-level accounts
            if parent_code is None:
                # Map RGS to ERPNext root types based on RGS code patterns
                if child['rgs_code'].startswith('1'):
                    account_props['root_type'] = 'Asset'
                elif child['rgs_code'].startswith('2'):
                    account_props['root_type'] = 'Liability'  
                elif child['rgs_code'].startswith('3'):
                    account_props['root_type'] = 'Equity'
                elif child['rgs_code'].startswith('4'):
                    account_props['root_type'] = 'Expense'
                elif child['rgs_code'].startswith('8'):
                    account_props['root_type'] = 'Income'
                else:
                    account_props['root_type'] = 'Asset'  # Default
            
            # Build subtree
            subtree = build_tree(child_code)
            if subtree:
                account_props.update(subtree)
            
            # Use description as account name
            account_name = child.get('rgs_omskort', child['rgs_code'])  # Use Dutch description
            tree[account_name] = account_props
        
        return tree
    
    # Build the complete CoA template
    coa_template = {
        "country_code": "nl",
        "name": "Netherlands - RGS 3.7 Chart of Accounts",
        "tree": build_tree()
    }
    
    return coa_template

def save_coa_template():
    """Save the converted CoA template"""
    
    coa = convert_rgs_to_erpnext_coa()
    if not coa:
        return False
    
    # Save as ERPNext template
    output_file = 'nl_rgs_chart_of_accounts.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(coa, f, indent=4, ensure_ascii=False)
    
    print(f"✅ ERPNext CoA template saved: {output_file}")
    print(f"📊 Template contains {len(coa['tree'])} root accounts")
    
    # Count total accounts
    def count_accounts(tree):
        count = 0
        for key, value in tree.items():
            if isinstance(value, dict):
                count += 1
                # Count nested accounts (exclude metadata keys)
                for subkey, subvalue in value.items():
                    if subkey not in ['account_number', 'account_type', 'is_group', 'root_type'] and isinstance(subvalue, dict):
                        count += count_accounts({subkey: subvalue})
        return count
    
    total_accounts = count_accounts(coa['tree'])
    print(f"📈 Total accounts in template: {total_accounts}")
    
    return True

if __name__ == '__main__':
    save_coa_template()
