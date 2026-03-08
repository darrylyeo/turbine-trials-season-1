FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install dotenvx binary (required for python-dotenvx decryption)
RUN apt-get update -qq && apt-get install -y -qq curl && rm -rf /var/lib/apt/lists/* \
	&& curl -sfS https://dotenvx.sh/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["dotenvx", "run", "--", "python", "-u", "main.py"]
