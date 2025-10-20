from .common import InfoGroup, ListInfoGroup, process_cmd, which, pjoin, pexists, tostrlist, tointlist, re, MultiClassInfoGroup

################################################################################
# Infos from clinfo (OpenCL devices and runtime)
################################################################################
class OpenCLInfoPlatformDeviceClass(InfoGroup):
    '''Class to read information for one OpenCL device in one platform(uses the clinfo command)'''
    def __init__(self, device, suffix, extended=False, anonymous=False, clinfo_path=""):
        super(OpenCLInfoPlatformDeviceClass, self).__init__(extended=extended, anonymous=anonymous)
        self.device = device
        self.suffix = suffix
        self.clinfo_path = clinfo_path
        clcmd = pjoin(clinfo_path, "clinfo")
        if not pexists(clcmd):
            clcmd = which("clinfo")
        if clcmd and len(clcmd) > 0:
            cmdopts = "--raw --offline | grep '[{}/{}]'".format(self.suffix, self.device)
            self.name = process_cmd((clcmd, cmdopts, r"CL_DEVICE_NAME\s+(.+)", str))
            self.const("Name", self.name)
            self.addc("ImagePitchAlignment", clcmd, cmdopts, r"CL_DEVICE_IMAGE_PITCH_ALIGNMENT\s+(\d+)", int)
            self.addc("Vendor", clcmd, cmdopts, r"CL_DEVICE_VENDOR\s+(.+)", str)
            self.addc("DriverVersion", clcmd, cmdopts, r"CL_DRIVER_VERSION\s+(.+)", str)
            self.addc("VendorId", clcmd, cmdopts, r"CL_DEVICE_VENDOR_ID\s+(.+)", str)
            self.addc("OpenCLVersion", clcmd, cmdopts, r"CL_DEVICE_OPENCL_C_VERSION\s+(.+)", str)
            self.addc("Type", clcmd, cmdopts, r"CL_DEVICE_TYPE\s+(.+)", str)
            self.addc("MaxComputeUnits", clcmd, cmdopts, r"CL_DEVICE_MAX_COMPUTE_UNITS\s+(\d+)", int)
            self.addc("MaxClockFrequency", clcmd, cmdopts, r"CL_DEVICE_MAX_CLOCK_FREQUENCY\s+(\d+)", int)
            self.addc("DeviceAvailable", clcmd, cmdopts, r"CL_DEVICE_AVAILABLE\s+(.+)", str)
            self.addc("CompilerAvailable", clcmd, cmdopts, r"CL_DEVICE_COMPILER_AVAILABLE\s+(.+)", str)
            self.addc("LinkerAvailable", clcmd, cmdopts, r"CL_DEVICE_LINKER_AVAILABLE\s+(.+)", str)
            self.addc("Profile", clcmd, cmdopts, r"CL_DEVICE_PROFILE\s+(.+)", str)
            self.addc("PartitionMaxSubDevices", clcmd, cmdopts, r"CL_DEVICE_PARTITION_MAX_SUB_DEVICES\s+(\d+)", int)
            self.addc("PartitionProperties", clcmd, cmdopts, r"CL_DEVICE_PARTITION_PROPERTIES\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("PartitionAffinityDomain", clcmd, cmdopts, r"CL_DEVICE_PARTITION_AFFINITY_DOMAIN\s+(.+)", str)
            self.addc("MaxWorkItemDims", clcmd, cmdopts, r"CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS\s+(\d+)", int)
            self.addc("MaxWorkItemSizes", clcmd, cmdopts, r"CL_DEVICE_MAX_WORK_ITEM_SIZES\s+(.+)", tointlist)
            self.addc("MaxWorkGroupSize", clcmd, cmdopts, r"CL_DEVICE_MAX_WORK_GROUP_SIZE\s+(\d+)", int)
            self.addc("PreferredWorkGroupSizeMultiple", clcmd, cmdopts, r"CL_KERNEL_PREFERRED_WORK_GROUP_SIZE_MULTIPLE\s+(\d+)", int)
            self.addc("MaxNumSubGroups", clcmd, cmdopts, r"CL_DEVICE_MAX_NUM_SUB_GROUPS\s+(\d+)", int)
            self.addc("SubGroupSizesIntel", clcmd, cmdopts, r"CL_DEVICE_SUB_GROUP_SIZES_INTEL\s+([\d\s]+)", tointlist)
            self.addc("PreferredVectorWidthChar", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_CHAR\s+(\d+)", int)
            self.addc("NativeVectorWidthChar", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_CHAR\s+(\d+)", int)
            self.addc("PreferredVectorWidthShort", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_SHORT\s+(\d+)", int)
            self.addc("NativeVectorWidthShort", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_SHORT\s+(\d+)", int)
            self.addc("PreferredVectorWidthInt", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_INT\s+(\d+)", int)
            self.addc("NativeVectorWidthInt", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_INT\s+(\d+)", int)
            self.addc("PreferredVectorWidthLong", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_LONG\s+(\d+)", int)
            self.addc("NativeVectorWidthLong", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_LONG\s+(\d+)", int)
            self.addc("PreferredVectorWidthFloat", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_FLOAT\s+(\d+)", int)
            self.addc("NativeVectorWidthFloat", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_FLOAT\s+(\d+)", int)
            self.addc("PreferredVectorWidthDouble", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_DOUBLE\s+(\d+)", int)
            self.addc("NativeVectorWidthDouble", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_DOUBLE\s+(\d+)", int)
            self.addc("PreferredVectorWidthHalf", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_VECTOR_WIDTH_HALF\s+(\d+)", int)
            self.addc("NativeVectorWidthHalf", clcmd, cmdopts, r"CL_DEVICE_NATIVE_VECTOR_WIDTH_HALF\s+(\d+)", int)
            self.addc("HalfFpConfig", clcmd, cmdopts, r"CL_DEVICE_HALF_FP_CONFIG\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("SingleFpConfig", clcmd, cmdopts, r"CL_DEVICE_SINGLE_FP_CONFIG\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("DoubleFpConfig", clcmd, cmdopts, r"CL_DEVICE_DOUBLE_FP_CONFIG\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("AddressBits", clcmd, cmdopts, r"CL_DEVICE_ADDRESS_BITS\s+(\d+)", int)
            self.addc("EndianLittle", clcmd, cmdopts, r"CL_DEVICE_ENDIAN_LITTLE\s+(.+)", str)
            self.addc("GlobalMemSize", clcmd, cmdopts, r"CL_DEVICE_GLOBAL_MEM_SIZE\s+(\d+)", int)
            self.addc("MaxMemAllocSize", clcmd, cmdopts, r"CL_DEVICE_MAX_MEM_ALLOC_SIZE\s+(\d+)", int)
            self.addc("ErrorCorrection", clcmd, cmdopts, r"CL_DEVICE_ERROR_CORRECTION_SUPPORT\s+(.+)", str)
            self.addc("HostUnifiedMemory", clcmd, cmdopts, r"CL_DEVICE_HOST_UNIFIED_MEMORY\s+(.+)", str)
            self.addc("SvmCapabilities", clcmd, cmdopts, r"CL_DEVICE_SVM_CAPABILITIES\s+(.+)", str)
            self.addc("MinDataTypeAlignSize", clcmd, cmdopts, r"CL_DEVICE_MIN_DATA_TYPE_ALIGN_SIZE\s+(\d+)", int)
            self.addc("MemBaseAddrAlign", clcmd, cmdopts, r"CL_DEVICE_MEM_BASE_ADDR_ALIGN\s+(\d+)", int)
            self.addc("PreferredPlatformAtomicAlign", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_PLATFORM_ATOMIC_ALIGNMENT\s+(\d+)", int)
            self.addc("PreferredGlobalAtomicAlign", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_GLOBAL_ATOMIC_ALIGNMENT\s+(\d+)", int)
            self.addc("PreferredLocalAtomicAlign", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_LOCAL_ATOMIC_ALIGNMENT\s+(\d+)", int)
            self.addc("MaxGlobalVariableSize", clcmd, cmdopts, r"CL_DEVICE_MAX_GLOBAL_VARIABLE_SIZE\s+(\d+)", int)
            self.addc("GlobalVariablePreferredTotalSize", clcmd, cmdopts, r"CL_DEVICE_GLOBAL_VARIABLE_PREFERRED_TOTAL_SIZE\s+(\d+)", int)
            self.addc("GlobalMemCacheType", clcmd, cmdopts, r"CL_DEVICE_GLOBAL_MEM_CACHE_TYPE\s+(.+)", str)
            self.addc("GlobalMemCacheSize", clcmd, cmdopts, r"CL_DEVICE_GLOBAL_MEM_CACHE_SIZE\s+(\d+)", int)
            self.addc("GlobalMemCachelineSize", clcmd, cmdopts, r"CL_DEVICE_GLOBAL_MEM_CACHELINE_SIZE\s+(\d+)", int)
            self.addc("ImageSupport", clcmd, cmdopts, r"CL_DEVICE_IMAGE_SUPPORT\s+(.+)", str)
            self.addc("MaxSamplers", clcmd, cmdopts, r"CL_DEVICE_MAX_SAMPLERS\s+(\d+)", int)
            self.addc("ImageMaxBufferSize", clcmd, cmdopts, r"CL_DEVICE_IMAGE_MAX_BUFFER_SIZE\s+(\d+)", int)
            self.addc("ImageMaxArraySize", clcmd, cmdopts, r"CL_DEVICE_IMAGE_MAX_ARRAY_SIZE\s+(\d+)", int)
            self.addc("ImageBaseAddressAlign", clcmd, cmdopts, r"CL_DEVICE_IMAGE_BASE_ADDRESS_ALIGNMENT\s+(\d+)", int)
            self.addc("ImagePitchAlign", clcmd, cmdopts, r"CL_DEVICE_IMAGE_PITCH_ALIGNMENT\s+(\d+)", int)
            self.addc("Image2dMaxHeight", clcmd, cmdopts, r"CL_DEVICE_IMAGE2D_MAX_HEIGHT\s+(\d+)", int)
            self.addc("Image2dMaxWidth", clcmd, cmdopts, r"CL_DEVICE_IMAGE2D_MAX_WIDTH\s+(\d+)", int)
            self.addc("PlanarYuvMaxHeightIntel", clcmd, cmdopts, r"CL_DEVICE_PLANAR_YUV_MAX_HEIGHT_INTEL\s+(\d+)", int)
            self.addc("PlanarYuvMaxWidthIntel", clcmd, cmdopts, r"CL_DEVICE_PLANAR_YUV_MAX_WIDTH_INTEL\s+(\d+)", int)
            self.addc("Image3dMaxHeight", clcmd, cmdopts, r"CL_DEVICE_IMAGE3D_MAX_HEIGHT\s+(\d+)", int)
            self.addc("Image3dMaxWidth", clcmd, cmdopts, r"CL_DEVICE_IMAGE3D_MAX_WIDTH\s+(\d+)", int)
            self.addc("Image3dMaxDepth", clcmd, cmdopts, r"CL_DEVICE_IMAGE3D_MAX_DEPTH\s+(\d+)", int)
            self.addc("MaxReadImageArgs", clcmd, cmdopts, r"CL_DEVICE_MAX_READ_IMAGE_ARGS\s+(\d+)", int)
            self.addc("MaxWriteImageArgs", clcmd, cmdopts, r"CL_DEVICE_MAX_WRITE_IMAGE_ARGS\s+(\d+)", int)
            self.addc("MaxReadWriteImageArgs", clcmd, cmdopts, r"CL_DEVICE_MAX_READ_WRITE_IMAGE_ARGS\s+(\d+)", int)
            self.addc("MaxPipeArgs", clcmd, cmdopts, r"CL_DEVICE_MAX_PIPE_ARGS\s+(\d+)", int)
            self.addc("PipeMaxActiveReservations", clcmd, cmdopts, r"CL_DEVICE_PIPE_MAX_ACTIVE_RESERVATIONS\s+(\d+)", int)
            self.addc("PipeMaxPacketSize", clcmd, cmdopts, r"CL_DEVICE_PIPE_MAX_PACKET_SIZE\s+(\d+)", int)
            self.addc("LocalMemType", clcmd, cmdopts, r"CL_DEVICE_LOCAL_MEM_TYPE\s+(.+)", str)
            self.addc("MaxConstantArgs", clcmd, cmdopts, r"CL_DEVICE_MAX_CONSTANT_ARGS\s+(\d+)", int)
            self.addc("MaxConstantBufferSize", clcmd, cmdopts, r"CL_DEVICE_MAX_CONSTANT_BUFFER_SIZE\s+(\d+)", int)
            self.addc("MaxParameterSize", clcmd, cmdopts, r"CL_DEVICE_MAX_PARAMETER_SIZE\s+(\d+)", int)
            self.addc("QueueOnHostProperties", clcmd, cmdopts, r"CL_DEVICE_QUEUE_ON_HOST_PROPERTIES\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("QueueOnDeviceProperties", clcmd, cmdopts, r"CL_DEVICE_QUEUE_ON_DEVICE_PROPERTIES\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("QueueOnDevicePreferredSize", clcmd, cmdopts, r"CL_DEVICE_QUEUE_ON_DEVICE_PREFERRED_SIZE\s+(\d+)", int)
            self.addc("QueueOnDeviceMaxSize", clcmd, cmdopts, r"CL_DEVICE_QUEUE_ON_DEVICE_MAX_SIZE\s+(\d+)", int)
            self.addc("MaxOnDeviceQueues", clcmd, cmdopts, r"CL_DEVICE_MAX_ON_DEVICE_QUEUES\s+(\d+)", int)
            self.addc("MaxOnDeviceEvents", clcmd, cmdopts, r"CL_DEVICE_MAX_ON_DEVICE_EVENTS\s+(\d+)", int)
            self.addc("PreferredInteropUserSync", clcmd, cmdopts, r"CL_DEVICE_PREFERRED_INTEROP_USER_SYNC\s+(.+)", str)
            self.addc("ProfilingTimerResolution", clcmd, cmdopts, r"CL_DEVICE_PROFILING_TIMER_RESOLUTION\s+(\d+)", int)
            self.addc("ExecutionCapabilities", clcmd, cmdopts, r"CL_DEVICE_EXECUTION_CAPABILITIES\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("SubGroupIndependentForwardProgress", clcmd, cmdopts, r"CL_DEVICE_SUB_GROUP_INDEPENDENT_FORWARD_PROGRESS\s+(.+)", str)
            self.addc("IlVersion", clcmd, cmdopts, r"CL_DEVICE_IL_VERSION\s+(.+)", str)
            self.addc("SpirVersions", clcmd, cmdopts, r"CL_DEVICE_SPIR_VERSIONS\s+(.+)", str)
            self.addc("PrintfBufferSize", clcmd, cmdopts, r"CL_DEVICE_PRINTF_BUFFER_SIZE\s+(\d+)", int)
            self.addc("BuiltInKernels", clcmd, cmdopts, r"CL_DEVICE_BUILT_IN_KERNELS\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("MeVersionIntel", clcmd, cmdopts, r"CL_DEVICE_ME_VERSION_INTEL\s+(\d+)", int)
            self.addc("AvcMeVersionIntel", clcmd, cmdopts, r"CL_DEVICE_AVC_ME_VERSION_INTEL\s+(\d+)", int)
            self.addc("AvcMeSupportsTextureSamplerUseIntel", clcmd, cmdopts, r"CL_DEVICE_AVC_ME_SUPPORTS_TEXTURE_SAMPLER_USE_INTEL\s+(.+)", str)
            self.addc("AvcMeSupportsPreemptionIntel", clcmd, cmdopts, r"CL_DEVICE_AVC_ME_SUPPORTS_PREEMPTION_INTEL\s+(.+)", str)
            self.addc("DeviceExtensions", clcmd, cmdopts, r"CL_DEVICE_EXTENSIONS\s+(.+)", lambda x: tostrlist(x.strip()))
            
class OpenCLInfoPlatformClass(ListInfoGroup):
    '''Class to read information for one OpenCL device (uses the clinfo command)'''
    def __init__(self, platform, extended=False, anonymous=False, clinfo_path=""):
        super(OpenCLInfoPlatformClass, self).__init__(extended=extended, anonymous=anonymous)
        self.name = platform
        self.platform = platform
        self.clinfo_path = clinfo_path
        clcmd = pjoin(clinfo_path, "clinfo")
        if not pexists(clcmd):
            clcmd = which("clinfo")
        if clcmd and len(clcmd) > 0:
            cmdopts = "--raw --offline"
            self.addc("Name", clcmd, cmdopts, r"\s+CL_PLATFORM_NAME\s+(.+)", str)
            self.addc("Version", clcmd, cmdopts, r"\s+CL_PLATFORM_VERSION\s+(.+)", str)
            self.addc("Extensions", clcmd, cmdopts, r"\s+CL_PLATFORM_EXTENSIONS\s+(.+)", lambda x: tostrlist(x.strip()))
            self.addc("Profile", clcmd, cmdopts, r"\s+CL_PLATFORM_PROFILE\s+(.+)", str)
            self.addc("Vendor", clcmd, cmdopts, r"\s+CL_PLATFORM_VENDOR\s+(.+)", str)
            #self.commands["IcdSuffix"] = (clcmd, cmdopts, r"\s+CL_PLATFORM_ICD_SUFFIX_KHR\s+(.+)", str)
            suffix = process_cmd((clcmd, cmdopts, r"\s+CL_PLATFORM_ICD_SUFFIX_KHR\s+(.+)", str))
            if " " in suffix:
                suffix = "P0"
            self.const("IcdSuffix", suffix)
            num_devs = process_cmd((clcmd, cmdopts, r".*{}.*#DEVICES\s*(\d+)".format(suffix), int))
            if num_devs and num_devs > 0:
                self.userlist = [r for r in range(num_devs)]
                self.subargs = {"clinfo_path" : clinfo_path, "suffix" : suffix}
                self.subclass = OpenCLInfoPlatformDeviceClass

class OpenCLInfoLoaderClass(InfoGroup):
    '''Class to read information for one OpenCL loader (uses the clinfo command)'''
    def __init__(self, loader, extended=False, anonymous=False, clinfo_path=""):
        super(OpenCLInfoLoaderClass, self).__init__(name=loader, extended=extended, anonymous=anonymous)
        self.clinfo_path = clinfo_path
        self.loader = loader
        clcmd = pjoin(clinfo_path, "clinfo")
        if not pexists(clcmd):
            clcmd = which("clinfo")
        if clcmd and len(clcmd) > 0:
            cmdopts = "--raw --offline | grep '[OCLICD/*]'"
            self.addc("Name", clcmd, cmdopts, r"\s+CL_ICDL_NAME\s+(.+)", str)
            self.addc("Vendor", clcmd, cmdopts, r"\s+CL_ICDL_VENDOR\s+(.+)", str)
            self.addc("Version", clcmd, cmdopts, r"\s+CL_ICDL_VERSION\s+(.+)", str)
            self.addc("OclVersion", clcmd, cmdopts, r"\s+CL_ICDL_OCL_VERSION\s+(.+)", str)

class OpenCLInfo(MultiClassInfoGroup):
    '''Class to spawn subclasses for each OpenCL device and loader (uses the clinfo command)'''
    def __init__(self, clinfo_path="", extended=False, anonymous=False):
        super(OpenCLInfo, self).__init__(name="OpenCLInfo", extended=extended, anonymous=anonymous)
        self.clinfo_path = clinfo_path
        clcmd = pjoin(clinfo_path, "clinfo")
        if not pexists(clcmd):
            clcmd = which("clinfo")
        if clcmd and len(clcmd) > 0:
            out = process_cmd((clcmd, "--raw --offline"))
            loaderlist = []
            platlist = []
            for l in out.split("\n"):
                m = re.match(r".*CL_PLATFORM_NAME\s+(.*)", l)
                if m and m.group(1) not in platlist:
                    platlist.append(m.group(1))
                    self.classlist.append(OpenCLInfoPlatformClass)
                    self.classargs.append({"platform" : m.group(1), "clinfo_path" : clinfo_path})
            for l in out.split("\n"):
                m = re.match(r".*CL_ICDL_NAME\s+(.*)", l)
                if m:
                    self.classlist.append(OpenCLInfoLoaderClass)
                    self.classargs.append({"loader" : m.group(1), "clinfo_path" : clinfo_path})
