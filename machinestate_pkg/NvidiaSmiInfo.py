from .common import InfoGroup, ListInfoGroup, process_cmd, which, pjoin, pexists

################################################################################
# Infos from nvidia-smi (Nvidia GPUs)
################################################################################
class NvidiaSmiInfoClass(InfoGroup):
    '''Class to read information for one Nvidia GPU (uses the nvidia-smi command)'''
    def __init__(self, device, extended=False, anonymous=False, nvidia_path=""):
        super(NvidiaSmiInfoClass, self).__init__(name="Card{}".format(device),
                                                 extended=extended,
                                                 anonymous=anonymous)
        self.device = device
        self.nvidia_path = nvidia_path
        cmd = pjoin(nvidia_path, "nvidia-smi")
        if pexists(cmd):
            self.cmd = cmd
        elif which("nvidia-smi"):
            self.cmd = which("nvidia-smi")
        self.cmd_opts = "-q -i {}".format(device)
        abscmd = which(self.cmd)
        matches = {"ProductName" : r"\s+Product Name\s+:\s+(.+)",
                   "VBiosVersion" : r"\s+VBIOS Version\s+:\s+(.+)",
                   "ComputeMode" : r"\s+Compute Mode\s+:\s+(.+)",
                   "GPUCurrentTemp" : r"\s+GPU Current Temp\s+:\s+(\d+\sC)",
                   "MemTotal" : r"\s+Total\s+:\s+(\d+\sMiB)",
                   "MemFree" : r"\s+Free\s+:\s+(\d+\sMiB)",
                  }
        extmatches = {"PciDevice" : r"^GPU\s+([0-9a-fA-F:]+)",
                      "PciLinkWidth" : r"\s+Current\s+:\s+(\d+x)",
                      "GPUMaxOpTemp" : r"\s+GPU Max Operating Temp\s+:\s+(\d+\sC)",
                     }
        if abscmd:
            for key, regex in matches.items():
                self.addc(key, self.cmd, self.cmd_opts, regex)
            if extended:
                for key, regex in extmatches.items():
                    self.addc(key, self.cmd, self.cmd_opts, regex)

class NvidiaSmiInfo(ListInfoGroup):
    '''Class to spawn subclasses for each NVIDIA GPU device (uses the nvidia-smi command)'''
    def __init__(self, nvidia_path="", extended=False, anonymous=False):
        super(NvidiaSmiInfo, self).__init__(name="NvidiaInfo",
                                            extended=extended,
                                            anonymous=anonymous)
        self.nvidia_path = nvidia_path
        self.cmd = "nvidia-smi"
        cmd = pjoin(nvidia_path, "nvidia-smi")
        if pexists(cmd):
            self.cmd = cmd
        self.cmd_opts = "-q"
        abscmd = which(self.cmd)
        if abscmd:
            num_gpus = process_cmd((self.cmd, self.cmd_opts, r"Attached GPUs\s+:\s+(\d+)", int))
            if not isinstance(num_gpus, int):
                # command failed (because nvidia-smi is installed but non-functional)
                # don't add cmd to list
                return
            if num_gpus > 0:
                self.userlist = [i for i in range(num_gpus)]
                self.subclass = NvidiaSmiInfoClass
                self.subargs = {"nvidia_path" : nvidia_path}
        matches = {"DriverVersion" : r"Driver Version\s+:\s+([\d\.]+)",
                   "CudaVersion" : r"CUDA Version\s+:\s+([\d\.]+)",
                  }
        if abscmd:
            for key, regex in matches.items():
                self.addc(key, self.cmd, self.cmd_opts, regex)
