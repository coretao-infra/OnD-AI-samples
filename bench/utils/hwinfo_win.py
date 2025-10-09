import wmi

def query_processors_accelerators_gpus():
    """
    Query Windows devices for Processor, Compute Accelerator, and GPU using WMI.
    Returns a dict with lists of device info for each class.
    """
    c = wmi.WMI()
    result = {"Processor": [], "ComputeAccelerator": [], "GPU": []}
    for cpu in c.Win32_Processor():
        result["Processor"].append({"Name": cpu.Name, "Cores": cpu.NumberOfCores, "Threads": cpu.NumberOfLogicalProcessors})
    for dev in c.Win32_PnPEntity():
        pnp_class = getattr(dev, 'PNPClass', None)
        if pnp_class == "ComputeAccelerator" or (
            "Accelerator" in (dev.Name or "") or "Accelerator" in (dev.Description or "") or "NPU" in (dev.Name or "") or "NPU" in (dev.Description or "")
        ):
            result["ComputeAccelerator"].append({
                "Name": dev.Name,
                "Description": dev.Description,
                "Manufacturer": getattr(dev, 'Manufacturer', None),
                "Status": getattr(dev, 'Status', None),
                "DeviceID": getattr(dev, 'DeviceID', None)
            })
    for gpu in c.Win32_VideoController():
        gpu_info = {
            "Name": gpu.Name,
            "Description": gpu.Description,
            "AdapterRAM_MB": int(gpu.AdapterRAM) // (1024*1024) if gpu.AdapterRAM else None,
            "VideoProcessor": gpu.VideoProcessor,
            "DriverVersion": gpu.DriverVersion
        }
        result["GPU"].append(gpu_info)
    return result

def query_system_ram():
    """
    Query the total system RAM using WMI.
    Returns the total RAM in GB.
    """
    c = wmi.WMI()
    for comp in c.Win32_ComputerSystem():
        total_ram_bytes = getattr(comp, 'TotalPhysicalMemory', None)
        if total_ram_bytes:
            return round(int(total_ram_bytes) / (1024 ** 3), 2)  # Convert bytes to GB
    return None
