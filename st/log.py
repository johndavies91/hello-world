from logging import * # pylint: disable=unused-wildcard-import,wildcard-import,redefined-builtin
import sys
import subprocess
# Avoid importing other devops modules in here where possible to avoid cyclic imports

# TODO2 multiline logs ideally should show the timestamp next to each line, not just the first one. Maybe logtransfer can do this instead?
# TODO logrotation
# TODO use ELK and logtransfer

logger = None

class logstr(str):
    pass

def highlight(text, style="red"):
    # Returns the original text wrapped in the style tags.
    style = {"black": 0, "purple": 35, "red": 31, "green": 32, "yellow": 33, "blue": 34, "cyan": 36, "grey": 90, "blackback": 0, "greyback": 47}.get(style, style)
    text = "\x1b[%sm%s\x1b[0m" % (style, text)
    return text

class StFormatter(Formatter):

    def format(self, record):
        text = super().format(record)
        if hasattr(record.msg, "colour"):
            text = highlight(text, record.msg.colour)
        return text

    def formatException(self, ei):
        text = super().formatException(ei)
        try:
            text = "%s\n%s"%(ei[1].decoded, text)
        except AttributeError:
            pass
        return text

class ColourLogger(Logger):
    def __init__(self, *args):
        super().__init__(*args)

    def _log(self, level, msg, *args, **kw): # pylint: disable=arguments-differ
        colour = kw.pop("colour", None)
        if colour:
            msg = logstr(msg)
            msg.colour = colour # pylint: disable=attribute-defined-outside-init
        super()._log(level, msg, *args, **kw)

setLoggerClass(ColourLogger)
logger = getLogger('devops')

def setup(level=INFO, name=sys.argv[0]):
    subprocess.call("mkdir -p /var/log/devops", shell=True)
    filename = "/var/log/devops/%s.log"%(name.split("/")[-1].rsplit(".")[0].lower()) #TODO2 maybe there is a better alternative to var log but leaving it as is for now
    logger.setLevel(level)

    formatter1 = StFormatter(fmt='%(asctime)s.%(msecs)03d\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    formatter2 = Formatter(fmt='%(asctime)s.%(msecs)03d\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S') # Do not log colours to a logfile, just the stdout stream

    fileHandler = FileHandler(filename, encoding="utf-8") # TODO2 maybe allow different encodings
    fileHandler.setFormatter(formatter2)
    logger.addHandler(fileHandler)

    consoleHandler = StreamHandler()
    consoleHandler.setFormatter(formatter1)
    logger.addHandler(consoleHandler)

    logger.info("BEGIN %s", sys.argv)
    return logger
