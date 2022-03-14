"""Module for reprsenting scheduler jobs."""
from datetime import timedelta
import re
from typing import Any, Dict, Optional, Union


multiple_map = {
    "K": 1024 ** 0,
    "M": 1024 ** 1,
    "G": 1024 ** 2,
    "T": 1024 ** 3,
    "E": 1024 ** 4,
}

state_colors = {
    "FAILED": "red",
    "TIMEOUT": "red",
    "OUT_OF_MEMORY": "red",
    "RUNNING": "cyan",
    "CANCELLED": "yellow",
    "COMPLETED": "green",
    "PENDING": "blue",
}

#: Regex for DDHHMMSS style timestamps
DDHHMMSS_RE = re.compile(
    r"(?P<days>\d+)-(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})"
)
#: Regex for HHMMSS style timestamps
HHMMSS_RE = re.compile(r"(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})")
#: Regex for HHMMmmm style timestamps
MMSSMMM_RE = re.compile(
    r"(?P<minutes>\d{2}):(?P<seconds>\d{2}).(?P<milliseconds>\d{3})"
)
#: Regex for maxRSS and reqmem
MEM_RE = re.compile(
    r"(?P<memory>[-+]?\d*\.\d+|\d+)(?P<multiple>[KMGTE]?)(?P<type>[nc]?)"
)


class Job:
    """Representation of scheduler job."""

    def __init__(self, job: str, jobid: str, filename: Optional[str]) -> None:
        """Initialize new job.

        Args:
            job: the base job number
            jobid: same as job unless an array job
            filename: the output file associated with this job
        """
        self.job = job
        self.jobid = jobid
        self.filename = filename
        self.stepmem = 0.0
        self.totalmem: Optional[float] = None
        self.time: Optional[str] = "---"
        self.time_eff: Union[str, float] = "---"
        self.cpu: Optional[Union[str, float]] = "---"
        self.mem: Union[str, float] = "---"
        self.state: Optional[str] = None
        self.other_entries: Dict[str, str] = {}

    def __eq__(self, other: Any) -> bool:
        """Test for equality.

        Args:
            other: the other object

        Returns:
            true if the other object is a Job and all attributes match
        """
        if not isinstance(other, Job):
            return False

        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        """Job representation.

        Returns:
            The job string representation
        """
        return f"Job(job={self.job}, jobid={self.jobid}, filename={self.filename})"

    def update(self, entry: Dict) -> None:
        """Update the job properties based on the db_inquirer entry.

        Args:
            entry: the db_inquirer entry for the matching job
        """
        if "." not in entry["JobID"]:
            self.state = entry["State"].split()[0]

        if self.state == "PENDING":
            return

        # main job id
        if self.jobid == entry["JobID"]:
            self._update_main_job(entry)

        elif self.state != "RUNNING":
            for k, value in entry.items():
                if k not in self.other_entries or not self.other_entries[k]:
                    self.other_entries[k] = value
            self.stepmem += parsemem(entry["MaxRSS"]) if "MaxRSS" in entry else 0

    def _update_main_job(self, entry: Dict) -> None:
        """Update properties for the main job.

        Args:
            entry: the entry where the jobid matches exactly, e.g. not batch or ex
        """
        self.other_entries = entry
        self.time = entry["Elapsed"] if "Elapsed" in entry else None
        requested = (
            _parse_slurm_timedelta(entry["Timelimit"]) if "Timelimit" in entry else 1
        )
        wall = _parse_slurm_timedelta(entry["Elapsed"]) if "Elapsed" in entry else 0

        if requested != 0:
            self.time_eff = round(wall / requested * 100, 1)

        if self.state == "RUNNING":
            return

        cpus = (
            _parse_slurm_timedelta(entry["TotalCPU"]) / int(entry["AllocCPUS"])
            if "TotalCPU" in entry and "AllocCPUS" in entry
            else 0
        )
        if wall == 0:
            self.cpu = None
        else:
            self.cpu = round(cpus / wall * 100, 1)

        if "REQMEM" in entry and "NNodes" in entry and "AllocCPUS" in entry:
            self.totalmem = parsemem(
                entry["REQMEM"], int(entry["NNodes"]), int(entry["AllocCPUS"])
            )

    def name(self) -> str:
        """The name of the job.

        Returns:
            The filename (if set) or jobid
        """
        if self.filename:
            return self.filename
        return self.jobid

    def get_entry(self, key: str) -> Any:
        """Get an attribute by name.

        Args:
            key: the attribute to query

        Returns:
            The value of that attribute or "---" if not found
        """
        if key == "JobID":
            return self.name()
        if key == "State":
            return self.state
        if key == "MemEff":
            if self.totalmem:
                return round(self.stepmem / self.totalmem * 100, 1)
            return "---"
        if key == "TimeEff":
            return self.time_eff
        if key == "CPUEff":
            return self.cpu if self.cpu else "---"
        else:
            return self.other_entries.get(key, "---")


def _parse_slurm_timedelta(delta: str) -> int:
    """Parse one of the three formats used in TotalCPU.

    Based on which regex matches, convert into a timedelta
    and return total seconds.

    Args:
        delta: The time duration

    Returns:
        Number of seconds elapsed during the delta

    Raises:
        ValueError: if unable to parse delta
    """
    match = re.match(DDHHMMSS_RE, delta)
    if match:
        return int(
            timedelta(
                days=int(match.group("days")),
                hours=int(match.group("hours")),
                minutes=int(match.group("minutes")),
                seconds=int(match.group("seconds")),
            ).total_seconds()
        )
    match = re.match(HHMMSS_RE, delta)
    if match:
        return int(
            timedelta(
                hours=int(match.group("hours")),
                minutes=int(match.group("minutes")),
                seconds=int(match.group("seconds")),
            ).total_seconds()
        )
    match = re.match(MMSSMMM_RE, delta)
    if match:
        return int(
            timedelta(
                minutes=int(match.group("minutes")),
                seconds=int(match.group("seconds")),
                milliseconds=int(match.group("milliseconds")),
            ).total_seconds()
        )
    raise ValueError(f'Failed to parse time "{delta}"')


def parsemem(mem: str, nodes: int = 1, cpus: int = 1) -> float:
    """Parse memory representations of reqmem and maxrss.

    Args:
        mem: the memory representation
        nodes: the number of nodes in the job
        cpus: the number of cpus in the job

    Returns:
        The number of bytes for the job.
        if mem is empty, return 0.
        if mem ends with n or c, scale by the provided nodes or cpus respecitvely
        the multiple of memory (e.g. M or G) is always scaled if provided

    Raises:
        ValueError: if unable to parse mem
    """
    if mem == "" or mem == "0":
        return 0
    match = re.fullmatch(MEM_RE, mem)
    if not match:
        raise ValueError(f'Failed to parse memory "{mem}"')
    memory = float(match.group("memory"))

    if match.group("multiple") != "":
        memory *= multiple_map[match.group("multiple")]

    if match.group("type") != "":
        if match.group("type") == "n":
            memory *= nodes
        else:
            memory *= cpus
    return memory
