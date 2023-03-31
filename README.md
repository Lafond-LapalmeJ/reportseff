[![Tests](https://github.com/troycomi/reportseff/workflows/Tests/badge.svg)](https://github.com/troycomi/reportseff/actions?workflow=Tests)
[![codecov](https://codecov.io/gh/troycomi/reportseff/branch/main/graph/badge.svg)](https://codecov.io/gh/troycomi/reportseff)
[![PyPI](https://img.shields.io/pypi/v/reportseff.svg)](https://pypi.org/project/reportseff/)

# `reportseff`

> A python script for tabular display of slurm efficiency information

![Example](https://github.com/troycomi/reportseff/raw/main/imgs/example.png)

## About

### Motivation

Whether a sys admin or cluster user, knowing how well you are estimating job
resources can help streamline job scheduling and maximize your priority. If you
have ever tried to use `sacct` you probably had some trouble interpreting the
output.  While `seff` or `jobstats` can provide detailed summaries, they don't
scale easily to array jobs or offer a way to see all the jobs from a single
user.  `reportseff` aims to fill this role.  Read more about the [motivation
for reportseff](https://github.com/troycomi/reportseff/blob/main/ABOUT.md).

### Audience

If you are running more than one slurm job at a time, you should try
`reportseff`.  Users of HPC systems can get an idea how well they estimate
resource usage.  By tuning these values, you can get scheduled earlier and not
be penalized for unused allocations.  Since `reportseff` can parse job ids from
slurm output files, it simplifies the task of identifying which jobs have
failed and why. Sys admins can pipe `reportseff` output to identify users with
poor utilization or produce summaries at the end of a billing cycle.

### Implementation

`reportseff` is a wrapper around `sacct` that provides more complex option
parsing, simpler options, and cleaner, colored outputs.  All querying is
performed in a single call to `sacct` and should have similar performance.
Multi-node and GPU utilization is acquired from information contained in the
`AdminComment` field, as generated by `jobstats`.

## Usage

### Installation

`reportseff` runs on python >= 3.6.
The only external dependency is click (>= 6.7).
Calling

```sh
pip install --user reportseff
# OR
pipx install reportseff
```

will create command line bindings and install click.

### Sample Usage

Try `reportseff -u $USER` or just `reportseff` in a directory with some slurm
outputs.  You may be surprised by your results!

#### Single job

Calling `reportseff` with a single jobid will provide equivalent information to
seff for that job. `reportseff 24371789` and `reportseff map_fastq_24371789`
produce the following output:

```txt
   JobID      State          Elapsed   CPUEff   MemEff
24371789    COMPLETED       03:08:03   71.2%    45.7%
```

#### Single array job

Providing either the raw job id or the array job id will get efficiency
information for a single element of the array job. `reportseff 24220929_421`
and `reportseff 24221219` generate:

```txt
       JobID      State          Elapsed    CPUEff   MemEff
24220929_421    COMPLETED       00:09:34    99.0%    34.6%
```

#### Array job group

If the base job id of an array is provided, all elements of the array will
be added to the output. `reportseff 24220929`

```txt
          JobID      State          Elapsed    CPUEff   MemEff
     24220929_1    COMPLETED       00:10:43    99.2%    33.4%
    24220929_11    COMPLETED       00:10:10    99.2%    37.5%
    24220929_21    COMPLETED       00:09:25    98.8%    36.1%
    24220929_31    COMPLETED       00:09:19    98.9%    33.3%
    24220929_41    COMPLETED       00:09:23    98.9%    33.3%
    24220929_51    COMPLETED       00:08:02    98.5%    36.3%
    ...
   24220929_951    COMPLETED       00:25:12    99.5%    33.5%
   24220929_961    COMPLETED       00:39:26    99.7%    34.1%
   24220929_971    COMPLETED       00:24:11    99.5%    34.2%
   24220929_981    COMPLETED       00:24:50    99.5%    44.3%
   24220929_991    COMPLETED       00:13:05    98.7%    33.7%
```

#### Glob expansion of slurm outputs

Because slurm output files can act as job id inputs, the following can
get all seff information for a given job name:

```txt
slurm_out  ❯❯❯ reportseff split_ubam_24*
              JobID      State          Elapsed   CPUEff   MemEff
split_ubam_24342816    COMPLETED       23:30:32   99.9%    4.5%
split_ubam_24342914    COMPLETED       22:40:51   99.9%    4.6%
split_ubam_24393599    COMPLETED       23:43:36   99.4%    4.4%
split_ubam_24393655    COMPLETED       21:36:58   99.3%    4.5%
split_ubam_24418960     RUNNING        02:53:11    ---      ---
split_ubam_24419972     RUNNING        01:26:26    ---      ---
```

#### No arguments

Without arguments, reportseff will try to find slurm output files in the
current directory. Combine with `watch` to monitor job progress:
`watch -cn 300 reportseff --color --modified-sort`

```txt
                JobID           State          Elapsed   CPUEff   MemEff
   split_ubam_24418960          RUNNING        02:56:14    ---      ---
fastq_to_ubam_24419971          RUNNING        01:29:29    ---      ---
   split_ubam_24419972          RUNNING        01:29:29    ---      ---
fastq_to_ubam_24393600         COMPLETED     1-02:00:47   58.3%    41.1%
    map_fastq_24419330          RUNNING        02:14:53    ---      ---
    map_fastq_24419323          RUNNING        02:15:24    ---      ---
    map_fastq_24419324          RUNNING        02:15:24    ---      ---
    map_fastq_24419322          RUNNING        02:15:24    ---      ---
mark_adapters_24418437         COMPLETED       01:29:23   99.8%    48.2%
mark_adapters_24418436         COMPLETED       01:29:03   99.9%    47.4%
```

#### Filtering slurm output files

One useful application of `reportseff` is filtering a directory of slurm output
files based on the state or time since running. Additionally, if only the
`jobid` is specified as a format output, the filenames will be returned in a
pipe-friendly manner:

```txt
old_runs   ❯❯❯ reportseff --since d=4 --state Timeout

                 JobID   State      Elapsed  CPUEff   MemEff
call_variants_31550458  TIMEOUT    20:05:17  99.5%     0.0%
call_variants_31550474  TIMEOUT    20:05:17  99.6%     0.0%
call_variants_31550500  TIMEOUT    20:05:08  99.7%     0.0%
old_runs   ❯❯❯ reportseff --since d=4 --state Timeout --format jobid
call_variants_31550458
call_variants_31550474
call_variants_31550500
```

To find all lines with `output:` in jobs which have timed out or failed
in the last 4 days:

```sh
reportseff --since 'd=4' --state TO,F --format jobid | xargs grep output:
```

### Arguments

Jobs can be passed as arguments in the following ways:

- Job ID such as 1234567.  If the id is part of an array job, only the element
for that ID will be displayed.  If the id is the base part of an array job,
all elements in the array will be displayed.
- Array Job ID such as 1234567\_89.  Will display only the element specified.
- Slurm output file.  Format must be BASE\_%A\_%a.  BASE is optional as is a
'.out' suffix.  Unix glob expansions can also be used to filter which jobs
are displayed.
- From current directory.  If no argument is supplied, `reportseff` will attempt
to find slurm output files in the current directory as described above.
If a user is provided, instead `reportseff` will show recent jobs for that user.
If only `since` is set, all recent jobs for all users will be shown (if allowed).
- Supplying a directory as a single argument will override the current
directory to check for slurm outputs.

### Options

- `--color/--no-color`: Force color output or not.  By default, will force color
  output.  With the no-color flag, click will strip color codes for everything
  besides stdout.
- `--modified-sort`: Instead of sorting by filename/jobid, sort by last
  modification time of the slurm output file.
- `--debug`: Write sacct result to stderr.
- `--user/-u`: Ignore job arguments and instead query sacct with provided user.
  Returns all jobs from the last week.
- `--state/-s`: Output only jobs with states matching one of the provided options.
  Accepts comma separated values of job codes (e.g. 'R') or full names
  (e.g. RUNNING).  Case insensitive.
- `--not-state/-S`: Output only jobs with states not matching any of the provided options.
  Accepts comma separated values of job codes (e.g. 'R') or full names
  (e.g. RUNNING).  Case insensitive.
- `--format`: Provide a comma separated list of columns to produce. Prefixing the
  argument with `+` adds the specified values to the defaults.  Values can
  be any valid column name to sacct and the custom efficiency values: TimeEff,
  cpuEff, MemEff.  Can also optionally set alignment (<, ^, >) and maximum width.
  Default is center-aligned with a width of the maximum column entry.  For
  example, `--format 'jobid%>,state%10,memeff%<5'` produces 3 columns with:
  - JobId aligned right, width set automatically
  - State with width 10 (center aligned by default)
  - MemEff aligned left, width 5
- `--slurm-format`: The filename pattern passed to sbatch during job submission.
  Overrides the default regex for job id parsing from filenames.  E.g. to match
  filenames like `123456.out` set `--slurm-format %j.out`.
- `--since`: Limit results to those occurring after the specified time.  Accepts
  sacct formats and a comma separated list of key/value pairs.  To get jobs in
  the last hour and a half, can pass `h=1,m=30`.
-`--until`: Limit results to those occurring before the specified time. Accepts
  sacct formats and a comma separated list of key/value pairs.
  Useful in combination with the 'since' option to query a specific range.
- `--partition`: Limit results to a specific partition.
- `--node/-n`: Display information for multi-node jobs; requires additional
  sacct fields from jobstats.
- `--node-and-gpu/-g`: Display information for multi-node jobs and GPU information;
  requires additional sacct fields from jobstats.
- `--parsable/-p`: Ignore formatting and output as a `|` delimited table.  Useful
  for piping into more complex analyses.

## Status, Contributions, and Support

`reportseff` is actively maintained but currently feature complete.  If there
is a function missing, please open an issue to discuss its merit!

Bug reports, pull requests, and any feedback are welcome! Prior to submitting
a pull request, be sure any new features have been tested and all unit tests
are passing. In the cloned repo with
[poetry](https://github.com/python-poetry/poetry#installation) installed:

```sh
poetry install
poetry run pytest
poetry run pre-commit install
nox
```

## Troubleshooting

### I can't install, what is pip?

[pip](https://pip.pypa.io/en/stable/) is the package installer for python.  If
you get an error that pip isn't found, look for a python/anaconda/conda module.
[pipx](https://pypa.github.io/pipx/) ensures that each application is installed
in an isolated environment.  This resolves issues of dependency versions and
allows applications to be run from any environment.

### The output has no color with many jobs!

Click should determine if the output supports color display and react automatically
in a way you expect.  Check that your terminal is setup to display colors and
that your pager (probably less) will display color by default.  Some commands,
e.g. `watch` aren't handled properly even when invoked to support color.  Here
are some useful settings for your `.bashrc`:
```
# have less display colors by default.  Will fix `reportseff` not showing colors
export LESS="-R"
# for watch aliases, include the `--color` option
watch -cn 300 reportseff --color --modified-sort
#      ^                 ^^^^^^^
```
You can always for display of color (or suppress it) with the `--color/--no-color`
options

### I get an error about broken pipes when chaining to other commands

Python will report that the consumer of process output has closed the stream
(i.e. the pipe) while still attempting to write.  Newer versions of click
should suppress the warning output, but it seems to not always work.  Besides
some extra printing on stderr, the output is not affected.

### My jobs don't have any information about multiple nodes or GPU efficiency

Because `sacct` doesn't currently record this information, `reportseff`
retrieves it from a custom field from `jobstats`, developed at Princeton
University.  If you are outside a Research Computing cluster, that information
will likely be absent.  Node-level reporting is only shown for jobs which use
multiple nodes or GPUs.  If you need a list of where jobs were run, you can add
`--format +NodeList`.

## Acknowledgments

The code for calling sacct and parsing the returning information was taken
from [Slurmee](https://github.com/PrincetonUniversity/slurmee).

Style and tooling from [hypermodern python](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)

Code review provided from a [repo-review](https://researchcomputing.princeton.edu/services/repo-review-consultations)
which vastly improved this readme.
