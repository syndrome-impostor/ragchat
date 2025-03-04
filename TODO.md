# Desired functionality and known issues
- [ ] Choose between web and CLI chat interface
- [ ] Implement PDF processing
- [ ] Duplicate URLs currently throw ChromaDB errors
- [ ] Allow other LLM providers
- [ ] Investigate Instructor-xl replacements, maybe some of the x5 models?
- [ ] Add verbosity control to CLI (-v flags)
    - [ ] Reduce default verbosity of ingest
- [ ] Fix the verbosity of the chat session
- [ ] Actually make a decent system prompt
- [ ] Fiddle with chunking, token limits, etc to improve performance
- [ ] WebDriverManager is storing drivers in ~/.wdm, tainting the local system. 
    - [ ] This caused a dependency issue when the wrong version of ChromeDriver was installed, and the cache had to be manually deleted.
    - [ ] Migrating to a custom path for the cache proved difficult. WDM_LOCAL stores the cache in ./src/bot/.wdm
- [ ] Multi-line pasting in CLI chat
- [ ] Implement a config.yaml to override config defaults?
- [ ] Figure out why it's slow to start up (~2s)