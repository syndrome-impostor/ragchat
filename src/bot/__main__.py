import argparse
import sys
import asyncio

from . import scrape, ingest, query, chat

def main():
    parser = argparse.ArgumentParser(prog="bot")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add subparser for scrape
    subparsers.add_parser("scrape", help="Scrape data from external sources")
    
    # Add subparser for ingest
    subparsers.add_parser("ingest", help="Ingest data into storage")
    
    # Add subparser for query with its arguments
    query_parser = subparsers.add_parser("query", help="Query the stored data")
    query_group = query_parser.add_mutually_exclusive_group()
    query_group.add_argument('-l', '--list', action='store_true', help='List all documents')
    query_group.add_argument('query', nargs='?', help='Search query')
    query_parser.add_argument('-n', '--num-results', type=int, default=5, help='Number of results to show')
    query_parser.add_argument('-v', '--verbose', action='store_true', help='Show full result details')
    
    # Add subparser for chat with its arguments
    chat_parser = subparsers.add_parser("chat", help="Chat with the bot")
    chat_parser.add_argument('-v', '--verbose', action='store_true',
                           help='Show source references')
    chat_parser.add_argument('-vv', '--very-verbose', action='store_true',
                           help='Show source chunks and metadata')

    args = parser.parse_args()
    
    if args.command == "scrape":
        asyncio.run(scrape.run_scrape())
    elif args.command == "ingest":
        ingest.run_ingest()
    elif args.command == "query":
        query.run_query(args)
    elif args.command == "chat":
        chat.run_chat(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
