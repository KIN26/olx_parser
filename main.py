from parser import OlxParser
from handler import Handler


if __name__ == '__main__':
    with OlxParser() as parser:
        parser.loop.run_until_complete(parser.run())
    handler = Handler(parser.data)
    handler.run()
    handler.display()
