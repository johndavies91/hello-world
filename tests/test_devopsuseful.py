import stcheck
import devopsuseful
import csv
import platform
import subprocess

class Test_devopsuseful():

    @stcheck.mark.parametrize("write, writeKw, readKw, expected, readException, writeException", [
        ("", {}, {}, "", None, None),
        ("1", {}, {}, "1", None, None),
        (b"2 \xc3\xa9", {}, {"flag":"rb", "encoding":None}, b"2 \xc3\xa9", None, None),
        (b"3 \xc3\xa9", {}, {"flag":"rb"}, "3 \xc3\xa9", ValueError("binary mode doesn't take an encoding argument"), None),
        ("4 \xc3\xa9", {}, {}, "4 \xc3\xa9", None, None),
        ("5 \xc3\xa9", {}, {"flag":"rb", "encoding":None}, b'5 \xc3\x83\xc2\xa9', None, None),
        ("6 f1,f2\nv1,v2%s,v%s3,v4"%(chr(0), chr(0)), {}, {}, '6 f1,f2\nv1,v2\x00,v\x003,v4', None, None),
        (b"7 f1,f2\nv1,v2\x00,v\x003,v4", {}, {"flag":"rb", "encoding":None}, b'7 f1,f2\nv1,v2\x00,v\x003,v4', None, None),
        ("8 flag is now wb", {"flag":"wb", "encoding":None}, {}, "", None, TypeError("a bytes-like object is required, not 'str'")),
        ("9 file should be gone after test 8", {"flag":"wb"}, {}, "", Exception(r"\[Errno 2\] No such file or directory: '/tmp/test_readFile_writeFile'"), ValueError("binary mode doesn't take an encoding argument")),
        (r"10 \xc3\xa9", {"encoding":"latin-1"}, {}, "10 \\xc3\\xa9", None, None),
        ("11 \u0777", {}, {"encoding":"ascii"}, None, UnicodeDecodeError, None),
        ("12 \u0021", {"encoding":"ascii"}, {"encoding":"ascii"}, "12 !", None, None),
    ])
    def test_readFile_writeFile(self, write, writeKw, readKw, expected, readException, writeException):
        filename = "/tmp/test_readFile_writeFile"
        with stcheck.raises(writeException):
            devopsuseful.writeFile(write, filename, **writeKw)
        with stcheck.raises(readException):
            actual = devopsuseful.readFile(filename, **readKw)
            assert expected == actual
        devopsuseful.runCommand(["rm", filename], check=False) #not using temporary files yet, so using this as cleanup

    @stcheck.mark.parametrize("data, kw, expected, expected2", [
        ("", {}, [], []),
        (chr(0), {}, [], []),
        ("x", {}, [], [["x"]]),
        ("x\ny", {}, [{"x":"y"}], [["x"], ["y"]]),
        ("D,e,l,t,\u0394\n\u0394", {}, [{"D":"\u0394", "e":None, "l":None, "t":None, "\u0394":None}], [["D", "e", "l", "t", "\u0394"], ["\u0394"]]),
        ('f1,f2\nv1,v2,v3,v4', {}, [{"f1":"v1", "f2":"v2", None:["v3", "v4"]}], [["f1", "f2"], ["v1", "v2", "v3", "v4"]]),
        ('f1,f2\nv1,v2%s,v%s3,v4'%(chr(0), chr(0)), {}, [{"f1":"v1", "f2":"v2", None:["v3", "v4"]}], [["f1", "f2"], ["v1", "v2", "v3", "v4"]]),
    ])
    def test_readCsv(self, data, kw, expected, expected2):
        actual = devopsuseful.readCsv(data, **kw)
        assert expected == actual
        kw["reader"] = csv.reader
        actual = devopsuseful.readCsv(data, **kw)
        assert expected2 == actual

    @stcheck.mark.parametrize("types, hostname, expected", [
        ([], "stageloadbalancer50", False),
        ("mailserver", "prodmailserver4", True),
        (["dev", ",", "jeff"], "dev1", True),
        (8, "dev2", False),
        (["all"], "whateveryouwant", True),
        (["terminal"], "stageterminal25", True),        
    ])
    def test_isHostType(self, types, hostname, expected):
        actual = devopsuseful.isHostType(types, hostname)
        assert expected == actual

    @stcheck.mark.parametrize("levels, hostname, expected", [
        ([], "stageloadbalancer50", False),
        ("prod", "prodmailserver4", True),
        (["dev", ",", "jeff"], "developer1", True),
        (8, "devrepository2", False),
        (["all"], "whateveryouwant", True),
        (["prod"], "prodterminal22", True),
    ])
    def test_isHostLevel(self, levels, hostname, expected):
        actual = devopsuseful.isHostLevel(levels, hostname)
        assert expected == actual

    @stcheck.mark.parametrize("hostname, expected, expectedException", [
        ("stageloadbalancer50", ("stage", "loadbalancer", 50), None),
        ("prodmailserver4", ("prod", "mailserver", 4), None),
        ("dev1", ("dev", "dev", 1), None),
        ("dev22", ("dev", "dev", 22), None),
        ("build3", ("build", "build", 3), None), # TODOPUPPET maybe terminal/build should still be level dev? What about build3 on the stage branch? Or should we rename it stagebuild3 and devbuild1 (with devdev1 as the new name for dev boxes or perhaps use devstpp)
        ("terminal21", ("terminal", "terminal", 21), None), # TODOPUPPET maybe terminal/build should still be level dev?
        ("buildstpay3", ("build", "stpay", 3), None),
        ("stub18", None, Exception(r"Unexpected hostname \(stub18\). Doesn't follow naming convention")),
        ("devloadbalancer2", ("dev", "loadbalancer", 2), None),
        ("devterminal222", ("dev", "terminal", 222), None),
    ])
    def test_splitHostname(self, hostname, expected, expectedException):
        with stcheck.raises(expectedException):
            actual = devopsuseful.splitHostname(hostname)
        if expectedException is None:
            assert expected == actual

        assert devopsuseful.splitHostname(hostname=None) == devopsuseful.splitHostname(hostname=platform.node())

    @stcheck.mark.parametrize("command, kw, exception, expecteds", [
        (["cat", "/usr/local/devops/tests/data/utf8.txt"], {}, None, {"decoded":"A \xa310.99"}),
        (["cat", "/usr/local/devops/tests/data/utf8.txt"], {"encoding":"latin-1"}, None, {"decoded":"A \xc2\xa310.99"}),
        (["echo"], {}, None, {"decoded":""}),
        (["echo"], {"split":"\n"}, None, {"decoded":"", "split":[]}),
        (["echo", "test"], {"split":"\n"}, None, {"decoded":"test", "split":["test"]}),
        (["junk", "command"], {}, FileNotFoundError("No such file or directory"), {}),
        (["junk", "command"], {"check":False}, FileNotFoundError("No such file or directory"), {}), # check=False still raises for a non-existant command. TODO maybe we don't want that? useful.runCommand doesn't
        (["cat", "/tmp/idonotexist.txt"], {}, subprocess.CalledProcessError, {}),
        (["cat", "/tmp/idonotexist.txt"], {"check":False}, None, {"decoded":"cat: /tmp/idonotexist.txt: No such file or directory"}),
        (["echo", "test1"], {}, None, {"decoded":"test1"}),
        (["echo", "test1"], {"stdout":None}, None, {"decoded":None}),
    ])
    def test_runCommand(self, command, kw, exception, expecteds):
        with stcheck.raises(exception):
            actual = devopsuseful.runCommand(command, **kw)
            if exception is None:
                assert expecteds, "Test doesn't do anything!"
            for attr, expected in expecteds.items():
                assert expected == getattr(actual, attr, None)
