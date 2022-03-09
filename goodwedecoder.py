
def decode(payload):
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
        # "unknown_1": payload[36:38].hex(),
        "temperature": int.from_bytes(payload[38:40], "big") / 10,
        # "unknown_2": payload[40:44].hex(),
        "kwh_total": int.from_bytes(payload[44:48], "big") / 10,
        "hours_total": int.from_bytes(payload[48:52], "big"),
        # "unknown_3": payload[52:64].hex(),
        # "country": payload[63:64].hex(), # maybe?
        "kwh_daily": int.from_bytes(payload[64:66], "big") / 10,
    }
