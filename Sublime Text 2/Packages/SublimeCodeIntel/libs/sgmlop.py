try:
    from _local_arch.sgmlop import *
    platform = "Local arch"
except ImportError:
    try:
        from _linux_libcpp6_x86_64.sgmlop import *
        platform = "Linux 64 bits"
    except ImportError:
        try:
            from _linux_libcpp6_x86.sgmlop import *
            platform = "Linux 32 bits"
        except ImportError:
            try:
                from _win64.sgmlop import *
                platform = "Windows 64 bits"
            except ImportError:
                try:
                    from _win32.sgmlop import *
                    platform = "Windows 32 bits"
                except ImportError:
                    try:
                        from _macosx_universal.sgmlop import *
                        platform = "MacOS X Universal"
                    except ImportError:
                        raise ImportError("Could not find a suitable sgmlop binary for your platform and architecture.")
