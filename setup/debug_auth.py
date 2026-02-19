#!/usr/bin/env python3
"""Diagnostic: test DataHub Repository API auth formats.

Run:  python -m setup.debug_auth
"""
import base64
import json
import sys

import requests

# Load state
with open(".boomi-setup-state.json") as f:
    state = json.load(f)

cfg = state["config"]
account_id = cfg.get("boomi_account_id", "")
hub_token = cfg.get("datahub_token", "")
hub_url = cfg.get("hub_cloud_url", "")
universe_ids = cfg.get("universe_ids", {})

# Also need platform creds from env
import os
boomi_user = os.environ.get("BOOMI_USER", "")
boomi_token = os.environ.get("BOOMI_TOKEN", "")

print("=== DataHub Auth Diagnostic ===")
print(f"account_id:    {'set (' + account_id[:8] + '...)' if account_id else 'MISSING'}")
print(f"hub_token:     {'set (' + str(len(hub_token)) + ' chars)' if hub_token else 'MISSING'}")
print(f"hub_url:       {hub_url or 'MISSING'}")
print(f"universe_ids:  {len(universe_ids)} models")
print(f"boomi_user:    {'set' if boomi_user else 'MISSING (env BOOMI_USER)'}")
print(f"boomi_token:   {'set' if boomi_token else 'MISSING (env BOOMI_TOKEN)'}")
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
        '<RecordQueryRequest limit="1">\n'
        '  <view><fieldId>RECORD_ID</fieldId></view>\n'
        '</RecordQueryRequest>'
    )
    print(f"Test URL: POST {test_url}")
    print(f"Universe: {model_name} ({uid[:12]}...)")
else:
    test_url = f"{hub_url}/mdm"
    test_data = None
    print(f"Test URL: GET {test_url}  (no universes yet)")

print()

# Auth formats to try
formats = []

if account_id and hub_token:
    # Format 1: accountId:hubAuthToken (per Boomi docs)
    raw1 = f"{account_id}:{hub_token}"
    formats.append(("accountId:hubToken", raw1))

if boomi_user and boomi_token:
    # Format 2: BOOMI_TOKEN.user:apiToken (Platform API format)
    raw2 = f"BOOMI_TOKEN.{boomi_user}:{boomi_token}"
    formats.append(("BOOMI_TOKEN.user:apiToken", raw2))

if boomi_user and hub_token:
    # Format 3: BOOMI_TOKEN.user:hubToken (hybrid)
    raw3 = f"BOOMI_TOKEN.{boomi_user}:{hub_token}"
    formats.append(("BOOMI_TOKEN.user:hubToken", raw3))

if account_id and boomi_token:
    # Format 4: accountId:apiToken (cross)
    raw4 = f"{account_id}:{boomi_token}"
    formats.append(("accountId:apiToken", raw4))

for label, raw in formats:
    encoded = base64.b64encode(raw.encode()).decode()
    headers = {"Authorization": f"Basic {encoded}"}
    if test_data:
        headers["Content-Type"] = "application/xml"
        resp = requests.post(test_url, data=test_data, headers=headers, timeout=15)
    else:
        resp = requests.get(test_url, headers=headers, timeout=15)

    status = resp.status_code
    marker = "OK" if status != 401 else "401 UNAUTHORIZED"
    print(f"  [{marker:>16s}]  {label:<30s}  -> HTTP {status}")
    if status != 401 and status < 500:
        print(f"                    Response: {resp.text[:200]}")

print()
print("Any format showing non-401 = valid auth. Use that format in the code.")
