import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "goodwe_proxy_server"))

from goodwedecoder import decode_1phase, decode_errors  # noqa: E402

# Datalog upload captured from a GW3600-DS in 2023
CAPTURE = bytes.fromhex(
    "00" + b"13600DSU15600594".hex() + "01002e"
    "071c0513002f00170919002e138a04550001013900000000"
    "0002da2900007ffc00100000000000000e3900000023"
)


def test_decodes_capture():
    m = decode_1phase(CAPTURE)
    assert m["device_id"] == "13600DSU15600594"
    assert m["voltage_pv1"] == 182.0
    assert m["power_ac"] == 1109
    assert m["work_mode"] == "Normal"
    assert m["temperature"] == 31.3
    assert m["error_code"] == 0
    assert m["errors"] == "OK"
    assert m["kwh_total"] == 18692.1
    assert m["hours_total"] == 32764
    assert m["voltage_bus"] == 364.1
    assert m["kwh_daily"] == 3.5


def test_decodes_fault_frame():
    payload = bytearray(CAPTURE)
    payload[36:38] = (3).to_bytes(2, "big")
    payload[40:44] = ((1 << 9) | (1 << 18)).to_bytes(4, "big")
    m = decode_1phase(bytes(payload))
    assert m["work_mode"] == "Permanent Fault"
    assert m["error_code"] == 0x40200
    assert m["errors"] == "Utility Loss, Isolation Failure"


def test_unknown_values_stay_visible():
    payload = bytearray(CAPTURE)
    payload[36:38] = (7).to_bytes(2, "big")
    assert decode_1phase(bytes(payload))["work_mode"] == "Unknown (7)"
    assert decode_errors(1 << 5) == "Unknown bit 5"


def test_rejects_wrong_length():
    try:
        decode_1phase(CAPTURE[:-1])
    except ValueError:
        return
    raise AssertionError("expected ValueError")
