import subprocess
import json
import psutil

def query_processors_accelerators_gpus():
    """
    Query macOS devices for Processor, Compute Accelerator (stub), and GPU info using system_profiler.
    Returns a dict with lists of device info for each class.
    """
    result = {"Processor": [], "ComputeAccelerator": [], "GPU": []}
    try:
        # Get CPU info
        cpu_info = subprocess.check_output([
            "sysctl", "-n", "machdep.cpu.brand_string"
        ]).decode().strip()
        result["Processor"].append({"Name": cpu_info, "Cores": psutil.cpu_count(logical=False), "Threads": psutil.cpu_count()})

        # Get GPU info via system_profiler
        gpu_json = subprocess.check_output([
            "system_profiler", "SPDisplaysDataType", "-json"
        ]).decode()
        gpu_data = json.loads(gpu_json)
        gpus = gpu_data.get("SPDisplaysDataType", [])
        for gpu in gpus:
            gpu_info = {
                "Name": gpu.get("_name", "Unknown GPU"),
                "Description": gpu.get("spdisplays_vendor", "Unknown Vendor"),
                "AdapterRAM_MB": int(gpu.get("spdisplays_vram_shared", "0 MB").split()[0]) if gpu.get("spdisplays_vram_shared") else None,
                "VideoProcessor": gpu.get("spdisplays_gpusubtype", "Unknown Processor"),
                "DriverVersion": gpu.get("spdisplays_rom_revision", "Unknown Version")
            }
            result["GPU"].append(gpu_info)
    except Exception:
        pass
    # There is currently no known "Compute Accelerator" detection for Mac: stub empty.
    return result

def query_system_ram():
    """
    Query the total system RAM on macOS.
    Returns the total RAM in GB.
    """
    try:
        ram_bytes = psutil.virtual_memory().total
        return round(ram_bytes / (1024 ** 3), 2)
    except Exception:
        return None
