import argparse
import logging
import sys
import time
from pathlib import Path

import yaml
from meshtastic import BROADCAST_ADDR
from meshtastic.protobuf import channel_pb2
from meshtastic.serial_interface import SerialInterface
from meshtastic.util import fromPSK, pskToString
from pubsub import pub

from commands import run_command

log = logging.getLogger("linktastic")

DEFAULT_CONFIG = Path(__file__).with_name("config.yaml")
REPLY_MAX = 200  # LoRa caps text around 237 bytes, leave breathing room


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f) or {}


def fmt_id(num: int) -> str:
    return f"!{num:08x}"


def find_channel(interface, name: str):
    ch = interface.localNode.getChannelByName(name)
    if ch is None:
        sys.exit(f"no channel named '{name}' on this node")
    if ch.role == channel_pb2.Channel.Role.DISABLED:
        sys.exit(f"channel '{name}' is disabled")
    return ch


def verify_psk(ch, psk_hex):
    if not psk_hex:
        return
    if ch.settings.psk != fromPSK(psk_hex):
        sys.exit("psk mismatch: node key differs from config")


def short_name(interface, node_id: str) -> str:
    node = interface.nodes.get(node_id, {})
    return node.get("user", {}).get("shortName") or node_id


def make_handler(cfg, chan):
    allowed = {i.lower() for i in cfg["allowed_ids"]}

    def on_receive(packet, interface):
        # only care about text on our private channel
        if packet.get("channel") != chan.index:
            return
        if packet["from"] == interface.myInfo.my_node_num:
            return  # our own echo
        from_id = fmt_id(packet["from"])
        if from_id.lower() not in allowed:
            log.warning("ignored msg from %s (not allowed)", from_id)
            return
        decoded = packet.get("decoded") or {}
        if decoded.get("portnum") != "TEXT_MESSAGE_APP":
            return
        text = decoded.get("text", "")
        log.info("%s: %s", from_id, text)
        reply = run_command(text, sender=from_id)
        if reply:
            reply = f"{short_name(interface, from_id)}: {reply}"[:REPLY_MAX]
            try:
                interface.sendText(reply, destinationId=BROADCAST_ADDR, channelIndex=chan.index)
            except Exception:
                log.exception("reply failed")

    return on_receive


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="config path")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    cfg = load_config(Path(args.config))
    if not cfg.get("channel_name"):
        sys.exit("config: channel_name required")
    if not cfg.get("allowed_ids"):
        sys.exit("config: allowed_ids required (your client's !nodeid)")

    interface = SerialInterface(devPath=cfg.get("port") or None)
    interface.waitForConfig()

    chan = find_channel(interface, cfg["channel_name"])
    verify_psk(chan, cfg.get("psk_hex"))
    log.info(
        "listening on '%s' (index %d, %s)",
        cfg["channel_name"],
        chan.index,
        pskToString(chan.settings.psk),
    )

    pub.subscribe(make_handler(cfg, chan), "meshtastic.receive")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        interface.close()


if __name__ == "__main__":
    main()
