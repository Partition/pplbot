# Simple setup

## Install dependencies
In the project directory, run:
```bash
pip install -r requirements.txt
```

## Set up database
Create a new database and user in postgres and update the .env file with the correct credentials.
https://youtu.be/KuQUNHCeKCk

## Set up environment variables
Create a `.env` file in the root of the project with the following variables:
```bash
DB_USER=<your_database_user>
DB_PASSWORD=<your_database_password>
DB_HOST=<your_database_host>
DB_PORT=<your_database_port>
DB_NAME=<your_database_name>
BOT_TOKEN=<your_discord_bot_token>
BOT_READY_CHANNEL_ID=<your_discord_channel_id>
```

## Running the bot
then run (or play button in IDE):
```bash
python bot.py
```

Enjoy!