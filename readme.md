# Topfly Webhooks

# Steps

- Install packages in `requirements.txt` using `pip install -r requirements.txt` (use virtualenv for local development)
- Create `.env` file from `.env.example` and fill the variables
- Run the using the command `pytest` (for printing the logs, use flag `-s -v`)
- Run the application using `uvicorn main:app --reload`

Note: No need to set `SENTRY_DNS` in `env` for local development
