
# Names from GoodWe's EzExplorer USB tool, which shows the same running-info record.
WORK_MODES = {
    0: "Wait",
    1: "Normal",
    2: "Fault",
    3: "Permanent Fault",
}

ERROR_BITS = {
    0: "GFCI Device Failure",
    1: "AC HCT Failure",
    2: "TBD",
    3: "DCI Consistency Failure",
    4: "GFCI Consistency Failure",
    9: "Utility Loss",
    10: "Ground I Failure",
    11: "DC Bus High",
    12: "Internal Fan Failure",
    13: "Over Temperature",
    14: "Auto Test Failure",
    15: "PV Over Voltage",
    16: "External Fan Failure",
    17: "Vac Failure",
    18: "Isolation Failure",
    19: "DC Injection High",
    22: "Fac Consistency Failure",
    23: "Vac Consistency Failure",
    25: "Relay Check Failure",
    29: "Fac Failure",
    30: "EEPROM R/W Failure",
    31: "Internal Communication Failure",
}


def decode_work_mode(mode):
    return WORK_MODES.get(mode, f"Unknown ({mode})")


def decode_errors(code):
    names = [
        ERROR_BITS.get(bit, f"Unknown bit {bit}")
        for bit in range(32)
        if code & (1 << bit)
    ]
    return ", ".join(names) if names else "None"


def decode_1phase(payload):
    if len(payload) != 66:
        raise ValueError
    work_mode = int.from_bytes(payload[36:38], "big")
    error_code = int.from_bytes(payload[40:44], "big")
    return {
        "device_id": payload[1:17].decode('ascii'),
        # "mode": payload[18:21].hex(),
        "voltage_pv1": int.from_bytes(payload[20:22], "big") / 10,
        "voltage_pv2": int.from_bytes(payload[22:24], "big") / 10,
        "current_pv1": int.from_bytes(payload[24:26], "big") / 10,
        "current_pv2": int.from_bytes(payload[26:28], "big") / 10,
        "voltage_ac": int.from_bytes(payload[28:30], "big") / 10,
        "current_ac": int.from_bytes(payload[30:32], "big") / 10,
        "freq_ac": int.from_bytes(payload[32:34], "big") / 100,
        "power_ac": int.from_bytes(payload[34:36], "big"),
        "work_mode": decode_work_mode(work_mode),
        "temperature": int.from_bytes(payload[38:40], "big") / 10,
        "error_code": error_code,
        "errors": decode_errors(error_code),
        "kwh_total": int.from_bytes(payload[44:48], "big") / 10,
        "hours_total": int.from_bytes(payload[48:52], "big"),
        # EzExplorer and GoodWeUSBLogger label 52:64 as values recorded at the last
        # fault, but on a GW3600-DS 52:56 look like flags, 56:60 stay zero and 62:64
        # alternates 0/20 between uploads. 60:62 follows PV voltage while waiting and
        # sits around 360 V while feeding in: the boost converter's DC bus.
        "voltage_bus": int.from_bytes(payload[60:62], "big") / 10,
        "kwh_daily": int.from_bytes(payload[64:66], "big") / 10,
    }
