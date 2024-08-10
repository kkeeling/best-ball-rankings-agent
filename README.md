# Best Ball Rankings Agent

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Install Playwright browsers:
   ```
   playwright install
   ```

## Running the application

To run the application, use the following command:

```
python src/main.py
```

## Troubleshooting

If you encounter an error about missing Playwright executables, try the following steps:

1. Make sure you've run the `playwright install` command as described in the setup instructions.

2. If the error persists, try uninstalling and reinstalling Playwright:
   ```
   pip uninstall playwright
   pip install playwright==1.38.0
   playwright install
   ```

3. If you're still having issues, you can try to install the browsers manually:
   ```
   python -m playwright install chromium
   ```

4. Check if the Playwright cache directory exists and has the correct permissions:
   ```
   ls -l ~/Library/Caches/ms-playwright
   ```
   If it doesn't exist or you don't have the correct permissions, you can try creating it manually:
   ```
   mkdir -p ~/Library/Caches/ms-playwright
   chmod 755 ~/Library/Caches/ms-playwright
   ```

5. If none of the above steps work, please report the issue to the project maintainers with details about your operating system and Python version.
