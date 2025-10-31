import subprocess

REQUIRED_VRAM_FREE = 23400


def get_free_vram_mib(gpu_index: int = 0) -> int | None:
    """
    Return free VRAM (MiB) for the given GPU index using nvidia-smi.
    Returns None if nvidia-smi fails.
    """
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.free",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        if gpu_index >= len(lines):
            return None
        return int(lines[gpu_index])
    except Exception:
        return None
