# CRITICAL REALIGNMENT PLAN
## Dutch RGS MKB ERPNext App

**Date:** August 22, 2025  
**Status:** CRITICAL - Implementation Misaligned with Design Specification

## 🚨 CRITICAL GAPS IDENTIFIED

### 1. **Primary Key Architecture Violation**
**Problem:** DocType uses generic field names instead of official RGS field names
**Impact:** Complete misalignment with RGS 3.7 specification
**Solution:** Rebuild DocType with correct RGS field mapping

### 2. **Missing Three-Document Integration**
**Problem:** No integration with available source data files
**Impact:** Manual data entry instead of automated RGS compliance
**Solution:** Implement complete data processing pipeline

### 3. **ERPNext Integration Gaps**
**Problem:** Static field options without intelligent derivation
**Impact:** No automatic compliance, manual mapping required
**Solution:** Implement intelligent field derivation logic

## 📋 CORRECTIVE IMPLEMENTATION PLAN

### Phase 1: Foundation Correction (IMMEDIATE)
1. **Rebuild RGS Classification DocType with correct field mapping**
   - Use official RGS field names (rgsCode, rgsReknr, rgsOmskort)
   - Implement proper primary key structure
   - Add missing critical fields (rgsDc, rgsOmslag, concept_mappings)

2. **Create Source Data Processing Pipeline**
   - Process rgsmkb_all4EN.json (canonical data)
   - Integrate attributes.csv (field specifications)
   - Process labels.csv (translation concepts)

3. **Implement Intelligent ERPNext Field Derivation**
   - Auto-calculate report_type from rgsCode
   - Derive root_type from concept mappings
   - Map account_type using RGS patterns
   - Convert rgsDc to balance_must_be

### Phase 2: CoA Template Integration (NEXT)
1. **Process Entity-Specific Templates**
   - Load ZZP, BV, EZ, SVC templates from /opt/frappe_docker/rgs_mkb/
   - Create ERPNext Chart of Accounts Template integration
   - Implement template selection workflow

2. **Account DocType Enhancement**
   - Correct custom field mapping to use rgsCode as link
   - Auto-populate from RGS Classification master data
   - Implement RGS compliance validation

### Phase 3: User Experience Alignment (FINAL)
1. **Template Selection Workflow**
   - Company creation with RGS template selection
   - Entity-specific template filtering
   - Template customization with compliance validation

2. **RGS Browser and Navigation**
   - Tree view of RGS hierarchy
   - Search and filter functionality
   - Template building interface

## 🎯 SUCCESS CRITERIA REALIGNMENT

### Technical Foundation
- ✅ RGS Classification DocType matches official RGS 3.7 specification
- ✅ Three-document integration provides complete legal basis
- ✅ ERPNext fields auto-derived from RGS concepts
- ✅ Primary key uses rgsCode, UI shows rgsReknr + rgsOmskort

### User Experience  
- ✅ Company creation offers entity-specific RGS templates
- ✅ Template customization maintains RGS compliance
- ✅ Account creation auto-populates from RGS master data
- ✅ Reporting uses official RGS structure

### Performance & Scalability
- ✅ Fixture loading optimized for 1,598 RGS records
- ✅ Build-time processing eliminates runtime bottlenecks
- ✅ Redis caching for efficient queries
- ✅ Batch processing prevents memory issues

## 🔧 IMMEDIATE NEXT STEPS

1. **Stop current development** - Current implementation is misaligned
2. **Rebuild RGS Classification DocType** with correct field mapping
3. **Implement source data processing** pipeline
4. **Test with small dataset** before full fixture loading
5. **Validate against design specification** at each step

## 📊 IMPLEMENTATION PRIORITY

**Priority 1 (CRITICAL):** Correct DocType structure and field mapping
**Priority 2 (HIGH):** Three-document integration pipeline  
**Priority 3 (MEDIUM):** ERPNext intelligent field derivation
**Priority 4 (LOW):** User interface and template workflows

This realignment is CRITICAL for project success. All current development should stop until the foundation is corrected according to the design specification.
