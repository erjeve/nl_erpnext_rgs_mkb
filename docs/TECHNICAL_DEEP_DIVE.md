# Technical Deep Dive - Data Loading Solutions
**Understanding why standard approaches failed and what works**

## The Core Problem: Tree DocTypes vs Standard Import

### Why `bench data-import` Failed

Frappe's `data-import` command is designed for **flat, independent records**, not hierarchical tree structures:

```python
# data-import assumes simple document creation:
doc = frappe.get_doc(csv_row_data)
doc.insert()  # ❌ Fails for tree doctypes
```

**Tree DocTypes require**:
- Parent documents exist before children
- `lft`/`rgt` values calculated via nested set model
- Tree rebuilding after all nodes inserted
- Proper transaction management for rollback

### Frappe's NestedSet Model

Tree doctypes inherit from `NestedSet` which provides:
```python
class NestedSet:
    lft = 0      # Left boundary
    rgt = 0      # Right boundary  
    old_parent   # Parent tracking
    
    def rebuild_tree()  # Recalculates lft/rgt
```

**Our RGS data**: 1,598 records in 4-level hierarchy require proper tree calculation.

## Solution Architecture

### ✅ Working Approach: Programmatic Tree Import

```python
def import_tree_data():
    # 1. Sort by hierarchy level (parents first)
    sorted_data = sorted(rgs_data, key=lambda x: x['rgs_nivo'])
    
    # 2. Import level by level  
    for level in [1, 2, 3, 4]:
        level_records = filter_by_level(sorted_data, level)
        for record in level_records:
            doc = frappe.get_doc(record)
            doc.insert()  # ✅ Parents exist, works correctly
    
    # 3. Rebuild tree structure
    frappe.get_doc("RGS Classification").rebuild_tree()
```

### Why This Works

1. **Dependency Order**: Parents created before children
2. **Proper Validation**: Uses Frappe's document validation
3. **Tree Calculation**: `rebuild_tree()` handles lft/rgt values
4. **Transaction Safety**: Rollback possible if errors occur

## Data Format Analysis

### Original JSON Structure (Enhanced)
```json
{
  "doctype": "RGS Classification",
  "rgs_code": "10000",
  "rgs_description": "Immateriële vaste activa",
  "rgs_nivo": 2,                           # String → Int conversion needed
  "parent_rgs_classification": "1",        # Parent reference
  "is_group": true,                        # Boolean → Check field
  "account_type": "Asset"                  # ERPNext integration
}
```

### DocType Field Definitions
```json
{
  "fieldname": "rgs_nivo",
  "fieldtype": "Int",        # ← Requires integer conversion
  "reqd": 1
},
{
  "fieldname": "is_group", 
  "fieldtype": "Check",      # ← Boolean field
  "label": "Is Group"
}
```

## Error Analysis & Solutions

### Error 1: AttributeError 'lft' missing
```
AttributeError: 'RGSClassification' object has no attribute 'lft'
```
**Cause**: Fixture loading bypasses NestedSet initialization  
**Solution**: Use programmatic creation with proper document flow

### Error 2: String vs Int comparison
```
TypeError: '<' not supported between instances of 'str' and 'int'
```
**Cause**: JSON strings not converted to expected field types  
**Solution**: Explicit type conversion before document creation

### Error 3: data-import NoneType error
```
TypeError: '<' not supported between instances of 'int' and 'NoneType'
```
**Cause**: data-import bug with complex doctypes  
**Solution**: Use custom import logic, not data-import command

## Implementation Patterns

### Pattern 1: Migration Patch (Recommended)
```python
# File: patches/v1_0/import_rgs_data.py
def execute():
    if frappe.db.count("RGS Classification") > 0:
        return  # Already imported
    
    import_rgs_tree_data()
```

**Benefits**: 
- Runs automatically on `bench migrate`
- Version controlled
- Idempotent (can run multiple times safely)

### Pattern 2: Management Command
```python
# File: commands/import_rgs.py
@click.command()
def import_rgs():
    import_rgs_tree_data()
```

**Benefits**:
- Manual control over execution
- Can be run independently
- Good for testing/development

### Pattern 3: Fixture Override
```python
# In hooks.py
def before_install():
    # Import data programmatically instead of using fixtures
    pass
```

## Performance Considerations

### Large Dataset Handling
- **1,598 records**: Process in batches of 100
- **Memory usage**: Commit periodically to avoid memory issues  
- **Rollback strategy**: Transaction management for error recovery

### Tree Rebuilding Cost
- `rebuild_tree()` is O(n) operation
- Run once after all imports complete
- Monitor for performance with larger datasets

## Testing Strategy

### Validation Steps
1. **Count verification**: `frappe.db.count("RGS Classification") == 1598`
2. **Tree integrity**: Check parent-child relationships
3. **Field types**: Verify `rgs_nivo` as int, `is_group` as boolean
4. **Tree navigation**: UI tree view works correctly
5. **Custom fields**: Chart of Accounts integration functional

### Error Recovery
```python
try:
    import_rgs_tree_data()
    frappe.db.commit()
except Exception as e:
    frappe.db.rollback()
    frappe.log_error(f"RGS import failed: {e}")
```

---

**Key Insight**: Standard Frappe data import tools are not designed for complex hierarchical structures. Custom programmatic import with proper tree handling is the correct solution.
