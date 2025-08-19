---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# Neighbor Engineers Messaging Server (Chip)

This service provides a FastAPI-based webhook and messaging abstraction layer for Loop Messaging (iMessage) with a pluggable adapter design to add providers like Twilio or WhatsApp. A lightweight agent stub is included; swap with DSPy+Groq in production.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)
## ✨ Features

- FastAPI
- [Hypercorn](https://hypercorn.readthedocs.io/)
- Python 3

## 💁‍♀️ How to use

- Clone locally and install packages with pip using `pip install -r requirements.txt`
- Run locally using `hypercorn main:app --reload`

### Environment

- `LOOP_API_BASE_URL` default: `https://server.loopmessage.com/api/v1`
- `LOOP_API_KEY` token for Loop outbound requests (Authorization)
- `LOOP_WEBHOOK_SECRET` optional inbound verification token
- `LOOP_SENDER_NAME` default sender email/name (e.g., `sender@example.com`)

## 🧪 Tests

Run tests:

```bash
pip install -r requirements.txt
pytest -q
```

The suite includes:
- Unit tests for adapters and normalization
- Contract tests against documented Loop webhook payload shapes
- Webhook end-to-end test using FastAPI `TestClient`


## 📝 Notes

- To learn about how to use FastAPI with most of its features, you can visit the [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)
- To learn about Hypercorn and how to configure it, read their [Documentation](https://hypercorn.readthedocs.io/)
