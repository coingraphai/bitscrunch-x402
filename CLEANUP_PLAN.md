# Production Cleanup Plan

## Files to KEEP (Essential for Production)

### Backend (Required)
- backend/__init__.py
- backend/client.py (payment client)
- backend/facilitator_server.py (payment verification server)
- backend/protocol.py (x402 protocol logic)
- backend/resource_server.py (API endpoints server)
- backend/settlement.py (blockchain settlement)
- backend/verification.py (payment verification)

### Frontend (Required)
- frontend/__init__.py
- frontend/app_coingecko.py (main production app)

### Configuration (Required)
- .env (environment variables - DO NOT commit to git)
- .env.example (template for deployment)
- .gitignore
- requirements.txt (production dependencies)

### Scripts (Required)
- start_servers.sh (server startup script)

### Documentation (Keep minimal)
- README.md (main documentation)
- QUICKSTART.md (quick start guide)

## Files to REMOVE (Not needed in production)

### Unused Test Files
- test_client.py (development testing only)
- test_collection_analysis.py
- test_nft_valuation.py
- test_unleashnfts.py
- tests/ directory (unit tests not needed in production)

### Unused Frontend Files
- frontend/app.py (old version)
- frontend/app_coingecko.py.backup (backup)
- frontend/app_coingecko_backup.py (backup)
- frontend/app_full.py (old version)
- frontend/app_simple.py (old version)

### Debug/Development Scripts
- check_config.sh
- debug_signature.py
- query_usdc_domain.py
- setup.sh (only needed for initial setup)
- install_minimal.sh
- start.sh (replaced by start_servers.sh)
- start_all.sh (duplicate)
- stop_all.sh

### Redundant Documentation
- BITSCRUNCH_INTEGRATION.md
- COLLECTION_ANALYSIS_INTEGRATION.md
- EMOJI_REMOVAL_SUMMARY.md
- FIXES_APPLIED.md
- FRONTEND_GUIDE.md
- IMPLEMENTATION_COMPLETE.md
- INSTALLATION_SUCCESS.md
- PROJECT_SUMMARY.md
- UI_UPDATES.md

### Requirements
- requirements-minimal.txt (redundant)

### Virtual Environments (exclude from git, but keep locally)
- venv/ (old environment, not used)
- venv-py311/ (KEEP - used in production)
