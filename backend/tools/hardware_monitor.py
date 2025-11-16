"""
Hardware Monitor Tool
Monitor CPU, RAM, GPU, disk, network, temperature
"""
import psutil
from typing import Dict, Any
from loguru import logger

from core.tool_manager import BaseTool


class HardwareMonitorTool(BaseTool):
    """Hardware monitoring tool"""
    
    name = "hardware_monitor"
    description = "Monitor system hardware and resources"
    
    async def execute(self, metric: str = "all", **kwargs) -> Dict[str, Any]:
        """Execute hardware monitoring"""
        metrics = {
            "all": self.get_all_stats,
            "cpu": self.get_cpu_stats,
            "memory": self.get_memory_stats,
            "disk": self.get_disk_stats,
            "network": self.get_network_stats,
            "gpu": self.get_gpu_stats,
            "temperature": self.get_temperature,
            "battery": self.get_battery_stats,
            "processes": self.get_process_list
        }
        
        if metric not in metrics:
            return {
                "error": f"Unknown metric: {metric}",
                "available": list(metrics.keys())
            }
        
        try:
            result = await metrics[metric](**kwargs)
            return {
                "success": True,
                "metric": metric,
                "data": result
            }
        except Exception as e:
            logger.error(f"Hardware monitoring error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "metric": metric
            }
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Get all system statistics"""
        stats = {
            "cpu": await self.get_cpu_stats(),
            "memory": await self.get_memory_stats(),
            "disk": await self.get_disk_stats(),
            "network": await self.get_network_stats()
        }
        
        # Optional stats (may not be available)
        try:
            stats["gpu"] = await self.get_gpu_stats()
        except:
            stats["gpu"] = None
        
        try:
            stats["temperature"] = await self.get_temperature()
        except:
            stats["temperature"] = None
        
        try:
            stats["battery"] = await self.get_battery_stats()
        except:
            stats["battery"] = None
        
        return stats
    
    async def get_cpu_stats(self) -> Dict[str, Any]:
        """Get CPU statistics"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        return {
            "usage_percent": psutil.cpu_percent(interval=1),
            "per_cpu": cpu_percent,
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "frequency_mhz": {
                "current": cpu_freq.current if cpu_freq else None,
                "min": cpu_freq.min if cpu_freq else None,
                "max": cpu_freq.max if cpu_freq else None
            }
        }
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "virtual": {
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3),
                "used_gb": mem.used / (1024**3),
                "percent": mem.percent
            },
            "swap": {
                "total_gb": swap.total / (1024**3),
                "used_gb": swap.used / (1024**3),
                "percent": swap.percent
            }
        }
    
    async def get_disk_stats(self) -> Dict[str, Any]:
        """Get disk statistics"""
        partitions = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "percent": usage.percent
                })
            except PermissionError:
                continue
        
        disk_io = psutil.disk_io_counters()
        
        return {
            "partitions": partitions,
            "io": {
                "read_mb": disk_io.read_bytes / (1024**2) if disk_io else 0,
                "write_mb": disk_io.write_bytes / (1024**2) if disk_io else 0
            }
        }
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        
        interfaces = {}
        for interface, stats in psutil.net_io_counters(pernic=True).items():
            interfaces[interface] = {
                "sent_mb": stats.bytes_sent / (1024**2),
                "recv_mb": stats.bytes_recv / (1024**2),
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv
            }
        
        return {
            "total": {
                "sent_mb": net_io.bytes_sent / (1024**2),
                "recv_mb": net_io.bytes_recv / (1024**2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "interfaces": interfaces
        }
    
    async def get_gpu_stats(self) -> Dict[str, Any]:
        """Get GPU statistics"""
        gpus = []
        
        try:
            import GPUtil
            
            for gpu in GPUtil.getGPUs():
                gpus.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "load_percent": gpu.load * 100,
                    "memory_used_mb": gpu.memoryUsed,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_percent": (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
                    "temperature_c": gpu.temperature
                })
        except ImportError:
            # Try nvidia-ml-py3
            try:
                import pynvml
                
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    
                    gpus.append({
                        "id": i,
                        "name": name.decode() if isinstance(name, bytes) else name,
                        "load_percent": utilization.gpu,
                        "memory_used_mb": mem_info.used / (1024**2),
                        "memory_total_mb": mem_info.total / (1024**2),
                        "memory_percent": (mem_info.used / mem_info.total) * 100,
                        "temperature_c": temperature
                    })
                
                pynvml.nvmlShutdown()
            except:
                pass
        
        return {
            "gpus": gpus,
            "count": len(gpus)
        }
    
    async def get_temperature(self) -> Dict[str, Any]:
        """Get system temperature"""
        temps = {}
        
        try:
            if hasattr(psutil, "sensors_temperatures"):
                for name, entries in psutil.sensors_temperatures().items():
                    temps[name] = [
                        {
                            "label": entry.label or name,
                            "current": entry.current,
                            "high": entry.high,
                            "critical": entry.critical
                        }
                        for entry in entries
                    ]
        except:
            pass
        
        return temps
    
    async def get_battery_stats(self) -> Dict[str, Any]:
        """Get battery statistics"""
        if not hasattr(psutil, "sensors_battery"):
            return None
        
        battery = psutil.sensors_battery()
        
        if battery is None:
            return None
        
        return {
            "percent": battery.percent,
            "plugged": battery.power_plugged,
            "time_left_seconds": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
        }
    
    async def get_process_list(self, limit: int = 10) -> Dict[str, Any]:
        """Get list of top processes by CPU/memory"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda p: p['cpu_percent'] or 0, reverse=True)
        
        return {
            "processes": processes[:limit],
            "total": len(processes)
        }


# Standalone function for system API endpoint
async def get_system_info() -> Dict[str, Any]:
    """Get system information for API endpoint"""
    tool = HardwareMonitorTool()
    result = await tool.execute(metric="all")
    return result.get("data", {})

