# Security

Belfort runs on your own machine and binds to `127.0.0.1`. It stores practice records in `data/belfort.db` and your AI key only in your browser (or in your own `.env`). It sends your key only to the AI provider you choose.

If you find a security problem, such as a way for a web page to read your key, a path traversal or code execution, tell the other founder directly rather than in an issue, and fix it before anything else.

Please do not expose Belfort to the internet. It has no user accounts, and `ACCESS_CODES` is a simple gate for private networks only.
