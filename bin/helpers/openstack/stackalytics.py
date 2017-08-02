import sys
import json
import yaml
import datetime

# Read default_data.json from stackalytics/etc/ and convert for
# repoXplorer.

if __name__ == "__main__":
    ident = {'identities': {},
             'groups': {}}
    data = json.loads(file(sys.argv[1]).read())
    users = data['users']
    groups = data['companies']
    i = ident['identities']
    g = ident['groups']
    gstore = {}
    for group in groups:
        gstore[group['company_name']] = group['domains']
    for user in users:
        try:
            i[user['launchpad_id']] = {}
            iu = i[user['launchpad_id']]
        except:
            try:
                i[user['github_id']] = {}
                iu = i[user['github_id']]
            except:
                continue
        sys.stdout.write('.')
        iu['name'] = user['user_name']
        iu['default-email'] = user['emails'][0]
        iu['emails'] = {}
        for email in user['emails']:
            iu['emails'].setdefault(email, {})
            histo = []
            for c in user['companies']:
                iu['emails'][email].setdefault('groups', {})
                iu['emails'][email]['groups'][c['company_name']] = {}
                # cd = iu['emails'][email]['groups'][c['company_name']]
                g.setdefault(
                    c['company_name'], {
                        'description': '',
                        'emails': {},
                        'domains': gstore.get(c['company_name'], [])
                    })
                if c['end_date'] is not None:
                    end_date_raw = datetime.datetime.strptime(
                        c['end_date'], '%Y-%b-%d')
                    histo.append([None, end_date_raw, c['company_name']])
                else:
                    histo.append([None, None, c['company_name']])
            histo.sort(key=lambda tup: tup[1] or datetime.datetime.today())
            for z, h in enumerate(histo):
                if z == 0:
                    pass
                h[0] = histo[z-1][1]
                cd = iu['emails'][email]['groups'][h[2]]
                if h[0]:
                    cd['begin-date'] = h[0].strftime('%Y-%m-%d')
                if h[1]:
                    cd['end-date'] = h[1].strftime('%Y-%m-%d')

    path = 'test.yaml'
    with open(path, 'w') as fd:
        fd.write(yaml.safe_dump(ident,
                                default_flow_style=False))
