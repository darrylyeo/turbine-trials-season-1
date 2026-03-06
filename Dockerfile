FROM python:3.12-slim

WORKDIR /app

# Install dotenvx binary (required for python-dotenvx decryption)
RUN apt-get update -qq && apt-get install -y -qq curl && rm -rf /var/lib/apt/lists/* \
	&& curl -sfS https://dotenvx.sh/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# If .env exists (e.g. committed encrypted), use dotenvx to decrypt and run. Else use Railway Variables only.
CMD ["sh", "-c", "if [ -f .env ]; then exec dotenvx run -- python main.py; else exec python main.py; fi"]
