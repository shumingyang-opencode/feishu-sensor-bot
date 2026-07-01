"""TXT 設定檔生成與上傳。"""

import re
from feishu_client import upload_file_to_cloud


def generate_filename(params: dict) -> str:
    sensor = params.get("revision", params.get("sensor_name", "UNKNOWN"))
    w = params.get("resolution", {}).get("width", "0")
    h = params.get("resolution", {}).get("height", "0")
    fps = params.get("frame_rate_fps", "0")
    fmt = params.get("pixel_format", "UNKNOWN")
    iface = params.get("interface", {})
    lanes = iface.get("lanes", "")
    data_rate = iface.get("data_rate_mhz", "")
    interface_str = f"mipi{data_rate}" if data_rate else f"{lanes}lane"
    return f"{sensor}_{w}x{h}_{fps}fps_{fmt}_{interface_str}.txt"


def build_header(params: dict) -> str:
    res = params.get("resolution", {})
    iface = params.get("interface", {})
    lines = [
        ";TAG:0x10",
        ";",
        f";Sensor revision: {params.get('revision', '')}",
        f";Input clock frequency: {params.get('input_clock_mhz', '')}MHz",
        f";Image output size: {res.get('width', '')}x{res.get('height', '')}",
        f";Image crop size: {params.get('crop', '')}",
        f";Pixel data format: {params.get('pixel_format', '')}",
        f";Frame timing and frame rate: {params.get('frame_rate_fps', '')}fps",
        f";System clock frequency: {params.get('system_clock_mhz', '')}MHz",
        f";Output interface and data rate: {iface.get('lanes', '')}lane, {iface.get('data_rate_mhz', '')}MHz",
        f";Backend processor: {params.get('backend_processor', '')}",
        f";Embedded line: {params.get('embedded_line', '')}",
        f";FSIN: {params.get('fsin', '')}",
        f";Others: {params.get('others', '')}",
        f";Core Setting version info: {params.get('core_setting_version', '')}",
        ";",
    ]
    return "\n".join(lines)


def validate(content: str) -> list[str]:
    issues: list[str] = []
    if ";TAG:0x10" not in content:
        issues.append("Missing ;TAG:0x10 line")
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";"):
            continue
        if stripped.startswith("SL"):
            parts = stripped.split()
            if len(parts) != 2 or not parts[1].isdigit():
                issues.append(f"Invalid SL format: {line}")
        elif "\t" in line:
            issues.append(f"Tab found: {line}")
        else:
            parts = stripped.split()
            if len(parts) < 3:
                issues.append(f"Register write should have 3+ fields: {line.strip()}")
    return issues


def assemble_txt(params: dict, registers: str) -> str:
    header = build_header(params)
    reg_lines = registers.strip()
    if reg_lines.startswith("```"):
        reg_lines = reg_lines.split("\n", 1)[1]
        reg_lines = reg_lines.rsplit("```", 1)[0]
    reg_lines = reg_lines.strip()
    return f"{header}\n\n{reg_lines}"


def upload_txt(content: str, params: dict) -> str:
    filename = generate_filename(params)
    file_token = upload_file_to_cloud(filename, content.encode("utf-8"))
    return file_token
