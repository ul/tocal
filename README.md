# ToCal

A small script to automate adding tasks as events into your Google calendar.

## Getting started

- It's a Python script, and `make deps` will call `pip` to install its dependencies.
- You'll need a GCP project with Calendar API enabled and create OAuth 2.0 Client credentials: https://developers.google.com/workspace/guides/create-project
- Copy `client_secrets.example.json` to `client_secrets.json` and fill in `client_id` and `client_secret` from the previous step.
- Optionally configure your business hours and other hardcoded parameters in `main.py`.
- Optionally symlink `main.py` to somewhere in the `PATH` for a more convenient use.

## Usage

```
main.py +3 /60 Recompile the kernel
```

is interpreted by ToCal as "starting from 3 days in the future, within my business hours, find a free slot of 60 minutes and create an event 'Recompile the kernel'.
If there will be no suitable slot for 7 days then just book it during the business hours after the last event you checked while looking for a free spot."

Offset `+DAYS` is optional and is `1` by default (i.e. "starting from tomorrow").
Duration `/MINUTES` is optional and is `30` by default.
Business hours are hardcoded to be from 9am to 5pm.

Both default values, business hours and the search window could be changed by editing script code.
