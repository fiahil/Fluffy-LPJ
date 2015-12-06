#!/usr/bin/python
#coding: utf-8

import os, sys, re
import subprocess
import logging as log
from datetime import datetime, timedelta
from BeautifulSoup import BeautifulSoup as BS

try:
    import eventlet
    from eventlet.green import urllib2
except ImportError:
    import urllib2

URL_PROGS = 'http://www.canalplus.fr/rest/bootstrap.php?/bigplayer/getMEAs/%s'
URL_VIDEO = 'http://www.canalplus.fr/rest/bootstrap.php?/bigplayer/getVideos/%s'
QUAL      = {1: 'mobile',
             2: 'bas_debit',
             3: 'haut_debit',
             4: 'hd',
             5: 'hds',
             6: 'hls',
             }
PROGLIST  = [
#             (130,     'act',  "Action discrete"),
#             (304,     '',     "Action discrete"),
#             (371,     '',     "Action discrete"),
#             ( 62,     'bdj',  "Le boucan du jour"),
#             (627,     '',     "Bref"),
             (104,      'lgj',  "Le grand journal"),
             (254,      'gro',  "Groland"),
             ( 48,      'gdi',  "Guignols de l'info (les)"),
#             (242,     'hoc',  "Du hard ou du cochon"),
#             (451,     'jcc',  "Jamel comedy club"),
             (896,      'jdh',  "Le journal du hard"),
#             ( 39,     'mat',  "La matinale"),
#             (215,     'mdh',  "Le meilleur du hier"),
#             ( 47,     'pdn',  "Les pépites du net"),
             (249,      'lpj',  "Petit journal (le)"),
#             (843,     'qdp',  "La question de plus"])
#             (294,     'cel',  "La revue de presse de Catherine et Eliane"),
#             (1082,    'slt',  "Salut les terriens"),
#             ( 41,     '',     "Salut les terriens"),
#             ( 74,     '',     "Salut les terriens"),
#             (105,     '',     "Salut les terriens"),
#             (110,     '',     "Salut les terriens"),
#             (316,     '',     "Salut les terriens"),
#             (371,     '',     "Salut les terriens"),
#             (680,     '',     "Salut les terriens - edito de Blako"),
#             (1064,    '',     "Salut les terriens - Gaspard Proust"),
#             (1072,    '',     "Salut les terriens - les martiens de la semaine"),
#             (252,     'sav',  "SAV des émissions"),
#             (936,     'tec',  "Tweet en clair"),
             (201,      'zap',  "Zapping (le)"),
            ]

PROGS = {P[1]:(P[0],P[2]) for P in PROGLIST}

# generate list from printer-like ranges
fromrange = lambda s: list(a for b in (range(int(x[0]),int(x[-1])+1) for x in [y.split('-') for y in s.split(',') if s]) for a in b)

def get_videos(id):
    """Generates list of videos for program"""
    log.debug('Opening "%s"' % (URL_PROGS % id))
    soup = BS(urllib2.urlopen(URL_PROGS % id))
    videos = []
    for mea in soup.findAll('mea'):
        videos.append( {'id': mea.find('id').text,
                       'title': mea.find('titre').text,
                       'subtitle': mea.find('sous_titre').text,
                       })
    return videos

def get_video_info(id, show=None):
    """Get infos and URL for a given video"""
    soup = BS(urllib2.urlopen(URL_VIDEO % id))
    log.debug('Opening "%s"' % (URL_VIDEO % id))
    d = datetime.strptime(soup.find('date').text, '%d/%m/%Y').strftime('%Y-%m-%d')
    try:
        duration = int(soup.find('duration').text)
    except ValueError:
        duration = None
    video = {'id': int(id),
             'show': show,
             'date': d,
             'title': soup.find('titre').text.replace('/', '-'),
             'subtitle': soup.find('sous_titre').text.replace('/', '-'),
             'duration': duration,
             'urls': {},
             }
    for (q, i) in QUAL.items():
        try:
            video['urls'][q] = soup.find(i).text
        except AttributeError:
            pass
#    return soup
    return video

