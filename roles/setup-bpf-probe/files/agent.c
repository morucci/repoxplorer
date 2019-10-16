/* Copyright 2019 Red Hat

   Licensed under the Apache License, Version 2.0 (the "License"); you may
   not use this file except in compliance with the License. You may obtain
   a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
   License for the specific language governing permissions and limitations
   under the License. */

#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct pid_info_t {
  u64 start_time;
  u32 cgroup;
  char comm[TASK_COMM_LEN];
};

BPF_TABLE("hash", pid_t, struct pid_info_t, pid_infos, 4096);
BPF_TABLE("hash", pid_t, u64, oncpus, 4096);

// Each time the scheduler switch a process this function get called
int sched_switch(struct pt_regs *ctx, struct task_struct *prev)
{
  // The current kernel time
  u64 ts = bpf_ktime_get_ns();
  pid_t prev_pid = prev->pid;

  // First let's record info about the next pid (the current one) to be scheduled
  pid_t cur_pid = bpf_get_current_pid_tgid();
  struct pid_info_t *pid_info = pid_infos.lookup(&cur_pid);
  if (pid_info == NULL) {
    // This is the first time we see that pid, collect cgroup and comm name
    struct pid_info_t new_pid_info = {};
    new_pid_info.cgroup = bpf_get_current_cgroup_id() & 0xffffffff;
    if (new_pid_info.cgroup == 0 || new_pid_info.cgroup == 1) {
      // Skip global cg
    }
    new_pid_info.start_time = ts;
    bpf_get_current_comm(&new_pid_info.comm, sizeof(new_pid_info.comm));
    pid_infos.update(&cur_pid, &new_pid_info);
  } else {
    // Reset the start_time of that pid
    pid_info->start_time = ts;
  }

  // Then count time for the previous process
  //if (prev->state == TASK_RUNNING) {
  struct pid_info_t *prev_info = pid_infos.lookup(&prev_pid);
  if (prev_info != NULL) {
    u64 delta = ts - prev_info->start_time;
    // We know about that process, let's update it's time
    u64 *oncpu = oncpus.lookup(&prev_pid);
    if (oncpu == NULL) {
      oncpus.update(&prev_pid, &delta);
    } else {
      *oncpu += delta;
    }
  } //}
  return 0;
}
