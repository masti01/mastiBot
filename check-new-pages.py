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

#
# (C) masti, 2006-2026
#
# Distributed under the terms of the MIT license.
#

#TODO: move to mwparserfromhell from textlib

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import CurrentPageBot

from datetime import datetime

from mwparserfromhell import parse
from mwparserfromhell.nodes import Wikilink
from mwparserfromhell.wikicode import Wikicode

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

    @staticmethod
    def ek(parsed: Wikicode) -> bool:
        # templaete ek and synonims
        ekname = ("ek", "ekspresowe kasowanko", "usuń", "speedy", "delete")
        for t in parsed.filter_templates():
            if t.name.matches(ekname):
                return True
        return False

    @staticmethod
    def category(wikilink: Wikilink) -> bool:
        return wikilink.title.lower().startswith(("kategoria:", "category:"))

    @staticmethod
    def file(wikilink: Wikilink) -> bool:
        return wikilink.title.lower().startswith(("plik:", "file:"))

    def treat_page(self) -> None:

        if self.opt.test:
            pywikibot.output(f'Title:[[{self.current_page.title()}]]')
            pywikibot.output(f'Depth:{self.current_page.depth}')

        """ parse page for checks"""
        parsed = parse(self.current_page.text)

        #TODO: move to class level
        tests = {'links': 0,
                 'cat': 0,
                 'files': 0,
                 'template': 0,
                 'infobox': 0,
                 'refs': 0,
                 'dopracować': 0
                 }
        # cleanupTmpl = False
        summary = []

        if self.current_page.isRedirectPage():
            pywikibot.output(f'Skipping REDIRECT: [[{self.current_page.title()}]]')
            return
        elif self.current_page.isDisambig():
            pywikibot.output(f'Skipping DISAMBIG: [[{self.current_page.title()}]]')
            return
        if self.ek(parsed):  # page contains speedy delete template
            pywikibot.output(f'Skipping DELETE candidate: [[{self.current_page.title()}]]')
            return

        # Wikilinks
        wikilinks = parsed.filter_wikilinks()
        tests['links'] = len(wikilinks)
        if self.opt.test:
            pywikibot.output(f'Wikiinks count: {wikilinks}')

        # Templates
        for t in parsed.filter_templates():
            if self.opt.test:
                pywikibot.output(f'Template:[[{t}]]')
        tests['template'] = len(parsed.filter_templates())

        # infobox
        tests['infobox'] = len(
            parsed.filter_templates(matches=lambda tmpl: tmpl.name.lower().strip().endswith("infobox")))

        # dopracowć
        tests['dopracować'] = len(
            parsed.filter_templates(matches=lambda tmpl: tmpl.name.lower().strip().startswith("dopracować")))

        # References
        tests['refs'] = len(parsed.filter_tags(matches=lambda tag: tag.tag.lower() == "ref"))

        # Categories
        tests['cat'] = len(parsed.filter_wikilinks(matches=lambda link: self.category(link)))

        # Files
        tests['files'] = len(parsed.filter_wikilinks(matches=lambda link: self.file(link)))

        # categories & files are not real Wikilinks
        tests['links'] = tests['links'] - tests['cat'] - tests['files']

        """
        else:
            if self.opt.test:
                pywikibot.output(u'Title:%s' % self.current_page.title())
                pywikibot.output(u'Depth:%s' % self.current_page.depth)
            for l in self.current_page.linkedPages(namespaces=0):
                if self.opt.test:
                    pywikibot.output(u'Links to:[[%s]]' % l.title())
                tests['links'] += 1
                # pywikibot.output(u'Links:%s' % len(list(self.current_page.linkedPages(namespaces=0))))
            for t, p in textlib.extract_templates_and_params(text, remove_disabled_parts=True):
                if self.opt.test:
                    pywikibot.output('Template:[[%s]]' % t)
                tests['template'] += 1
                if 'infobox' in t:
                    tests['infobox'] += 1
                if 'dopracować' in t.lower():
                    tests['dopracować'] = True
                if t.lower() in tmplcat:  # check for category adding templates
                    tests['cat'] += 1
                    if self.opt.test:
                        pywikibot.output('Current cat#%i' % tests['cat'])
                    # cleanupTmpl = (t, p)
                # if 'rok w' in t or 'Rok w' in t:
                #     links['cat'] += 1

            for c in textlib.getCategoryLinks(text):
                if self.opt.test:
                    pywikibot.output('Category:%s' % c)
                tests['cat'] += 1
                if self.opt.test:
                    pywikibot.output('Current cat#%i' % tests['cat'])
            for r in refR.finditer(text):
                if self.opt.test:
                    pywikibot.output('Ref:%s' % r.group('all'))
                tests['refs'] += 1
            if self.opt.test:
                pywikibot.output('Links=%s' % tests)
                # pywikibot.output('Cleanup=%s' % re.sub('\n','',textlib.glue_template_and_params(cleanupTmpl)))

        if tests['dopracować']:
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
            if not (tests['links'] and tests['cat']):
                if not tests['links']:
                    p['linki'] = datestr
                    summary.append('linki')
                if not tests['cat']:
                    p['kategoria'] = datestr
                    summary.append('kategorie')
                if not tests['refs']:
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
        """
        pywikibot.output('#####################')
        pywikibot.output(f'treat_page results:{tests}')

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