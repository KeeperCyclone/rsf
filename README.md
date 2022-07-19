# ReSurFace

`rsf` is a simple script for resurfacing rsf-scheduled Markdown notes in a
directory. It will only read files from the current working directory.

There is no scheduling algorithm. All scheduling and file modification falls on
the user to accomplish through other means.

# Requirements

- `loguru` for a bunch of logging
- `click` for the CLI

Everything else is just standard lib stuff. 

Written with Python 3.8.

# Basic Usage

The script will search for Markdown files in the current working directory and
look for RSF dateblocks in each, and then return the ones whose dates are due
for the day or the user-specified date range (see Options).

The ff. is an RSF dateblock located between content:

```markdown
Random content.

rsf:
- 2022-07-18
- 2022-07-30

More lorem ipsum.
```

RSF dateblocks may be located anywhere in a file. Hence, it is YAML-agnostic.

If there is more than one dateblock, only the first will be taken.

Run the script:

```shell
$ python rsf.py
DUE : 2022-07-18 : doc_1.md
```

It will return the due date of the file and the filename, if it is due.

There are two ways to mark a due date as completed. First, delete the date 
item:

```markdown
rsf:
- 2022-07-30
```

Second, mark it with an `x` (in *TODO.txt* style):

```markdown
rsf:
- x 2022-07-18
- 2022-07-30
```

The preference is left to the person.

## Options

The ff. demonstrates all available short options:

```shell
$ python rsf.py -ref 2022-07-10 -o 4 -a 4 -v -t -l 100
DateblockNotFound : doc_5.txt
DUE : 2022-07-14 : doc_4.txt
DUE : 2022-07-10 : doc_3.txt
NoDueDateFound : doc_2.md
NoDueDateFound : doc_1.md
NoDueDateFound : README.md
```

- `--reference | -ref <ISODATE>` makes the current date appear to be July 10.
- `--overdue | -o <DAYS>` captures due dates that are DAYS days overdue; default: 3.
- `--advance | -a <DAYS>` captures due dates DAYS days in advance.
- `--verbose | -v` displays all file reading results:
  - `DateblockNotFound` signals the lack of an RSF dateblock in the file.
  - `NoDueDateFound` means that there is a dateblock, but it has no listed
    dates which are due.
- `--include-txt | -t` includes .txt files in the search.
- `--limit | -l <LINES>` limits the script to reading the first LINES lines of a file.
  Useful if you have extremely long files and you happen to just put your RSF
  dateblocks at the very start of every file; default: 0 (no limit).
  - Note that dateblocks can be sliced 

The `-ref`, `-o`, and `-a` options together effectively allow the user to define an
arbitrary date range.

Again note that running the script without options will, by default, also capture
any dates overdue by 3 days since the current system date.


## Markdown Contents

### Valid Cases

A Markdown file should have the ff. in any part of it:

```markdown
rsf:
- x 2022-07-18
- 2022-07-30
```

It does not matter where these lines are located. Whether in YAML frontmatter or
in the main body of text, as long as they are there, they will be found.

Dates are always in ISO format. If there is a TODO-style `x` before them, they
are marked as "completed." The script will only print files with *non-completed*
due dates close to the current date.

The ff. are also viable ::

All caps:

```markdown
RSF:
- x 2022-07-18
- 2022-07-30
```

Completion mark is caps:

```markdown
RSF:
- x 2022-07-18
- X 2022-07-21
- 2022-07-30
```

Mixed case:

```markdown
RsF:
- x 2022-07-18
- 2022-07-30
```

Asterisk list items:

```markdown
rsf:
* x 2022-07-18
* 2022-07-30
```

Weird whitespace (if someone gets cross-eyed?):

```markdown
rsf:
-x2022-07-18
-     x   2022-07-30   
```

Even if the RSF dateblock is preceded and followed by text without blank lines,
it will still be detected:

```markdown
AAAAAAAAAAAA
rsf:
- x 2022-07-19
- 2022-07-30
AAAAAAAAAAAA
```

Incidentally, because of the above property, RSF dateblocks that are contained
within Markdown code fences will also be detected. Hence, keep this README away
from your directories, or else it will someday show up.


### Invalid Cases

However, the ff. **will not work** ::

Blank lines between list items; this will result in only the first date being
read:

```markdown
rsf:
- x 2022-07-18    # This will be detected.

- 2022-07-30      # This will not be seen.
```

`rsf` list header being divorced from list items will result in **no dates**
being read:

```markdown
rsf:

- x 2022-07-18   # Will not be read
```

Any amount of indentation will break the dateblock:

```markdown
rsf:
- x 2022-07-10      # This will still be read.
 - x 2022-07-18           # This will not be seen.
- 2022-07-30              # This will not be seen.
```

When two RSF blocks are in one file, the first will be read:

```markdown
rsf:             # This block will be read.
- x 2022-07-18
- 2022-07-30

RSF:             # This block will be ignored.
- 2022-08-10
- 2022-08-25
```


# Author's Notes

## Code Organization

I was experimenting with "monadic error-handling" and I still have no idea if I
handled it correctly, but that's what happened, so don't be surprised if the
script's more complicated than it should be.

Also, *viva la type hints!*

## Future Development

None planned. This is all I've ever wanted :'D

## Tests

The tests rely on `pytest`. They're actually incomplete, but since this was
just a short script, I let the ~~live-fire testing~~ console logs explain the
rest of the problems for me.

There's a bunch of test files too. You can use those—or not? Your choice.

## Performance Notes

The script will essentially open each and every file it can find in the current
working directory and read each line one by one, hitting each one with a regex.

It does not load the entire file into memory all at once. The real performance
hit here is the fact that it uses regex on a per-line basis. This means that
`rsf.py` is relatively slow, but not memory-hungry.

Hence, it should be fine for directories with about 1000 files of less than 100
lines each, for which it might take a noticeable second to complete.

If, for some reason, you tend to write very long files, get into the habit of
putting the RSF dateblocks at the very head of each file and use the `-l <LINES>`
option to limit file reading to the first LINES lines of each file.