def video_list(id, limit=None, datelimit=None):
    """Builds video list for program"""
    try:
        show = id
        id = PROGS[id][0]
    except KeyError:
        log.error('Invalid show "%s" (Available shows are "%s")' % (show, '", "'.join(sorted(PROGS))))
        show = id
    videos = get_videos(id)
    if videos:
        log.info('Found %s video(s) info for "%s"' % (len(videos), show))
    if limit:
        videos = videos[:limit]
    ids = [v['id'] for v in videos ]
    # asynchronously download video infos
    pool = eventlet.GreenPool()
    videos = []
    for video in pool.imap(lambda i: get_video_info(i, show), ids):
        if datelimit and video['date'] and video['date'] < datelimit:
            log.debug('Reached date limit: %s < %s' % (video['date'], datelimit))
            break
        videos.append(video)
    # make sure videos are sorted by date
    videos.sort(key=lambda x:x['date'])
    videos.reverse()
    olddate = ''
    for video in videos:
        if video['date'] == olddate:
            n += 1
        else:
            olddate = video['date'] ; n = 0
        video['n'] = n
    return videos

def download_video(url, out, duration=None, resume=False, quiet=False):
    import fcntl
    """Downloads video"""
    log.info('Downloading "%s" (%s)' % (out, url))
    if url.startswith('rtmp://'):
        RESUME = ('-e' if resume else '')
        QUIET  = ('-q' if quiet  else '')
        p = subprocess.Popen(('rtmpdump', RESUME, QUIET, '-r', url, '-o', out))
        p.wait()
#        p1 = subprocess.Popen(('rtmpdump', RESUME, QUIET, '-r', url, '-o', out), stderr = subprocess.PIPE, close_fds=True)
#        while p1.poll() is None:
#            out = p1.stderr.read(32)
#            if out == '' and p1.poll() != None:
#                break
#            if 'kB /' in out:
#                sys.stdout.write(out)
#                sys.stdout.flush()
    elif url.endswith('.m3u8'):
        cmd_args = ['avconv', '-i', url, '-ss', '00:00:00']
        if duration:
            cmd_args.extend(['-t', str(duration)])
        print "outing" + out
        cmd_args.extend(['-codec', 'copy', out])
        p = subprocess.Popen(cmd_args)
        p.wait()
    else:
        with open(out, 'w') as f:
            f.write(urllib2.urlopen(url))

if __name__ == '__main__':
    import argparse

    log.basicConfig(level=log.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=os.path.expanduser('.cpdl.log'),)
    stdoutLog = log.StreamHandler(stream=sys.stdout)
    stdoutLog.setFormatter(log.Formatter("[%(levelname).1s]  %(message)s"))
    stdoutLog.setLevel(log.ERROR)
    log.getLogger().addHandler(stdoutLog)

    parser = argparse.ArgumentParser(description='Download videos from Canal+')
#    parser.add_argument('-s', '--show', nargs='+', help='Show(s) to download')
    parser.add_argument('--shows', action='store_true', help='List available shows')
    parser.add_argument('show', metavar='SHOW', nargs='*', help='Show(s) to download')
    parser.add_argument('-i', '--list', action='store_true', help='Display available videos')

    group_time = parser.add_mutually_exclusive_group()
    group_time.add_argument('-t', '--today', action='store_true', help="Download today's videos")
    group_time.add_argument('-y', '--yesterday', action='store_true', help="Download yesterday's videos")
    group_time.add_argument('-l', '--last', metavar='N', type=int, nargs='?', help="Download last (N) videos", const=1)
    group_time.add_argument('-x', '--videos', metavar='XXX', type=str, help="Download given videos (1,2-4,7)")
    def validDate(d): # validation for the date format (YYYY-MM-DD)
        import re
        try:
            return re.match('\d{4}-\d\d-\d\d', d).group(0)
        except AttributeError:
            raise argparse.ArgumentTypeError('String "%s" does not match required format (YYYY-MM-DD)' % (d,))
    group_time.add_argument('-m', '--max-date', metavar='date', type=validDate, nargs=1, help="Download videos more recent than <date> (YYYY-MM-DD)")

    group_log = parser.add_mutually_exclusive_group()
    group_log.add_argument('-v', '--verbose', action='count', default=2, help='Verbosity (add several to increase)')
    group_log.add_argument('-V', '--quiet', action='store_true', help='No output')

    parser.add_argument('-f', '--format', metavar='XXX', help='Filename format (default "%%S_%%d_%%t(%%Q).%%e")\n' +
                                                              '%%S SHOW, %%s show, %%D YYYY-MM-DD, %%d YYYYMMDD, ' +
                                                              '%%T title, %%t subtitle, %%e .ext, %%n video number (same date), ' +
                                                              '%%q quality (1–4), %%Q quality (200-1500k)',  default='%S_%d_%t(%Q).%e')
    parser.add_argument('-q', '--quality', metavar='N', type=int, help='Quality (1–4)', default=6)
    parser.add_argument('-n', '--no-act', action='store_true', help='Dry run (do not download videos)')
    parser.add_argument('-P', '--play', action='store_true', help='Play video with vlc')
    parser.add_argument('-r', '--resume', action='store_true', help='Resume interrupted download')
    parser.add_argument('--no-sort', action='store_true', help='Do not download the newest videos first (group by show)')

    args = parser.parse_args()
    stdoutLog.setLevel(log.ERROR-10*min(args.verbose,3)) # set log level for stdout (v: WARN; vv: INFO; vvv+: DEBUG)
    args.quiet and stdoutLog.setLevel(log.CRITICAL)      # if quiet, set log level to CRITICAL
    if args.shows:
