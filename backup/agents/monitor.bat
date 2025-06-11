@echo off
gcloud alpha monitoring policies create --policy-from-file=alert_policy.json
pause