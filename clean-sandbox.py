"""
This is a bot to reset sandboxes

Call hourly:
    python3 pwb.py masti/clean-sandbox.py -page:"Wikipedia:Brudnopis" -text:"{{Prosimy - NIE ZMIENIAJ, NIE KASUJ, NIE PRZENOŚ tej linijki - pisz niżej}}" -summary:"resetowanie brudnopisu" -always

Call daily:
    python3 pwb.py masti/clean-sandbox.py -page:"Pomoc:Krok pierwszy - edytowanie" -text:"{{/podstrona}}" -summary:"resetowanie brudnopisu" -always
    python3 pwb.py masti/clean-sandbox.py -page:"Pomoc:Krok drugi - formatowanie" -text:"{{/podstrona}}" -summary:"resetowanie brudnopisu" -always
    python3 pwb.py masti/clean-sandbox.py -page:"Pomoc:Krok trzeci - linki" -text:"{{/podstrona}}" -summary:"resetowanie brudnopisu" -always
    python3 pwb.py masti/clean-sandbox.py -page:"Pomoc:Krok czwarty - grafiki" -text:"{{/podstrona}}" -summary:"resetowanie brudnopisu" -always
    python3 pwb.py masti/clean-sandbox.py -page:"Pomoc:Krok piąty - szablony" -text:"{{/podstrona}}" -summary:"resetowanie brudnopisu" -always

Use global -simulate option for test purposes. No changes to live wiki
will be done.

&params;
"""
#
# (C) masti, 2006-2026
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import CurrentPageBot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

class MyBot(CurrentPageBot):

    summary_key = 'basic-changing'
    use_redirects = False

    update_options = {
        'text': None,  # final text
        'summary': None,  # bot summary
        'always': False
    }

    def treat_page(self):
        if self.opt.text:
            self.put_current(self.opt.text, summary=self.opt.summary)


def main(*args: str) -> None:
    """Parse command line arguments and invoke bot."""
    options = {}
    gen_factory = pagegenerators.GeneratorFactory()
    # Option parsing
    local_args = pywikibot.handle_args(args)  # global options
    local_args = gen_factory.handle_args(local_args)  # generators options
    for arg in local_args:
        opt, sep, value = arg.partition(':')
        if opt in ('-summary', '-text'):
            if not value:
                pywikibot.input('Please enter a value for ' + opt)
            options[opt[1:]] = value
        elif opt == '-always':
            options['always'] = True
    pywikibot.output(f'local_args:{local_args}')
    MyBot(generator=gen_factory.getCombinedGenerator(), **options).run()

if __name__ == '__main__':
    main()