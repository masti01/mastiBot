import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

class MyBot(ExistingPageBot):

    summary_key = 'basic-changing'
    use_redirects = False

    update_options = {
        'text': 'This is a test text',
        'summary': 'Bot: a bot test edit with Pywikibot.'
    }

    def treat_page(self):
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text
        text += '\n' + self.opt.text
        self.put_current(text, summary=self.opt.summary)

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
            options[opt[1:]] = value
    MyBot(generator=gen_factory.getCombinedGenerator(), **options).run()

if __name__ == '__main__':
    main()