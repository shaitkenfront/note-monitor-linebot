# CLAUDE.md

This file provides guidance for Claude Code (claude.ai/code) to work with the code in this repository.

## Project Overview

This is a LINE Bot that retrieves follower counts from a specified URL on note.com. The Bot runs at scheduled times and returns the retrieved information.

## Architecture

This project has a modular architecture with AWS Lambda as the main entry point.

- **`lambda_function.py`**: The main AWS Lambda handler that processes LINE Webhook events
- **`app/line_handler.py`**: Handles LINE Bot Webhook validation, signature verification, and message replies.
- **Modules missing in `app/`:
- `note_scraper.py`: Retrieves specified information from note.com.

## Key Environment Variables

The following environment variables are required:
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot access token for sending messages
- `LINE_CHANNEL_SECRET`: LINE Bot channel secret for verifying the webhook signature
- `NOTE_URL`: URL to get the number of views (e.g. 'https://note.com/hekisaya')

## Development commands

This is a Python project that does not use package management files, so use standard Python commands.

```bash
# Run Lambda functions locally for testing
python lambda_function.py

# Run individual modules for testing
python -m app.line_handler
python -m app.note_scraper
````

## Core flow

1. AWS Lambda is launched by the trigger.
2. When triggered by an API Gateway trigger,
2.1. Check whether the received string matches the username rules of note.com (3-16 alphanumeric characters or underscores)
2.2. If it matches the username rules, save the LINE user ID and note.com username as a pair in DynamoDB
2.3. If the received event is an unfollow (block), delete the record associated with the corresponding LINE user ID from DynamoDB
3. When triggered by a time trigger, `note_scraper.get_dashboard_info_from_note()`:
3.1. Extract a list of LINE user IDs from DynamoDB
3.2. Get a list of note.com usernames for each extracted LINE user ID
3.3. Scrape the obtained note.com username by concatenating it with the URL "https://note.com/" to get the number of followers
3.4. Format the response.
3.5. Push notifications to LINE users

## Test

Run automated tests with pytest.

## Deploy

Deploy as an AWS Lambda function triggered by a scheduled event.