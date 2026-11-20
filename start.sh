#!/bin/bash
set -e

echo "Ensuring Playwright browsers are installed..."
playwright install chromium

echo "Starting gunicorn server..."
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300
