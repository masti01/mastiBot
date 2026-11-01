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
from mwparserfromhell.nodes import Wikilink, Template
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
        ekname = ("EK", "ek", "ekspresowe kasowanko", "usuń", "speedy", "delete")
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

    @staticmethod
    def link_interwiki(tmpl: Template) -> bool:
        # check if link is in {{link-interwiki}}
        return tmpl.name.lower().startswith("link-interwiki")
    
    def wikilinks(self, parsed) -> int:
        # count Wikilinks in parsed text
        if self.opt.test:
            pywikibot.output(f'PARSED:\n{parsed}')

        # wikilinks
        links = len(parsed.filter_wikilinks())
        
        # Categories
        cat = len(parsed.filter_wikilinks(matches=lambda link: self.category(link)))

        # Files
        files = len(parsed.filter_wikilinks(matches=lambda link: self.file(link)))
        
        # link-interwikis
        interwiki_links = len(parsed.filter_templates(matches=lambda tmpl: tmpl.name.lower().strip().startswith("link-interwiki")))

        # categories & files are not real Wikilinks
        return links - cat - files + interwiki_links

    @staticmethod
    def template_required(results) -> bool:
        # check if cleanup template is required
        for test in ('links', 'categories', 'refs'):
            if not results[test]:
                return True
        return False

    @staticmethod
    def common_element(a, b):
        # check if 2 lists have at least one common elemnet
        return [e for e in a if e in b]

    def build_template(self, results, tmpl: Template) -> None:
        # year-month for paarams
        datestr = datetime.now().strftime('%Y-%m')
        params = []
        for p in tmpl.params:
            params.append(p.name)
        if self.opt.test:
            pywikibot.output(f'>>> PARAMSL{params}')

        if not results['links']:
            results['summary'].append('linki')
            if not self.common_element(params, ('linki', 'linki wewnętrzne')):
                tmpl.add('linki',datestr)
        if not results['categories']:
            results['summary'].append('kategorie')
            if not self.common_element(params, ('kategoria', 'kategorie')):
                tmpl.add('kategorie',datestr)
        if not results['refs']:
            results['summary'].append('źródła')
            if not self.common_element(params, ('źródła', 'Źródła', 'WER', 'wer', 'brak źródeł', 'dodać źródła')):
                tmpl.add('źródła', datestr)


    def treat_page(self) -> None:

        if self.opt.test:
            pywikibot.output(f'Title:[[{self.current_page.title()}]]')

        # parse page for checks
        parsed = parse(self.current_page.text)

        article_requirements = {
                'links': 0,
                'categories': 0,
                'files': 0,
                'templates': 0,
                'infoboxes': 0,
                'refs': 0,
                'cleanuptmpl': None,
                'summary': list()
        }

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
        article_requirements['links'] = self.wikilinks(parsed)

        # Templates
        if self.opt.test:
            for t in parsed.filter_templates():
                pywikibot.output(f'Template:[[{t.replace('\n', '')}]]')
        article_requirements['templates'] = len(parsed.filter_templates())

        # infobox
        article_requirements['infoboxes'] = len(
            parsed.filter_templates(matches=lambda tmpl: tmpl.name.lower().strip().endswith("infobox")))

        # dopracowć
        try:
            article_requirements['cleanuptmpl'] = parsed.filter_templates(matches=lambda tmpl: tmpl.name.lower().strip().startswith("dopracować"))[0]
        except IndexError:
            pass

        # Categories
        article_requirements['categories'] = len(parsed.filter_wikilinks(matches=lambda link: self.category(link)))

        # References
        article_requirements['refs'] = len(parsed.filter_tags(matches=lambda tag: (tag.tag.lower() == "ref" and not tag.endswith('/>'))))
        if self.opt.test:
            pywikibot.output(f'Refs:{parsed.filter_tags(matches=lambda tag: (tag.tag.lower() == "ref" and not tag.endswith('/>')))}')

        # check if clenup template is required
        if self.template_required(article_requirements):
            pywikibot.output('#####################')
            pywikibot.output(f'treat_page results:{article_requirements}')
            pywikibot.output('#####################')

            # create template to insert
            if article_requirements['cleanuptmpl']:
                cleanup_tmpl = article_requirements['cleanuptmpl']
            else:
                cleanup_tmpl = Template("Dopracować")
                parsed.insert(0, cleanup_tmpl)
                parsed.insert(1, '\n')

            self.build_template(article_requirements, cleanup_tmpl)

            if self.opt.test:
                pywikibot.output(f'CleanupTmpl: {cleanup_tmpl}')
                pywikibot.output(f'nodes: {parsed.nodes}')

            if self.opt.test:
                pywikibot.output(f'*****************\n{parsed}\n*****************')

            self.put_current(str(parsed), summary=f'Sprawdzanie nowych stron: w artykule należy dopracować: {', '.join(article_requirements['summary'])}')


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