try:
    from _local_arch.ciElementTree import *
    platform = "Local arch"
except ImportError:
    try:
        from _linux_libcpp6_x86_64.ciElementTree import *
        platform = "Linux 64 bits"
    except ImportError:
        try:
            from _linux_libcpp6_x86.ciElementTree import *
            platform = "Linux 32 bits"
        except ImportError:
            try:
                from _win64.ciElementTree import *
                platform = "Windows 64 bits"
            except ImportError:
                try:
                    from _win32.ciElementTree import *
                    platform = "Windows 32 bits"
                except ImportError:
                    try:
                        from _macosx_universal.ciElementTree import *
                        platform = "MacOS X Universal"
                    except ImportError:
                        raise ImportError("Could not find a suitable ciElementTree binary for your platform and architecture.")
