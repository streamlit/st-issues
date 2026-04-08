# gh-14209: WebSocket fails behind Istio VirtualService

## Summary

User reports WebSocket connection (`/_stcore/stream`) fails when deployed behind Istio VirtualService with `websocketUpgrade: true`. Additionally, localhost requests within the same pod become extremely slow despite low resource usage.

## Analysis

### Classification

This appears to be a **deployment configuration issue**, not a Streamlit code bug. The user is deploying behind a reverse proxy with a path prefix (`/prefix/path`), which is a known category of issues.

### Missing information

The issue is missing critical details:
- No `Steps To Reproduce` provided
- No `Current Behavior` description
- No Streamlit server configuration (especially `server.baseUrlPath`)
- No error messages or network traces (only screenshots showing failed requests)
- No CORS/XSRF configuration details

### Likely root cause

When deploying behind a reverse proxy with a path prefix:
1. `server.baseUrlPath` must be configured to match the Istio prefix path
2. CORS (`server.enableCORS`) and XSRF (`server.enableXsrfProtection`) settings may need adjustment
3. Istio's Envoy sidecar may strip WebSocket upgrade headers or misroute the request

The AI triage bot already identified this correctly and linked to related issues (#8188, #12108, #8901).

### Existing labels

Already has appropriate labels: `type:bug`, `area:network`, `area:deployment`

## Recommendation

Request more information before confirming as a bug. Key questions:
1. Is `server.baseUrlPath` configured?
2. What is the exact CORS/XSRF configuration?
3. What errors appear in the browser console/network tab?
4. Does adding `server.baseUrlPath = "/prefix/path"` resolve the issue?

## Classification

- **Type:** Needs more info (likely deployment configuration)
- **Priority:** P3 if bug, otherwise documentation/configuration issue
- **Status:** Request more info
