# Copyright 2019 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from bcc import BPF
from time import sleep, strftime, monotonic
import os
import argparse
import signal

from typing import Dict, Set
from sys import argv, stdout, stderr


# Exit gracefully on sigterm
running = True
def sigterm(signum, frame):
    global running
    running = False

signal.signal(signal.SIGTERM, sigterm)


CGROUP_ID = int
CGROUP_NAME = str


def scan_cgroups() -> Dict[CGROUP_ID, CGROUP_NAME]:
    cgs = {}
    for w in os.walk("/sys/fs/cgroup"):
        d = w[0]
        cgs[os.stat(d).st_ino] = d[15:]
    return cgs

json = len(argv) == 2
if json:
    synced: Dict[str, Set[int]] = {
        "cg": set(),
        "pid": set(),
    }
    print('[')

cgs = scan_cgroups()
bpf = BPF(text=open(os.path.dirname(__file__) + "/agent.c").read())
bpf.attach_kprobe(event="finish_task_switch", fn_name="sched_switch")
pid_infos = bpf["pid_infos"]

now = monotonic()
try:
    while running:
        sleep(1)
        if not json:
            # print(chr(27) + "[2J")
            print("[%s]" % strftime("%H:%M:%S"))
        else:
            print('{"ts": %.2f},' % (monotonic() - now - 1))
        data = bpf["oncpus"]
        for k, v in sorted(data.items(), key=lambda kv: kv[1].value):
            pid_info = pid_infos[k]
            pid = k.value & 0xffffffff
            tid = k.value >> 32
            comm = pid_info.comm.decode('utf-8')
            cgid = pid_info.cgroup & 0xffffff
            if cgs.get(cgid) is None:
                cgs = scan_cgroups()
            ts = v.value / 1e6
            cgroup = cgs.get(cgid, "unknown")

            if not json:
                print("{cgroup} pid:{pid} task:{task} comm:{comm} time:{time}ms".format(
                    pid=pid,
                    task=tid,
                    comm=comm,
                    cgroup=cgroup,
                    time=ts,
                ))
            else:
                # Dump new info
                if cgid not in synced["cg"]:
                    print('{"cgr": %d, "v": "%s"},' % (cgid, cgroup.replace('\\', '\\\\')))
                    synced["cg"].add(cgid)
                if pid not in synced["pid"]:
                    print('{"pid": %d, "v": "%s", "c": %d},' % (pid, comm, cgid))
                    synced["pid"].add(pid)
                print('{"cpu": %d, "v": %.2f},' % (pid, ts))
#        if of is not None:
#            of.flush()
        data.clear()
finally:
    if json:
        print("{}]\n")
