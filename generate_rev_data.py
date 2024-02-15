#!/usr/bin/python3


'''
generate a table of rev id number vs time in 1 million revision increments,
suitable for feeding to gnuplot to chart project growth.
'''


import getopt
import json
import sys
import time
import requests


def usage(message=None):
    '''
    display a nice usage message along with an optional message
    describing an error
    '''
    if message:
        sys.stderr.write(message + "\n")
    usage_message = """Usage: $0 --domain [--startrev <num>] [--endrev <num>]
       [--dryrun] [--verbose]
or: $0 --help

Retrieve revision information in a format that can be fed to gnuplot to generate
a graph showing the increase in the number of revisions over time.

Arguments:

 --domain   (-d):  fqdn of wiki from which to retrieve data. e.g. en.wikipedia.org
 --startrev (-s):  starting rev_id; default 1
 --endrev   (-e):  ending rev_id; default the current maximum revid

Flags:

 --dryrun  (-d):  write the commands that would have been run instead of running them
 --verbose (-v):  write some progress messages some day
 --help    (-h):  show this help message
"""
    sys.stderr.write(usage_message)
    sys.exit(1)


def get_default_opts():
    '''
    initialize args with default values and return them
    '''
    args = {'domain': None, 'start_rev': '1', 'end_rev': None, 'dryrun': False, 'verbose': False}
    return args


def check_opts(args):
    '''
    whine if mandatory args not supplied, or if numeric ones aren't
    '''
    if 'domain' not in args or not args['domain']:
        usage("The argument 'domain' must be specified and may not be empty.")
    if not args['start_rev'].isdigit():
        usage("The 'startrev' argument must be a number.")
    if args['end_rev'] and not args['end_rev'].isdigit():
        usage("The 'endrev' argument must be a number.")
    if not args['end_rev']:
        args['end_rev'] = get_max_rev(args['domain'])


def process_opts():
    '''
    get command-line args and values, falling back to defaults
    where needed, whining about bad args
    '''
    try:
        (options, remainder) = getopt.gnu_getopt(
            sys.argv[1:], "d:e:s:Dvh",
            ["domain=", "startrev=", "endrev=",
             "dryrun", "verbose", "help"])

    except getopt.GetoptError as err:
        usage("Unknown option specified: " + str(err))

    args = get_default_opts()

    for (opt, val) in options:
        if opt in ["-d", "--domain"]:
            args['domain'] = val
        elif opt in ["-e", "--endrev"]:
            args['end_rev'] = val
        elif opt in ["-s", "--startrev"]:
            args['start_rev'] = val
        elif opt in ["-D", "--dryrun"]:
            args['dryrun'] = True
        elif opt in ["-v", "--verbose"]:
            args['verbose'] = True
        elif opt in ["-h", "--help"]:
            usage('Help for this script\n')
        else:
            usage("Unknown option specified: <%s>" % opt)

    if remainder:
        usage("Unknown option(s) specified: {opt}".format(opt=remainder[0]))

    check_opts(args)
    return args


def get_revids_url(domain, revids):
    '''
    return url and params that will let us get info about the specified list of revisions
    via the mediawiki api for the specified domain
    '''
    #https://en.wikipedia.org/w/api.php?action=query&list=recentchanges&format=json
    base = '/w/api.php'
    url = 'https://' + domain + base
    params = {'action': 'query', 'prop': 'revisions', 'revids': '|'.join(revids),
              'rvprop': 'ids|timestamp', 'format': 'json'}
    return url, params


def get_session():
    '''
    get an open session for making requests
    '''
    sess = requests.Session()
    sess.headers.update(
        {"User-Agent": "generate_rev_data.py/0.0 (ops-dumps@wikimedia.org)",
         "Accept": "application/json"})
    return sess


def get_revinfo_from_json(content):
    '''
    given json output from mediawiki api for revision info,
    get the revids and timestamps out of the results and
    return them
    if there's no revid in the content or it can't be parsed,
    return None
    '''
    revid_timestamp = {}
    try:
        revinfo = json.loads(content)
        badrevs = []
        if 'badrevids' in revinfo['query']:
            badrevs = list(revinfo['query']['badrevids'].keys())
        # print(revinfo)
        if 'pages' not in revinfo['query']:
            # all the revs were bad I guess
            return {}

        for page in revinfo['query']['pages']:
            revisions = revinfo['query']['pages'][page]['revisions']
            for revision in revisions:
                revid_timestamp[revision['revid']] = revision['timestamp']
                # print(revision['revid'], revision['timestamp'])
        return revid_timestamp, badrevs
    except Exception:
        return None


def get_maxrev_url(domain):
    '''
    return the url to retrieve the max rev id for the given
    domain via the mw api
    '''
    base = '/w/api.php'
    url = 'https://' + domain + base
    params = {'action': 'query', 'list': 'allrevisions', 'arvlimit': '1',
              'arvdir': 'older', 'format': 'json'}
    return url, params


def get_revid_from_json(content):
    '''
    given json response from mw api that should contain a rev id,
    extract and return it
    '''
    try:
        revinfo = json.loads(content)
        revisions = []
        for entry in revinfo['query']['allrevisions']:
            revisions.extend(entry['revisions'])
        if len(revisions) != 1:
            return None
        revid = revisions[0]['revid']
        return revid
    except Exception:
        return None


def get_max_rev(domain):
    '''
    get the max rev id for the specified domain and return
    it as an int
    '''
    sess = get_session()
    url, params = get_maxrev_url(domain)
    response = sess.get(url, params=params, timeout=5)
    if response.status_code != 200:
        sys.stderr.write("failed to get revid for %s\n" % url)
        return None
    revid = get_revid_from_json(response.content)
    return revid


def get_revinfo(revids, domain):
    '''
    get revision information for the specified revids at the
    given domain
    if we can't get a good response, return None
    '''
    sess = get_session()
    url, params = get_revids_url(domain, revids)
    response = sess.get(url, params=params, timeout=5)
    if response.status_code != 200:
        sys.stderr.write("failed to get revid for %s\n" % url)
        return None
    revinfo, badrevs = get_revinfo_from_json(response.content)
    return revinfo, badrevs


def display_revinfo(revinfo):
    '''
    print rev id and timestamp for each revision in some nice format
    '''
    revids = sorted(list(revinfo.keys()))
    for revid in revids:
        print(revid, revinfo[revid])


def do_revrange(revrange, domain):
    '''
    get revinfo for a list of revisions
    '''
    redo = []
    batch = [str(revid) for revid in revrange[:10]]
    while batch:
        revinfo, badrevs = get_revinfo(batch, domain)
        redo.extend(badrevs)
        display_revinfo(revinfo)
        revrange = revrange[10:]
        batch = [str(revid) for revid in revrange[:10]]
        if not batch:
            break
        time.sleep(5)
    return redo


def do_main():
    '''
    entry point
    '''
    args = process_opts()
    if args['verbose']:
        print("running with arguments:", args)
    revrange = range(int(args['start_rev']), int(args['end_rev']), 10000000)
    redo = do_revrange(revrange, args['domain'])
    if redo:
        time.sleep(5)
    while redo:
        new_range = [str(int(rev) + 1) for rev in redo]
        redo = do_revrange(new_range, args['domain'])


if __name__ == '__main__':
    do_main()
