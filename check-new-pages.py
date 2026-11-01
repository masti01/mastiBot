#!/usr/bin/python
"""

Call:
    pwb check-new-pages.py -ns:0 -newpages -pt:0 -always

This is a bot to check new articles:
* if no categories: add {{Dopracowac|kategoria=YYYY-MM}}
* if no wikilinks: add {{Dopracować|linki=YYYY-MM}}
# * if no refs: add {{Dopracować|przypisy=YYYY-MM}}

{{Dopracować}} has to be once per page: combine with already existing

Use global -simulate option for test purposes. No changes to live wiki
will be done.

-always           If used, the bot won't ask if it should file the message
                  onto user talk page.
-summary:         Set the action summary message for the edit.

Use global -simulate option for test purposes. No changes to live wiki will be done.

"""

#TODO: move to mwparserfromhell from textlib

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot, CurrentPageBot

from datetime import datetime
import re
from pywikibot import textlib

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# list of category adding templates
tmplcat = {
    'aktualne wydarzenie sportowe',
    'animanga infobox/anime',
    'animanga infobox/druk',
    'animanga infobox/film',
    'animanga infobox/ova',
}

class MyBot(CurrentPageBot):

    summary_key = 'basic-changing'
    use_redirects = False

    update_options = {
        'summary': None, #  No default edit summary
        'test': False,  # switch on test functionality
    }

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        #TODO: replace regex with mwpfh filter refs
        refR = re.compile(r'(?P<all><ref[^>]*?>)')
        # clenaupR = re.compile(r'(?i){{dopracować.*?}}')

        text = self.current_page.text

        #TODO: move to class level
        links = {'links': 0,
                 'cat': 0,
                 'template': 0,
                 'infobox': 0,
                 'refs': 0,
                 'dopracować': False
                 }
        # cleanupTmpl = False
        summary = []

        if self.current_page.isRedirectPage():
            pywikibot.output(u'Page %s is REDIRECT!' % self.current_page.title())
            return
        elif self.current_page.isDisambig():
            pywikibot.output(u'Page %s is DISAMBIG!' % self.current_page.title())
            return
        elif "{{ek" in self.current_page.text.lower():
            pywikibot.output(u'Page %s is to be DELETED!' % self.current_page.title())
            return
        else:
            if self.opt.test:
                pywikibot.output(u'Title:%s' % self.current_page.title())
                pywikibot.output(u'Depth:%s' % self.current_page.depth)
            for l in self.current_page.linkedPages(namespaces=0):
                if self.opt.test:
                    pywikibot.output(u'Links to:[[%s]]' % l.title())
                links['links'] += 1
                # pywikibot.output(u'Links:%s' % len(list(self.current_page.linkedPages(namespaces=0))))
            for t, p in textlib.extract_templates_and_params(text, remove_disabled_parts=True):
                if self.opt.test:
                    pywikibot.output('Template:[[%s]]' % t)
                links['template'] += 1
                if 'infobox' in t:
                    links['infobox'] += 1
                if 'dopracować' in t.lower():
                    links['dopracować'] = True
                if t.lower() in tmplcat:  # check for category adding templates
                    links['cat'] += 1
                    if self.opt.test:
                        pywikibot.output('Current cat#%i' % links['cat'])
                    # cleanupTmpl = (t, p)
                # if 'rok w' in t or 'Rok w' in t:
                #     links['cat'] += 1

            for c in textlib.getCategoryLinks(text):
                if self.opt.test:
                    pywikibot.output('Category:%s' % c)
                links['cat'] += 1
                if self.opt.test:
                    pywikibot.output('Current cat#%i' % links['cat'])
            for r in refR.finditer(text):
                if self.opt.test:
                    pywikibot.output('Ref:%s' % r.group('all'))
                links['refs'] += 1
            if self.opt.test:
                pywikibot.output('Links=%s' % links)
                # pywikibot.output('Cleanup=%s' % re.sub('\n','',textlib.glue_template_and_params(cleanupTmpl)))

        if links['dopracować']:
            if self.opt.test:
                pywikibot.output('Cleanup Tmpl FOUND')
        else:
            # add {{Dopracować}}
            t = 'Dopracować'  # template title
            p = {}  # template params
            today = datetime.now()
            datestr = today.strftime('%Y-%m')
            if self.opt.test:
                pywikibot.output('Date:%s' % datestr)
            if not (links['links'] and links['cat']):
                if not links['links']:
                    p['linki'] = datestr
                    summary.append('linki')
                if not links['cat']:
                    p['kategoria'] = datestr
                    summary.append('kategorie')
                if not links['refs']:
                    p['przypisy'] = datestr
                    summary.append('przypisy')
            cleanup_tmpl = (t, p)

            if not p:
                if self.opt.test:
                    pywikibot.output('Nothing to add')
                return

            if self.opt.test:
                pywikibot.output('Cleanup Tmpl TO ADD')
                pywikibot.output('summary:%s' % summary)
                pywikibot.output('params:%s' % p)
            text = re.sub('\n', '', textlib.glue_template_and_params(cleanup_tmpl)) + '\n' + text

            # if summary option is None, it takes the default i18n summary from
            # i18n subdirectory with summary_key as summary key.
            self.put_current(text,
                             summary=f'Sprawdzanie nowych stron: w artykule należy dopracować: {','.join(summary)}')

def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Option parsing
    local_args = pywikibot.handle_args(args)  # global options

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process pagegenerators arguments
    local_args = gen_factory.handle_args(local_args)  # generators options

    # Parse your own command line arguments
    for arg in local_args:
        opt, sep, value = arg.partition(':')
        opt = opt[1:]
        if opt in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + opt)
            options[opt] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[opt] = True
    MyBot(generator=gen_factory.getCombinedGenerator(), **options).run()

if __name__ == '__main__':
    main()