# link-tastic

A custom home-automation bridge for meshtastic

## why?

it would be cool to control smart-home stuff without needing a phone.

## Setup

1. `cp config.example.yaml config.yaml`, fill in channel name + allowed node ids (psk optional)
2. `pip install -r requirements.txt`
3. plug in the node, `python bridge.py`

- pi: `sudo usermod -aG dialout $USER` first; port like `/dev/ttyUSB0`
- mac: no groups needed; auto-detect just works, or set `/dev/cu.usbmodemXXXX`

## Commands

for now,

`help` : list commands
`status` : returns server disk usage
`boom` : fires missile:D

Unknown senders get logged and ignored. Replies go out on the private channel only.

## Security

This system relies on a pre-configured private channel with a random 256-bit psk and a whitelist.
Mark a command `requires_confirmation=True` in `commands.py` to require double-confirmation with a `confirm` keyword.

## Future

home assistant integration, pkc-signed messages, whatever ideas might strike my head (or the comments) in the meantime:) 

## dev

`pip install -r requirements-dev.txt` once, then `make fmt` to format and `make check` to lint. ruff rules in `.ruff.toml`.
