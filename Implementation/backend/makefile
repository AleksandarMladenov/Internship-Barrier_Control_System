run:
	cd ops && docker compose --env-file ../.env up --build
down:
	cd ops && docker compose --env-file ../.env down -v
logs:
	cd ops && docker compose --env-file ../.env logs -f api
ps:
	cd ops && docker compose --env-file ../.env ps
migrate:
	cd ops && docker compose --env-file ../.env exec api alembic upgrade head
revision:
	cd ops && docker compose --env-file ../.env exec api alembic revision --autogenerate -m "$(m)"
psql:
	cd ops && docker compose --env-file ../.env exec db psql -U $$POSTGRES_USER -d $$POSTGRES_DB
