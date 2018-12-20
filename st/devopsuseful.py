import log
logger = log.getLogger("devops")
import re
import csv
import subprocess
from io import StringIO
import platform

def decode(x, encoding):
    try:
        if x.stdout is None:
            x.decoded = None
        else:
            x.decoded = (x.stdout.decode(encoding)).strip()
    except UnicodeDecodeError as e:
        print("UNABLE TO DECODE AS %s (%s)"%(encoding, e))
        print(repr(x.stdout))
        raise

def runCommand(cmd, encoding="utf-8", split=None, retries=1, **kw):
    logger.info(subprocess.list2cmdline(cmd) if isinstance(cmd, list) else cmd)
    kw.setdefault("stdout", subprocess.PIPE)
    kw.setdefault("stderr", subprocess.STDOUT)
    kw.setdefault("check", True)
    while retries > 0:
        try:
            result = subprocess.run(cmd, **kw)
            retries = 0
        except subprocess.CalledProcessError as e:
            decode(e, encoding)
            logger.info(e.decoded)
            retries -= 1
            if retries == 0:
                raise
            else:
                import time
                time.sleep(1)

    if encoding is not None:
        decode(result, encoding)
        if split is not None:
            result.split = result.decoded.split(split)
            if result.split[-1] == "":
                result.split = result.split[:-1]
    return result

def readFile(filename, flag="r", encoding="utf-8"):
    with open(filename, flag, encoding=encoding) as f:
        try:
            return f.read()
        except Exception as e:
            raise e

def writeFile(contents, filename, flag="w", encoding="utf-8"):
    if isinstance(contents, bytes):
        flag = flag+"b"
        encoding = None
    f = open(filename, flag, encoding=encoding)
    f.write(contents)
    f.close()

def readCsv(data, reader=csv.DictReader, removeChars=re.compile(chr(0)), **kwargs):
    data = removeChars.sub("", data)
    result = list(reader(StringIO(data), **kwargs))
    for record in result:
        if isinstance(record, dict):
            for k, v in record.items():
                if isinstance(v, str):
                    record[k] = v
        elif isinstance(record, list):
            for i, v in enumerate(record):
                record[i] = v
    return result

def isHostType(types, hostname=None):
    if not isinstance(types, list):
        types = [types]
    return "all" in types or splitHostname(hostname)[1] in types

def isHostLevel(levels, hostname=None):
    if not isinstance(levels, list):
        levels = [levels]
    return "all" in levels or splitHostname(hostname)[0] in levels

def splitHostname(hostname=None):
    if hostname is None:
        hostname = platform.node()
    regex = re.compile("(dev|build|terminal|stage|prod)(.*?)([0-9]+)") #TODO2 temporarily allowing terminal on its own as this is the current setup, but in future we'll look to have terminal as a type only.
    match = regex.search(hostname)
    if not match:
        raise Exception("Unexpected hostname (%s). Doesn't follow naming convention"%hostname)
    (level, typ, number) = match.groups()

    if typ == "":
        typ = level
    return (level, typ, int(number))

def prompt(msg, prompts={"y": "continue", "n": "skip"}): # pylint: disable=dangerous-default-value
    msg = "%s (%s / CTRL-C=abort and exit): " % (msg, " / ".join("%s=%s" % (p, m) for p, m in sorted(prompts.items())))
    _prompt = None
    while _prompt not in prompts:
        _prompt = input(log.highlight(msg, "yellow")).lower()
    return _prompt
