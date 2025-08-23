# RGS MKB Pre-Build Fixture Processing Strategy

## Problem Statement
Large RGS fixtures (1,598+ records) cause memory issues and slow installation during site creation. The current approach loads fixtures at runtime, creating performance bottlenecks.

## Solution Architecture
Leverage Docker's layered build system to pre-process RGS fixtures during image build, creating a "fixture-ready" image with pre-baked DocTypes and optimized data.

## Implementation Strategy

### Phase 1: Build-Time Fixture Processing
```dockerfile
# Add to images/custom/Containerfile after builder stage
FROM builder AS fixture-processor

USER frappe
WORKDIR /home/frappe/frappe-bench

# Create temporary site for fixture processing
RUN echo "Creating temporary build site for fixture processing..." && \
    export start=`date +%s` && \
    # Initialize database configuration
    echo '{"db_host": "localhost", "redis_cache": "redis://localhost:6379", "redis_queue": "redis://localhost:6379"}' > sites/common_site_config.json && \
    # Create temporary site with lightweight database
    bench new-site build-temp.local \
        --no-mariadb-socket \
        --admin-password=admin \
        --db-root-password=admin \
        --install-app=erpnext,nl_erpnext_rgs_mkb \
        --set-default && \
    echo "✅ Temporary site created for fixture processing"

# Process RGS fixtures in build environment
RUN echo "Processing RGS fixtures during build..." && \
    cd /home/frappe/frappe-bench && \
    # Enable fixture processing mode
    export FIXTURE_BUILD_MODE=1 && \
    # Convert large RGS datasets to optimized format
    bench --site build-temp.local execute nl_erpnext_rgs_mkb.utils.convert_rgs_fixtures_for_build && \
    # Pre-generate translation files
    bench --site build-temp.local execute nl_erpnext_rgs_mkb.utils.setup_rgs_translations && \
    # Export optimized fixtures
    bench --site build-temp.local export-fixtures --app nl_erpnext_rgs_mkb && \
    echo "✅ RGS fixtures processed and optimized"

# Clean up temporary site but preserve processed fixtures
RUN echo "Cleaning up temporary build site..." && \
    cd /home/frappe/frappe-bench && \
    # Remove temporary site database
    bench drop-site build-temp.local --force && \
    # Keep optimized fixtures and translations
    echo "✅ Build cleanup completed, optimized data preserved"

FROM base AS backend
USER frappe
COPY --from=fixture-processor --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench
```

### Phase 2: Runtime Optimization
```python
# nl_erpnext_rgs_mkb/utils.py - Build-time fixture processing

@frappe.whitelist()
def convert_rgs_fixtures_for_build():
    """
    Convert large RGS fixtures to optimized format during Docker build
    This runs in a temporary site and pre-processes data for production
    """
    import os
    import json
    
    if not os.getenv('FIXTURE_BUILD_MODE'):
        frappe.throw("This function only runs during Docker build")
    
    # Load raw RGS data
    canonical_path = '/opt/frappe/rgsmkb_all4EN.json'
    if not os.path.exists(canonical_path):
        # Build-time: Use app data instead
        canonical_path = frappe.get_app_path('nl_erpnext_rgs_mkb', 'data/rgsmkb_all4EN.json')
    
    with open(canonical_path) as f:
        raw_data = json.load(f)
    
    # Process in optimized batches
    optimized_fixtures = []
    batch_size = 100  # Smaller batches for build-time processing
    
    for i in range(0, len(raw_data), batch_size):
        batch = raw_data[i:i+batch_size]
        processed_batch = process_rgs_batch_for_build(batch)
        optimized_fixtures.extend(processed_batch)
        
        # Build-time progress indicator
        print(f"Processed {min(i+batch_size, len(raw_data))}/{len(raw_data)} RGS records")
    
    # Save optimized fixtures
    fixture_path = frappe.get_app_path('nl_erpnext_rgs_mkb', 'fixtures/rgs_classification_optimized.json')
    with open(fixture_path, 'w') as f:
        json.dump(optimized_fixtures, f, indent=2)
    
    frappe.db.commit()
    return len(optimized_fixtures)

def process_rgs_batch_for_build(batch):
    """Process RGS batch with build-time optimizations"""
    processed = []
    
    for record in batch:
        # Apply three-document integration
        rgs_code = record.get('rgsCode', '')
        if not rgs_code:
            continue
            
        # Pre-calculate ERPNext mappings
        erpnext_mappings = derive_erpnext_mappings_build_time(record)
        
        # Build optimized fixture record
        fixture = {
            "doctype": "RGS Classification", 
            "name": rgs_code,
            "rgs_code": rgs_code,
            "rgs_omskort": record.get('rgsOmskort', ''),
            "rgs_reknr": str(record.get('rgsReknr', '0')).zfill(5),
            # Pre-calculated ERPNext fields
            "erpnext_report_type": erpnext_mappings.get('report_type'),
            "erpnext_root_type": erpnext_mappings.get('root_type'),
            "erpnext_account_type": erpnext_mappings.get('account_type'),
            # Optimized for fast loading
            "build_optimized": True
        }
        processed.append(fixture)
    
    return processed

@frappe.whitelist() 
def setup_rgs_translations():
    """Generate translation files during build phase"""
    if not os.getenv('FIXTURE_BUILD_MODE'):
        frappe.throw("This function only runs during Docker build")
    
    # Process official translations during build
    csv_path = frappe.get_app_path('nl_erpnext_rgs_mkb', '20210913 RGS NL en EN labels.csv')
    
    # Generate optimized translation files
    translations_dir = frappe.get_app_path('nl_erpnext_rgs_mkb', 'translations')
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)
    
    # Build-time translation processing
    process_translations_for_build(csv_path, translations_dir)
    
    print("✅ RGS translations processed during build")
    return True
```