#        log.error('Available shows are "%s"' % ('", "'.join(sorted(PROGS))))
        log.error('Available shows are %s' % ', '.join(['"%s" (%s)' % (s[0], s[1][1]) for s in sorted(PROGS.items())]))
        sys.exit()
    log.debug(args)

    # Let's start serious stuff
    if args.show:
        shows_infos = {}
        log.debug('Downloading infos for shows "%s)' % '), "'.join(['%s" (%s' % (P, PROGS[P][1]) for P in args.show if P in PROGS]))
        videos = []
        for show in args.show:
            show = show.lower()
            limit = None ; datelimit = None
            if args.today:
                limit = 3 # max 3 videos per day for one show
                datelimit = datetime.today().strftime('%Y-%m-%d')
            if args.yesterday:
                limit = 6 # max 3 videos per day for one show
                datelimit = (datetime.today()-timedelta(1)).strftime('%Y-%m-%d')
            elif args.last:
                limit = args.last
            elif args.max_date:
                datelimit = args.max_date[0]
            v = video_list(show, limit, datelimit)
            if not ((args.today or args.yesterday) and v and v[0]['date'] != datelimit):
                videos.extend(v)
            log.debug('Retrieved infos for %s videos%s' % (len(videos),
                                                            (' (max-date: %s)' % datelimit if datelimit else
                                                             ' (limit: %s)' % limit if limit else '')))
        # sort by date so that the newest videos are downloaded first
        if not args.no_sort:
            videos.sort(key=lambda x:x['date'], reverse=True)
        log.info('%s video(s) to download' % len(videos))

        if args.videos:
            vrange = fromrange(args.videos)
            if not args.last:
                args.last = max(vrange)

        i = 0
        Q = {1: '200k', 2: '400k', 3: '800k', 4: '1500k', 5:'HDS', 6:'HLS' }
        if args.list:
           for v in videos:
                i+=1
                if args.videos and i not in vrange:
                    continue
                print(u'[%s] %s (%s) %s "%s – %s"' % (i, v['date'], v['id'], v['show'].upper(), v['title'], v['subtitle']))
                q = max(1,min(args.quality, 6))
                url = v['urls'][q]
                log.debug('Download URL "%s"' % url)
        else:
            for v in videos:
                i+=1
                if args.videos and i not in vrange:
                    continue
                q = max(1,min(args.quality, 6))
                url = v['urls'][q]
                ext = url.rsplit('.', 1)[-1]
                filename = args.format.replace('%S', v['show'].upper()).replace('%s', v['show']).replace('%D', v['date']).replace('%e', ext).replace('%T', v['title']).replace('%t', v['subtitle'])
                filename = filename.replace('%d', v['date'].replace('-', '')).replace('%q', str(q)).replace('%Q', Q[q]).replace('%n', '-%s' % v['n'] if v['n'] else '')
                filename = re.sub(r'\s+', '_', filename)
                filename = filename.replace('.m3u8', '.mp4')
                filename = os.path.expanduser(filename)
                if os.path.exists(filename) and not os.path.getsize(filename):
                   os.remove(filename)
                   log.info('Deleting empty file "%s"' % filename)
                if args.play:
                    p = subprocess.Popen(('vlc', url))
                    p.wait()
                elif args.resume or not os.path.exists(filename):
                    if args.resume and os.path.exists(filename):
                        log.info('Resuming downloading video "%s" from show "%s" as "%s"' % (v['id'], v['show'], filename))
                    else:
                        log.info('Downloading video "%s" from show "%s" as "%s"' % (v['id'], v['show'], filename))
                    log.debug('Download URL "%s"' % url)
                    if not args.no_act:
                        download_video(url, filename, duration=v['duration'], resume=args.resume, quiet=args.quiet)
                else:
                    log.info('NOT downloading video "%s" from show "%s", file already exists: "%s"' % (v['id'], v['show'], filename))

