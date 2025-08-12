# stackoverflow-ingestion
Ingestion of relevant stackoverflow content for LLM training
## Running locally
```export SSM_OVERRIDE=true  
export RAW_OUTPUT_DIR="tmp"  
export STACKOVERFLOW_API_KEY="<your key>"  
export STACKOVERFLOW_API_URL="<your instance>"
export CONFLUENCE_API_URL="<your instance>"
export CONFLUENCE_API_TOKEN="<your key>"
export CERT_PATH="<path to your cert>"
```
need to update: `starting_pages` in handler.py as well as the call to `process_single_page`