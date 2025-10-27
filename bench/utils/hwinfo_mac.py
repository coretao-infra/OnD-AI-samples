import subprocess
import json
import psutil

def query_processors_accelerators_gpus():
    """
    Query macOS devices for Processor, Compute Accelerator (stub), and GPU info using system_profiler.
    Returns a dict with lists of device info for each class.
    """
    result = {"Processor": [], "ComputeAccelerator": [], "GPU": []}
    # CPU
    try:
        cpu_brand = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        result["Processor"].append({
            "Name": cpu_brand,
            "Cores": psutil.cpu_count(logical=False),
            "Threads": psutil.cpu_count(logical=True)
        })
    except Exception:
        pass
    # GPU
    try:
        gpu_json = subprocess.check_output(["system_profiler", "SPDisplaysDataType", "-json"]).decode()
        gdata = json.loads(gpu_json).get("SPDisplaysDataType", [])
        for g in gdata:
            result["GPU"].append({
                "Name": g.get("_name", "Unknown"),
                "Description": g.get("spdisplays_vendor", ""),
                "AdapterRAM_MB": int(g.get("spdisplays_vram_shared", "0 MB").split()[0]) if g.get("spdisplays_vram_shared") else None,
                "VideoProcessor": g.get("spdisplays_gpusubtype", ""),
                "DriverVersion": g.get("spdisplays_rom_revision", "")
            })
    except Exception:
        pass
    return result

def query_system_ram():
    """
    Query the total system RAM on macOS.
    Returns the total RAM in GB.
    """
    try:
        return round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        return None
