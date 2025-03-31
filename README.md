# Stock Analyzer

A web application that analyzes S&P 500 stocks using the 200-week moving average strategy. The application helps identify interesting stocks based on their deviation from the 200-week moving average.

![Demo GIF](demo.gif)

## Features

- Real-time S&P 500 stock data fetching
- 200-week moving average calculation
- Interactive visualizations:
  - Bubble chart showing all stocks' deviations
  - Separate charts for overbought and oversold stocks
- Customizable thresholds for overbought/oversold classification
- Data caching to minimize API calls
- Secure login system

## Prerequisites

- Python 3.12 or higher
- Google Cloud Platform account (for deployment)
- Access code (contact administrator)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-analyzer.git
cd stock-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies using `uv`:
```bash
pip install uv
uv sync
```

4. Create a `.env` file in the root directory with the following variables:
```env
GCP_PROJECT_ID=your-project-id
GCP_PROJECT_NUMBER=your-project-number
SERVICE_REGION=your-region
CLOUD_RUN_SERVICE_ACCOUNT=your-service-account
SERVICE_TIMEOUT=3600
SERVICE_MEMORY=1Gi
```

## Usage

### Local Development

Run the application locally:
```bash
uv run streamlit run src/app.py
```

The application will be available at `http://localhost:8501`

### Deployment

Deploy to Google Cloud Run:
```bash
./taskfile.sh deploy
```

## Project Structure

```
stock-analyzer/
├── src/
│   ├── app.py              # Main Streamlit application
│   ├── main.py             # Core data fetching logic
│   ├── utils.py            # Utility functions
│   └── cloud_storage.py    # Google Cloud Storage operations
├── cache/                  # Local cache directory
├── .env                    # Environment variables
├── pyproject.toml         # Project dependencies
├── taskfile.sh           # Task automation script
└── Dockerfile.app        # Docker configuration
```

## Data Sources

- S&P 500 stock data: Yahoo Finance API
- Company information: Wikipedia S&P 500 page

## Caching Strategy

The application implements a caching system to minimize API calls:
- Stock data is cached for 24 hours
- S&P 500 company information is cached for 24 hours
- Cache files are stored in the `cache/` directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

> For inquiries, contact me via [email](mailto:juliushaas91@gmail.com) or [LinkedIn](https://www.linkedin.com/in/jh91/)