### Phase 3: Production Site Creation Enhancement
```yaml
# overrides/compose.create-site-rgs.yaml - Enhanced site creation for RGS
services:
  create-site-rgs:
    image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-rgs-optimized}
    restart: "no"
    command:
      - bash
      - -c
      - |
        wait-for-it -t 120 db:3306
        wait-for-it -t 120 redis-cache:6379
        wait-for-it -t 120 redis-queue:6379
        
        # Wait for configurator
        export start=`date +%s`
        until [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".db_host // empty"` ]] && \
              [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_cache // empty"` ]] && \
              [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_queue // empty"` ]]; do
          echo "Waiting for common_site_config.json..."
          sleep 5
          if (( `date +%s`-start > 120 )); then
            echo "ERROR: Configuration timeout"
            exit 1
          fi
        done
        
        echo "🏗️  Creating RGS-optimized site: ${SITE_NAME}"
        
        if [[ ! -d "sites/${SITE_NAME}" ]]; then
          # Get database password
          if [[ -f "/run/secrets/db_root_password" ]]; then
            DB_ROOT_PASSWORD=$(cat /run/secrets/db_root_password)
          elif [[ -n "${DB_ROOT_PASSWORD}" ]]; then
            echo "Using environment variable for database password"
          else
            echo "ERROR: No database password available"
            exit 1
          fi
          
          # Create site with pre-optimized RGS app
          echo "Creating site with optimized RGS fixtures..."
          bench new-site ${SITE_NAME} \
            --no-mariadb-socket \
            --admin-password=${ADMIN_PASSWORD} \
            --db-root-password=${DB_ROOT_PASSWORD} \
            --install-app=${INSTALL_APPS} \
            --set-default
          
          echo "🎯 Activating RGS optimizations..."
          
          # Enable optimized fixture loading
          bench --site ${SITE_NAME} set-config rgs_optimized_mode 1
          
          # Load pre-processed RGS fixtures (much faster)
          bench --site ${SITE_NAME} execute nl_erpnext_rgs_mkb.utils.load_optimized_rgs_fixtures
          
          # Activate translations
          bench --site ${SITE_NAME} execute nl_erpnext_rgs_mkb.utils.activate_rgs_translations
          
          echo "✅ RGS-optimized site ${SITE_NAME} created successfully!"
        else
          echo "✅ Site ${SITE_NAME} already exists"
        fi
    depends_on:
      - db
      - redis-cache  
      - redis-queue
      - configurator
    volumes:
      - sites:/home/frappe/frappe-bench/sites
      - logs:/home/frappe/frappe-bench/logs
    environment:
      SITE_NAME: ${SITE_NAME}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin}
      INSTALL_APPS: ${INSTALL_APPS:-erpnext,nl_erpnext_rgs_mkb}
      DB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-}
      RGS_OPTIMIZED_MODE: 1
    profiles:
      - create-site-rgs
```

### Phase 4: Docker Bake Configuration
```hcl
# Add to docker-bake.hcl
target "rgs-optimized" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/custom/Containerfile"
    target = "backend"
    tags = [
        "${REGISTRY_USER}/erpnext:rgs-optimized",
        "${REGISTRY_USER}/erpnext:rgs-mkb-latest"
    ]
    args = {
        # Include RGS data in build context
        RGS_DATA_PATH = "/opt/frappe_docker/rgs_mkb"
        ENABLE_RGS_BUILD_OPTIMIZATION = "1"
    }
}
```

## Benefits of This Approach

### 🚀 **Performance Gains**
- ✅ **Build-time processing**: Heavy fixture processing happens once during build
- ✅ **Optimized runtime**: Site creation uses pre-processed, lightweight fixtures  
- ✅ **Memory efficiency**: No large JSON parsing during site creation
- ✅ **Fast deployment**: Production sites start in seconds, not minutes

### 🏗️ **Architecture Advantages**
- ✅ **Separation of concerns**: Build complexity vs. runtime simplicity
- ✅ **Immutable infrastructure**: Fixtures baked into image, consistent deployments
- ✅ **Version compatibility**: RGS data version tied to image version
- ✅ **Rollback capability**: Easy to revert to previous RGS data version

### 🔧 **Operational Benefits**
- ✅ **Predictable deployments**: No runtime fixture surprises
- ✅ **Horizontal scaling**: Multiple sites share optimized image
- ✅ **CI/CD friendly**: Build once, deploy everywhere
- ✅ **Troubleshooting**: Clear separation between build and runtime issues

### 🌍 **Translation Integration**
- ✅ **Build-time translation processing**: 58,029 translations pre-processed
- ✅ **Runtime efficiency**: Translations ready for immediate use
- ✅ **Multilingual support**: Dutch/English built-in from day one

## Usage

```bash
# Build optimized RGS image
docker buildx bake rgs-optimized --set rgs-optimized.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# Deploy with optimized site creation
docker compose --profile create-site-rgs up -d

# Result: Fast, reliable RGS site creation with all fixtures pre-loaded
```

This approach transforms the RGS installation from a runtime challenge to a build-time optimization, providing much better production characteristics.
