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