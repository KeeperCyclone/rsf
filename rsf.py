"""
module name: rsf
version: 1.0
alias: n/a

purpose: Resurface Markdown notes.

comments:
- "RSF header" refers to the case-insensitive string 'rsf:' which starts
  a dateblock.
- "Dateblock" or "RSF dateblock" refer to the Markdown list of 
  `todo.txt`-formatted ISO dates which describe a resurfacing 
  schedule.
"""


from dataclasses import dataclass, field
import typing
import io
import itertools
import functools
import re
import datetime
import pathlib


import click
from loguru import logger


logger.disable(__name__)
__version__ = '1.0'


# # Open file.
# # Look for rsf date list.
# # Check for due-dates.
# # Send file name to stdout.
# # Repeat for all files in directory.


class RsfException(Exception):
    """Base exception class for the RSF module."""


class DateblockNotFound(RsfException):
    """Dateblock not found in stream."""

    def __str__(self) -> str:
        return 'Dateblock not found in stream.'


class NoDueDateFound(RsfException):
    """There are no dates which are due in the dateblock."""

    def __init__(self, date_range: tuple, dateblock: list):
        self.date_range = date_range
        self.dateblock = dateblock

    def __str__(self) -> str:
        return (
            f'In range {self.date_range}, no dates '
            f'in {self.dateblock} are due.'
        )


class StringParsingError(RsfException):
    """Error parsing a string."""

    def __init__(self, string: str):
        self.string = string
    
    def __str__(self) -> str:
        return f"Error parsing <{self.string}>."


GenericFunction = typing.Callable[[typing.Any], typing.Any]


@dataclass
class MaybeResult:
    """Dataclass for attempted monadic error handling."""
    value: typing.Any
    success: bool

    @classmethod
    def _new(cls, value: typing.Any, success: bool) -> 'MaybeResult':
        """Make a new MaybeResult instance."""
        # For internal use; using `self.__init__` gets me mixed results.
        return cls(value=value, success=success)

    def bind(self, func: GenericFunction) -> 'MaybeResult':
        """
        Let a function mutate the internal value.
        
        If the function throws an RsfException, catch it and
        set result `success` to False and `value` to the 
        exception object.

        If success is False, future function calls do nothing.
        """
        if self.success is False:
            logger.debug("self.success == False; proceeding...")
            return self

        else:
            try:

                new_value = func(self.value)
                logger.debug(
                    "From {}, new value created: {}", 
                    self.value, 
                    new_value
                )
                return self._new(
                    value=new_value, 
                    success=True
                )

            except RsfException as e:

                logger.warning(
                    "Exception offloaded: <{}>. "
                    "Setting success to False...",
                    e
                )
                return self._new(
                    value=e, 
                    success=False
                )


PredicateFunction = typing.Callable[[typing.Any], bool]


def _droptake(
    drop_pred: PredicateFunction,
    take_pred: PredicateFunction,
    iterable: typing.Iterable[typing.Any]
) -> typing.Iterator:
    """
    Do dropwhile then takewhile.
    """
    logger.debug("Running on {}", iterable)

    # Drop everything up until the RSF header.
    dropped = (itertools.dropwhile(drop_pred, iterable))
    
    # Ignore the first element because it's just the RSF header.
    drop_skipped = itertools.islice(dropped, 1, None)
    logger.debug("After dropping: {}", drop_skipped)
    
    # Take all the dates then ignore everything afterward.
    taken = (itertools.takewhile(take_pred, drop_skipped))
    logger.debug("After taking: {}", taken)
    
    return taken


_START_PATTERN = re.compile(r'rsf:\s*\n?', re.IGNORECASE)
_DATE_PATTERN = re.compile(
    r'^[-*]\s*(?P<completed>x|X)?\s*(?P<date>\d{4}-\d{2}-\d{2})\s*'
)


def _isnot_start_pattern_match(line: str) -> bool:
    result = not (_START_PATTERN.match(line))
    logger.debug('Matched {} for "{}"', result, line)
    return result


