# Docker Build Configuration for Dutch RGS ERPNext

## Overview

This document describes the Docker build configurations used for creating ERPNext images with Dutch RGS 3.7 compliance support.

## Build Architecture

### Working Configuration Location
- **Primary Build:** `/opt/frappe_docker/images/rgs/`
- **Working Dockerfile:** `Containerfile.apps-json-version`
- **Build Config:** `docker-bake.hcl`
- **App Definition:** `apps.json`

### Build Command
```bash
cd /opt/frappe_docker/images/rgs
docker buildx bake -f docker-bake.hcl rgs
```

## Build Files

### 1. docker-bake.hcl
```hcl
target "rgs" {
  dockerfile = "Containerfile.apps-json-version"
  target = "production"
  tags = [
    "frappe/erpnext:rgs-3.7",
    "frappe/erpnext:rgs-latest"
  ]
  platforms = ["linux/amd64"]
}
```

### 2. apps.json
```json
[
  {
    "url": "https://github.com/erjeve/nl_erpnext_rgs_mkb",
    "branch": "main"
  }
]
```

### 3. Containerfile.apps-json-version (Working Build)
```dockerfile
# Multi-stage build for RGS ERPNext
FROM frappe/erpnext:latest AS builder

# Install dependencies
USER root
RUN apt-get update && apt-get install -y git

# Set up bench
USER frappe
WORKDIR /home/frappe/frappe-bench

# Copy apps configuration
COPY apps.json /tmp/apps.json

# Install RGS app
RUN for app in $(cat /tmp/apps.json | jq -r '.[].url'); do \
      bench get-app $app; \
    done

# Production stage
FROM frappe/erpnext:latest AS production

# Copy installed apps from builder
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench/apps/nl_erpnext_rgs_mkb /home/frappe/frappe-bench/apps/nl_erpnext_rgs_mkb

# Set locale for Dutch support
ENV LANG=nl_NL.UTF-8
ENV LC_ALL=nl_NL.UTF-8
ENV COUNTRY_CODE=NL
ENV RGS_VERSION=3.7

# Update apps.txt to include RGS app
RUN echo "nl_erpnext_rgs_mkb" >> /home/frappe/frappe-bench/sites/apps.txt
```

## Deployment Integration

### compose.yaml Override
```yaml
services:
  erpnext:
    image: frappe/erpnext:rgs-latest
    environment:
      - LANG=nl_NL.UTF-8
      - COUNTRY_CODE=NL
      - RGS_VERSION=3.7
```

### Site Installation
After container startup, install the app on your site:
```bash
# Enter the container
docker exec -it erpnext-container bash

# Install RGS app on site
bench --site your-site.local install-app nl_erpnext_rgs_mkb
```

## Verification

### Check Image Contents
```bash
# Verify app is available
docker run --rm frappe/erpnext:rgs-latest ls -la /home/frappe/frappe-bench/apps/

# Check apps.txt
docker run --rm frappe/erpnext:rgs-latest cat /home/frappe/frappe-bench/sites/apps.txt
```

### Expected Output
```
frappe
erpnext
nl_erpnext_rgs_mkb
```

## Alternative Build Methods (Documented)

### Method 1: APPS_JSON_BASE64 (Standard)
- Location: `/opt/frappe_docker/images/custom/`
- Method: Base64 encoded apps.json in environment variable
- Status: Compatible but requires different approach

### Method 2: Extension Layer (Experimental)
- File: `Containerfile.backup`
- Method: Layer on top of existing image
- Status: Issues with build context and dependencies

### Method 3: Script-based (Original)
- File: `Containerfile` (original)
- Method: Simple script execution
- Status: Missing dependencies, incomplete

## Troubleshooting

### Common Issues

1. **Build Context Problems**
   - Ensure `apps.json` is in the build context
   - Check `.dockerignore` doesn't exclude required files

2. **App Installation Failures**
   - Verify GitHub repository accessibility
   - Check branch existence (default: main)
   - Ensure git is available in builder stage

3. **Multi-stage Build Issues**
   - Verify COPY commands preserve ownership
   - Check file permissions in production stage
   - Ensure apps.txt is properly updated

### Debug Commands
```bash
# Build with debug output
docker buildx bake -f docker-bake.hcl rgs --progress=plain

# Inspect intermediate stages
docker buildx build --target=builder -t debug-builder .
docker run --rm -it debug-builder bash

# Check final image
docker run --rm -it frappe/erpnext:rgs-latest bash
```

## Maintenance

### Updating ERPNext Base
1. Update base image tag in Containerfile
2. Test build with new base
3. Verify RGS app compatibility
4. Update tags in docker-bake.hcl

### Updating RGS App
1. Update branch/tag in apps.json
2. Rebuild image
3. Test app installation
4. Update version tags

---

**Last Updated:** August 22, 2025  
**Working Build Confirmed:** frappe/erpnext:rgs-latest (ID: 441e72bc56a8)  
**Status:** Production Ready
