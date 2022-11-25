# Topfly Webhooks

# Steps

- Install packages in `requirements.txt` using `pip install -r requirements.txt` (use virtualenv for local development)
- Create `.env` file from `.env.example` and put the token (generated from `automation` user (under manager account)) in `Token` variables
- Run the using the command `pytest` (for printing the logs, use flag `-s -v`)
- Run the application using `uvicorn main:app --reload --host 0.0.0.0`

Note: No need to set `SENTRY_DNS` in `env` for local development