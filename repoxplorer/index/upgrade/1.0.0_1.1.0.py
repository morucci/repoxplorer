import os
import sys
import copy
import yaml

# Projects definition changed between version 1.0.0 and 1.1.0
# This script update project definition structure

if __name__ == '__main__':
    dirp = sys.argv[1]
    if not os.path.isdir(dirp):
        print("Is not a directory")
        sys.exit(1)
    for r, d, f in os.walk(dirp):
        for _f in f:
            if _f.endswith('yaml') or _f.endswith('yml'):
                p = os.path.join(r, _f)
                data = yaml.load(file(p))
                print(("Read %s" % p))
                ndata = copy.deepcopy(data)
                if "projects" not in data:
                    continue
                for pid, pd in list(data['projects'].items()):
                    if "repos" in pd:
                        print(("Skip %s from file %s. Format OK." % (pid, _f)))
                        continue
                    repos = copy.deepcopy(pd)
                    pd = {
                        "repos": repos,
                        "description": "",
                    }
                    ndata['projects'][pid] = pd
                print(("write %s" % p))
                yaml.dump(ndata, file(p, 'w'),
                          default_flow_style=False)
        # We not explore in subdirs
        break
