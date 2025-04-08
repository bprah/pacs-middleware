#!/bin/bash

echo "Script should be run in the project root"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
