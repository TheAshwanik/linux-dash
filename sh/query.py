import json
import shlex

import subprocess

class APIWriter(object):
    """
    I/O Abstraction layer.

    Exposes a "write" handler that accepts a JSON blob from the caller and writes it to a file.

    This could just as easily write to a database without the caller needing to be updated, though that may require
    coupling (either explicit or implicit) the IO later to the data collection layer in some way.
    """
    def __init__(self):
        self.dir = "../api"

    def write(self, metric, data):
        filename = "%s/%s.json" % (self.dir, metric)
        with open(filename, "w") as f:
            f.write(json.dumps(data, indent=2))

class SystemInfo(object):
    def __init__(self, api_writer):
        self.api = api_writer

    def run(self):
        self.ps()
        self.uptime()
        self.whereis()
        self.users()
        self.ip()
        self.issue()
        self.mem()
        self.top()
        self.df()
        self.hostname()

    def _exec(self, command, filter=None):
        proc = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if filter:
            output = subprocess.Popen(shlex.split(filter), stdin=proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
            stdout, err =  output.communicate()
        else:
            stdout, err = proc.communicate()

        return stdout

    def _write(self, metric, output):
        self.api.write(metric, output)


    def _list_to_json(self, blob, delim=","):
        data = blob.splitlines()
        data = [row.split(delim) for row in data]
        return data

    def ps(self):
        command = "ps aux"
        filter = "awk '{print $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11}'"
        result = self._exec(command, filter)
        output = self._list_to_json(result, delim=" ")

        # stripping ":" from the header row.
        output[0] = [col.replace(":","") for col in output[0]]
        self._write("ps", output)

    def test(self):
        command = "awk '{print $1*1000}' /proc/uptime"
        result = self._exec(command)
        output = int(result.strip()) / (1000*60*60)
        self._write("test", output)

    def uptime(self):
        command = "cat /proc/uptime"
        result = self._exec(command)
        system, idle = result.split(" ")
        output = int(float(system) / (60*60))
        self._write("uptime", output)

    def whereis(self):
        command = "whereis php mysql vim python ruby java apache2 nginx openssl vsftpd make, postgresql"
        filter = """awk '{ split($1, a, ":");if (length($2)==0) print a[1]",Not Installed"; else print a[1]","$2;}'"""
        result = self._exec(command, filter)
        output = self._list_to_json(result, delim=",")
        self._write("whereis", output)

    def users(self):
        command = "cat /etc/passwd"
        filter = """awk -F: '{ if ($3<=499) print "system",$1,$6; else print "user",$1,$6; }'"""
        result = self._exec(command, filter)
        output = self._list_to_json(result, delim=" ")
        self._write("users", output)

    def ip(self):
        # This one chains grep + two awks.  self._exec does not presently accept multiple filters.
        command = "/sbin/ifconfig | grep -B1 'inet addr' | awk ..."
        self._write("ip", [])

    def issue(self):
        command = "cat /etc/issue"
        result = self._exec(command)
        self._write("issue", result)

    def mem(self):
        command = "free -tmo"
        filter = "awk '{print $1,$2,$3,$4}'"
        result = self._exec(command, filter)
        output = self._list_to_json(result, delim=" ")
        self._write("mem", output[1])

    def top(self):
        # this one isn't implemented
        command = "top -b -n1"
        filter = "awk '{print $2}'"
        result = self._exec(command, filter)
        self._write("top", [])

    def hostname(self):
        command = "hostname"
        result = self._exec(command)
        self._write("hostname", result)

    def df(self):
        command = "df -h"
        filter = "awk '{print $1,$2,$3,$4,$5,$6}'"
        result = self._exec(command, filter)
        output = self._list_to_json(result, " ")
        self._write("df", output[1:])


if __name__ == "__main__":
    api = APIWriter()
    si = SystemInfo(api)
    si.run()


