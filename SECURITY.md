# Security

Belfort runs on your own machine and binds to `127.0.0.1`. It stores practice records in a local SQLite file and your AI key only in your browser (or in your own `.env`), and sends that key only to the AI provider you choose.

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private vulnerability reporting ("Report a vulnerability" on the Security tab of this repository). We aim to reply within a week and to fix confirmed issues before anything else.

Examples worth reporting: a way for a web page to read your key or call the local API, path traversal, code execution, or secrets in the repository.

Please do not expose Belfort to the internet. It has no user accounts, and `ACCESS_CODES` is a simple gate for private networks only.
