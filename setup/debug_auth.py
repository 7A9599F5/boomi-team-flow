#!/usr/bin/env python3
"""Diagnostic: test DataHub Repository API auth formats.

Run:  python -m setup.debug_auth
"""
import base64
import json
import os
import sys

import requests

# Load state
with open(".boomi-setup-state.json") as f:
    state = json.load(f)

cfg = state["config"]
account_id = cfg.get("boomi_account_id", "")
hub_token = cfg.get("datahub_token", "")
hub_url = cfg.get("hub_cloud_url", "")
hub_user = cfg.get("datahub_user", "")
universe_ids = cfg.get("universe_ids", {})

# Platform creds from env
boomi_user = os.environ.get("BOOMI_USER", "")
boomi_token = os.environ.get("BOOMI_TOKEN", "")

print("=== DataHub Auth Diagnostic ===")
print(f"account_id:    {'set (' + account_id[:8] + '..., ' + str(len(account_id)) + ' chars)' if account_id else 'MISSING'}")
print(f"hub_user:      {'set (' + hub_user[:8] + '..., ' + str(len(hub_user)) + ' chars)' if hub_user else 'MISSING (datahub_user in state)'}")
print(f"hub_token:     {'set (' + hub_token[:4] + '..., ' + str(len(hub_token)) + ' chars)' if hub_token else 'MISSING'}")
print(f"hub_url:       {hub_url or 'MISSING'}")
print(f"universe_ids:  {len(universe_ids)} models")
for name, uid in universe_ids.items():
    print(f"  {name}: {uid}")
print(f"boomi_user:    {'set' if boomi_user else 'MISSING (env BOOMI_USER)'}")
print(f"boomi_token:   {'set (' + str(len(boomi_token)) + ' chars)' if boomi_token else 'MISSING (env BOOMI_TOKEN)'}")

# Check for common token issues
if hub_token:
    issues = []
    if hub_token != hub_token.strip():
        issues.append("has leading/trailing whitespace")
    if any(ord(c) < 32 for c in hub_token):
        issues.append("contains control characters")
    if "\n" in hub_token or "\r" in hub_token:
        issues.append("contains newline characters")
    if issues:
        print(f"\n  WARNING: hub_token {', '.join(issues)}")

print()

if not hub_url:
    print("ERROR: hub_cloud_url is empty — run step 1.0 first")
    sys.exit(1)

# Pick a test URL
if universe_ids:
    model_name, uid = next(iter(universe_ids.items()))
    test_url = f"{hub_url}/mdm/universes/{uid}/records/query"
    test_data = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<RecordQueryRequest limit="1"/>'
    )
    print(f"Test URL: POST {test_url}")
    print(f"Universe: {model_name} ({uid})")
else:
    test_url = f"{hub_url}/mdm"
    test_data = None
    print(f"Test URL: GET {test_url}  (no universes yet)")

print()

# Auth formats to try (generated username first — this is the correct format)
formats = []

if hub_user and hub_token:
    raw0 = f"{hub_user}:{hub_token}"
    formats.append(("generatedUser:hubToken", raw0))

if account_id and hub_token:
    raw1 = f"{account_id}:{hub_token}"
    formats.append(("accountId:hubToken", raw1))

if boomi_user and boomi_token:
    raw2 = f"BOOMI_TOKEN.{boomi_user}:{boomi_token}"
    formats.append(("BOOMI_TOKEN.user:apiToken", raw2))

if boomi_user and hub_token:
    raw3 = f"BOOMI_TOKEN.{boomi_user}:{hub_token}"
    formats.append(("BOOMI_TOKEN.user:hubToken", raw3))

if account_id and boomi_token:
    raw4 = f"{account_id}:{boomi_token}"
    formats.append(("accountId:apiToken", raw4))

if not formats:
    print("ERROR: No credential combinations available to test")
    sys.exit(1)

print(f"Testing {len(formats)} auth format(s):\n")

for label, raw in formats:
    encoded = base64.b64encode(raw.encode()).decode()
    auth_header = f"Basic {encoded}"
    req_headers = {"Authorization": auth_header}
    method = "GET"
    if test_data:
        req_headers["Content-Type"] = "application/xml"
        resp = requests.post(test_url, data=test_data, headers=req_headers, timeout=15)
        method = "POST"
    else:
        resp = requests.get(test_url, headers=req_headers, timeout=15)

    status = resp.status_code
    marker = "OK" if status != 401 else "401 UNAUTHORIZED"
    print(f"  [{marker:>16s}]  {label:<30s}  -> HTTP {status}")
    # Always show response body — critical for diagnosing 401s
    body = resp.text[:500].strip() if resp.text else "(empty)"
    print(f"                    Response: {body}")
    # Print Postman/curl details
    print(f"                    Raw creds: {raw}")
    print(f"                    Auth header: {auth_header}")
    if test_data:
        inline_body = test_data.replace("\n", "")
        print(f"                    curl: curl -X POST '{test_url}' \\")
        print(f"                      -H 'Authorization: {auth_header}' \\")
        print(f"                      -H 'Content-Type: application/xml' \\")
        print(f"                      -d '{inline_body}'")
    else:
        print(f"                    curl: curl '{test_url}' \\")
        print(f"                      -H 'Authorization: {auth_header}'")
    print()

print("Any format showing non-401 = valid auth. Use that format in the code.")
