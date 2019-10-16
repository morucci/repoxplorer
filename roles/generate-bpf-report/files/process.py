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

from argparse import ArgumentParser
from collections import OrderedDict
from dataclasses import dataclass
from json import load
from typing import Any, Dict, List, Optional, Set, Tuple
from statistics import mean

def usage():
    parser = ArgumentParser()
    parser.add_argument("result")
    return parser.parse_args()


@dataclass
class PidInfo:
    name: str
    pid: int

    def shortName(self) -> str:
        return f"{self.name}[{self.pid}]"


@dataclass
class CgroupInfo:
    name: str
    pids: List[PidInfo]
    pos: int = 0

    def shortName(self) -> str:
        name = self.name
        if len(name) > 42:
            name = self.name.split('/')[0] + '/'
            name = name + self.name[(-1 * (38 - len(name))):]
        return name


@dataclass
class Model:
    cgroups: Dict[int, CgroupInfo]
    cpus: List[List[Tuple[int, int]]]

mean_cpu: float = 1
def process(events: List[Any]) -> Model:
    # Normalize json list to a structured map
    m = Model(OrderedDict(), [])
    cpus: List[int] = []
    for event in events:
        if event.get("ts") is not None:
            m.cpus.append([])
        elif event.get("cgr"):
            m.cgroups[event["cgr"]] = CgroupInfo(event["v"], [])
        elif event.get("pid") is not None:
            m.cgroups[event["c"]].pids.append(PidInfo(event["v"], pid=event["pid"]))
        elif event.get("cpu") is not None:
            m.cpus[-1].append((event["cpu"], event["v"]))
            cpus.append(event["v"])
        elif event:
            raise RuntimeError("unknown event: %s" % event)
    global mean_cpu
    mean_cpu = mean(cpus)
    return m


def rect(x: int, y: int, w: int, h: int, color: str) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" />'


def text(x: int, y: int, text: str, color: str, anchor: Optional[str] = None) -> str:
    extra = ""
    if anchor:
        extra += f' text-anchor="{anchor}"'
    return f'<text x="{x}" y="{y}" font-size="12" fill="{color}"{extra}>{text}</text>'

def boxText(x: int, y: int, w: int, h: int, s: str, bgColor: str, fgColor: str, rightAlign: bool = False) -> str:
    anchor = "end" if rightAlign else None
    return rect(x, y, w, h, bgColor) + text(
        x + w if rightAlign else x, y + LINE_HEIGHT - 3, s, fgColor, anchor=anchor
    )

LINE_HEIGHT = 13
STEP_SIZE = 50

@dataclass
class Cpu:
    step: int
    time: int

    def render(self, y: int) -> List[str]:
        global mean_cpu
        col = (min(190, int(180 * int(self.time * 90 / mean_cpu) / 100)), 10, 32)
        return [boxText(202 + self.step * STEP_SIZE, y, STEP_SIZE, LINE_HEIGHT, f"{self.time}ms",
                        "rgb({},{},{})".format(*col),
                        "rgb({},{},{})".format(*list(map(lambda x: 255 - x + 20, col))))]

@dataclass
class Pid:
    name: str
    pos: int
    cpus: List[Cpu]

    def render(self, y: int) -> Tuple[int, List[str]]:
        pid: List[str] = []
        y += self.pos * LINE_HEIGHT
        pid.append("<g>")
        pid.append(boxText(
            4, y, 196, LINE_HEIGHT, self.name, "gainsboro", "black", rightAlign=True))
        width = 0
        for cpu in self.cpus:
            pid.extend(cpu.render(y))
        pid.append("</g>")
        return 120, pid

@dataclass
class Cgroup:
    name: str
    pos: int
    pids: List[Pid]

    def render(self, y: int) -> Tuple[int, List[str]]:
        height = (len(self.pids) + 1) * LINE_HEIGHT
        width = 0
        cgroup: List[str] = []
        cgroup.append("<g>")
        cgroup.append(boxText(2, y, 200, height, self.name, "lightgrey", "blue"))
        for pid in self.pids:
            w, l = pid.render(y + LINE_HEIGHT)
            width = max(w, width)
            cgroup.extend(l)
        cgroup.append("</g>")
        return y + height + 2, cgroup

def render(m: Model) -> Tuple[int, int, List[str]]:
    result: List[str] = []
    pid_group: Dict[int, Pid] = {}
    cgroups: List[Cgroup] = []
    cgroup_pos = 0
    for cgroup_id, cgroup in m.cgroups.items():
        pids: List[Pid] = []
        pid_pos = 0
        for cpid in cgroup.pids:
            pid = Pid(cpid.shortName(), pid_pos, [])
            pid_group[cpid.pid] = pid
            pids.append(pid)
            pid_pos += 1
        cgroups.append(Cgroup(cgroup.shortName(), cgroup_pos, pids))
        cgroup_pos += 1
    for cpu_pos in range(len(m.cpus)):
        cpu = m.cpus[cpu_pos]
        for pid_num, cpu_time in cpu:
            pid_group[pid_num].cpus.append(Cpu(cpu_pos, cpu_time))

    height = 0
    for c in cgroups:
        height, res = c.render(height)
        result.extend(res)
    return height, 200 + STEP_SIZE * (cpu_pos + 2), result


args = usage()
model = process(load(open(args.result)))
height, width, boxes = render(model)
result = [
    f'<svg xmlns="http://www.w3.org/2000/svg" height="{height}" width="{width}">'
] + boxes + ['</svg>\n']

with open(args.result + ".svg", "w") as of:
    of.write("\n".join(result))