def _is_date_pattern_match(line: str) -> bool:
    result = bool(_DATE_PATTERN.match(line))
    logger.debug('Matched {} for "{}"', result, line)
    return result


def _strip_trailing_newline(string: str) -> str:
    return string.strip('\n')


def find_dateblock(
    stream: typing.Iterator[str]
) -> typing.List[str]:
    """
    Returns the lines of text that contain the RSF date block.
    
    Parameters
    ----------
    `stream` : `io.TextIOBase | typing.Iterator[str]`
        An opened file or other stream that probably contains the date block.
        More generally, can be an iterator of lines of strings.
    
    Returns
    -------
    typing.List[str]
        A list of date strings.
    """
    logger.info("Running 'find_dateblock'")

    dateblock = list(
        _droptake(
            drop_pred=_isnot_start_pattern_match,
            take_pred=_is_date_pattern_match,
            iterable=(line for line in stream)
        )
    )
    
    if len(dateblock) == 0:
        raise DateblockNotFound

    result = [
        _strip_trailing_newline(line)
        for line
        in dateblock
    ]
    logger.debug("Result: {}", result)
    return result


@dataclass(order=True)
class DueDate:
    date: datetime.date = field(compare=True)
    completed: bool = field(compare=False)

    @classmethod
    def from_datestr(cls, datestr: str):

        logger.debug("Input argument <datestr: '{}'>", datestr)

        m = _DATE_PATTERN.match(datestr)
        logger.debug("_DATE_PATTERN matched: {}", m)

        completed = None
        date = None


        if m.group('completed'):
            completed = True
        else:
            completed = False

        logger.debug("Detected completed is {}", completed)
        
        if (date_ := m.group('date')):
            date = datetime.date.fromisoformat(date_)
            logger.debug("Detected date is '{}'", date)
        else:
            raise StringParsingError(m.group())

        
        
        return cls(date, completed)


def _duedateblock_from_strdateblock(
    dateblock: typing.List[str]
) -> typing.List[DueDate]:
    """Convert list of dates-as-strings to DueDate objects."""
    logger.info("Running '_duedateblock_from_strdateblock'")
    return [
        DueDate.from_datestr(line)
        for line
        in dateblock
    ]


@dataclass
class DateRange:
    earliest: datetime.date
    latest: datetime.date
    
    def __contains__(self, date: datetime.date) -> bool:
        return self.earliest <= date <= self.latest

    @property
    def tuple(self) -> tuple:
        return self.earliest, self.latest


def _make_date_range(
        ref: datetime.date, 
        overdue: int, 
        advance: int
    ) -> DateRange:
        logger.debug(
            "ref: {}, overdue: {}, advance: {}",
            ref,
            overdue,
            advance
        )
        overdue_delta = datetime.timedelta(days=overdue)
        advance_delta = datetime.timedelta(days=advance)
        earliest, latest = ref - overdue_delta, ref + advance_delta
        logger.debug("earliest: {}, latest: {}", earliest, latest)
        return DateRange(earliest, latest)


def get_due_date(
    dateblock: typing.List[DueDate],
    reference: datetime.date,
    overdue: int,
    advance: int
) -> datetime.date:
    """Returns noncompleted dates from a list of DueDate objects."""
    
    logger.info("Running 'get_due_date'")
    daterange = _make_date_range(
        ref=reference,
        overdue=overdue,
        advance=advance
    )

    dates: typing.List[DueDate] = sorted(dateblock)
    logger.debug("Sorted dates: {}", dates)
    logger.info("Checking dates in ascending order...")
    for d in dates:
        if d.completed is True:
            logger.debug("<{}> is completed. Checking next...", d)
            continue
        if d.date in daterange:
            logger.info("<{}> is in DateRange. Returning it.", d)
            return d.date
    else:
        logger.warning("No due date found.")
        raise NoDueDateFound(
            date_range=daterange.tuple,
            dateblock=dateblock
        )


def _excise_filestem(filename: str) -> str:
    if '/' in filename:
        filename = filename.split('/')[-1]
    return filename


