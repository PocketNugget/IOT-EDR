"""
Restore any quarantined Smart Home device back to normal operation.

Usage:
    python 00_restore_device.py                          → interactive menu
    python 00_restore_device.py roomba_main              → restore specific device
    python 00_restore_device.py all                      → restore ALL devices
"""
import json
import sys
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "localhost"
PORT   = 1883

ALL_DEVICES = [
    "bulb_living_room",
    "bulb_kitchen",
    "bulb_bedroom1",
    "bulb_bedroom2",
    "bulb_bathroom",
    "bulb_porch",
    "switch_main_door",
    "switch_garage",
    "hub_central",
    "roomba_main",
    "sprinkler_garden",
]

def restore(device_ids: list[str]):
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="edr_restore_tool")
    try:
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print(f"[-] Cannot connect to Mosquitto on {BROKER}:{PORT} — {e}")
        print("[!] Make sure the Docker stack is running: docker-compose up -d")
        return

    for dev in device_ids:
        client.publish(f"home/control/{dev}", json.dumps({"action": "restore"}))
        print(f"[+] ✅ Restore command sent → {dev}")

    client.disconnect()
    print("\n[*] All restore commands dispatched. Check the SOC Dashboard at http://localhost:3002")


def main():
    if len(sys.argv) > 1:
        target = sys.argv[1].strip().lower()
        if target == "all":
            print("🔄 Restoring ALL smart home devices...\n")
            restore(ALL_DEVICES)
        else:
            if target not in ALL_DEVICES:
                print(f"[-] Unknown device '{target}'. Available devices:")
                for d in ALL_DEVICES:
                    print(f"    • {d}")
                sys.exit(1)
            restore([target])
    else:
        print("┌─────────────────────────────────────────────────────┐")
        print("│   Smart Home EDR — Device Restore Tool              │")
        print("└─────────────────────────────────────────────────────┘")
        print()
        for i, dev in enumerate(ALL_DEVICES, 1):
            print(f"  [{i:2d}] {dev}")
        print(f"  [ 0] Restore ALL devices")
        print()

        choice = input("Select device to restore (0–11): ").strip()
        if choice == "0":
            restore(ALL_DEVICES)
        elif choice.isdigit() and 1 <= int(choice) <= len(ALL_DEVICES):
            restore([ALL_DEVICES[int(choice) - 1]])
        else:
            print("[-] Invalid selection.")


if __name__ == "__main__":
    main()
