# Run the whole pipeline: make all  (needs PostgreSQL, e.g. `docker compose up -d`)
export DBT_PROFILES_DIR := dbt_project

all: extract transform report

extract:      ## download sources and load raw layer (skips unchanged files)
	python scripts/extract_load.py

transform:    ## build staging + marts and run all data tests
	dbt source freshness --project-dir dbt_project
	dbt build --project-dir dbt_project

report:       ## charts + summary from the marts
	python scripts/report.py

test:         ## python unit/integration tests
	pytest -q

docs:         ## dbt lineage docs at http://localhost:8080
	dbt docs generate --project-dir dbt_project && dbt docs serve --project-dir dbt_project