def get_due_str(
    due_date: datetime.date,
    filename: str
) -> str:
    """Format the display missage for a due file."""
    logger.info("Running 'get_due_str'")
    filename = _excise_filestem(filename)
    return f"DUE : {due_date.isoformat()} : {filename}"


def _limit_stream(stream: typing.Iterator, limit: int = 0) -> typing.Iterator:
    if limit <= 0:
        return stream
    return itertools.compress(
        stream,
        itertools.repeat(True, limit)
    )


def get_duestr_from_file(
    filename: str,
    reference: datetime.date,
    overdue: int,
    advance: int,
    return_nodues: bool,
    limit: int
) -> str:

    logger.info("Running 'get_duestr_from_file'")
    logger.debug(
        'filename: {}, reference date: {}, overdue: {}, advance: {}',
        filename,
        reference,
        overdue,
        advance
    )

    get_due_date_ = functools.partial(
        get_due_date,
        reference=reference,
        overdue=overdue,
        advance=advance
    )
    get_due_str_ = functools.partial(
        get_due_str,
        filename=filename
    )

    with open(filename, 'r') as stream:
        stream_ = _limit_stream(stream, limit=limit)
        result = MaybeResult(
            value=stream_,
            success=True
        ).bind(
            func=find_dateblock
        ).bind(
            func=_duedateblock_from_strdateblock
        ).bind(
            func=get_due_date_
        ).bind(
            func=get_due_str_
        )
    
    logger.info("Got duestr parsing result: {}", result)

    if result.success is True:
        return result.value
    
    if return_nodues is True:
        type_ = type(result.value).__name__
        return f"{type_} : {_excise_filestem(filename)}"
    else:
        return ''


@click.command()
@click.option(
    '--reference',
    '-ref',
    default=datetime.date.today().isoformat(),
    help="Compare due dates to this date; defaults to system's today.",
    type=str
)
@click.option(
    '--overdue',
    '-o', 
    type=int,
    default=3,
    help="Include due dates D days before the reference date; default: 3."
)
@click.option(
    '--advance',
    '-a', 
    type=int,
    default=0,
    help="Include due dates D days after the reference date; default: 0."
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help="Report all file reading results."
)
@click.option(
    '--include-txt',
    '-t',
    is_flag=True,
    help="Include `.txt` files in the search."
)
@click.option(
    '--limit',
    '-l',
    type=int,
    default=0,
    help="Limit the number of lines read per file; default: 0 (no limit)."
)
@click.option(
    '--enable-logging',
    is_flag=True,
    help="Flood the console."
)
def resurface(
    reference: str,
    overdue: int,
    advance: int,
    verbose: bool,
    include_txt: bool,
    limit: int,
    enable_logging: bool
) -> None:
    """
    Display Markdown files that have resurfacing schedules
    defined by RSF dateblocks, and which have dates which
    are due.
    """

    if enable_logging is True:
        logger.enable(__name__)

    logger.info("`resurface` command invoked!")

    cwd = pathlib.Path.cwd()
    reference_ = datetime.date.fromisoformat(reference)

    logger.debug('cwd: {}', cwd)
    logger.debug('reference date: {}', reference_)
    logger.debug(
        'verbose: {}, include_txt: {}',
        verbose,
        include_txt
    )

    glob_ = list(cwd.glob('*.md'))
    if include_txt is True:
        glob_.extend(
            list(
                cwd.glob('*.txt')
            )
        )
    glob_.sort(reverse=True)
    logger.debug('Files found: {}', glob_)
    
    results = list()
    for filename in glob_:
        logger.info("Doing next file: {}", filename)
        results.append(
            get_duestr_from_file(
                filename=str(filename),
                reference=reference_,
                overdue=overdue,
                advance=advance,
                return_nodues=verbose,
                limit=limit
            )
        )

    results_ = [
        r 
        for r 
        in results
        if r != ''
    ]

    for r in results_:
        click.echo(r)


if __name__ == '__main__':
    resurface()

