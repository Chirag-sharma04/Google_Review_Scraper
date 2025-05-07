# Google Maps Review Scraper

A Python desktop application that allows you to search for businesses on Google Maps and scrape their reviews for analysis and data export.

## Features

- **Search Functionality**: Search for businesses by name or paste a direct Google Maps link
- **Business Selection**: Choose from multiple search results to find the exact business
- **Review Scraping**: Extract reviews, ratings, reviewer names, and dates
- **Export Options**: Export scraped data to CSV or Excel formats
- **Anti-Detection Measures**: Uses undetected-chromedriver to bypass Google's bot detection


## Requirements

- Python 3.7 or higher
- Chrome browser installed
- Required Python packages (automatically installed by the script):
  - selenium
  - undetected-chromedriver
  - pandas
  - matplotlib
  - numpy
  - tkinter (usually comes with Python)
  - Streamlit

## Installation

1. Clone or download this repository
2. Run the script directly - it will automatically install required dependencies

```bash
 streamlit run  google_maps_review_scraper.py
```

## Usage

1. **Launch the Application**: Run the script to open the GUI
2. **Search for a Business**:
   - Enter a business name or paste a Google Maps URL
   - Click "Search"
3. **Select a Business**:
   - Choose from the search results by clicking on a business in the list
4. **Configure Scraping**:
   - Enter the number of reviews you want to scrape
   - Click "Scrape Reviews"
5. **View Results**:
   - Navigate to the "Reviews" tab to see all scraped reviews
   - Check the "Analytics" tab for visual data analysis
6. **Export Data**:
   - Use the "Export to CSV" or "Export to Excel" buttons in the Analytics tab

## Troubleshooting

### Common Issues

- **"NoneType has no attribute 'get'"**: This typically occurs when the script cannot find certain elements on the page. This may happen if:
  - Google Maps has updated its HTML structure
  - The review section isn't loading properly
  - The browser isn't properly initialized
  
  Solution: Try refreshing the page or restarting the application.

- **Driver Initialization Failed**: Make sure Chrome is installed and updated to the latest version.

- **Scraping Stops Too Early**: Google Maps loads reviews dynamically as you scroll. If you're seeing fewer reviews than expected, it might be because:
  - The business doesn't have that many reviews
  - The page didn't scroll enough to load all reviews
  
  Solution: Try requesting a smaller number of reviews.

## Technical Details

- Uses Selenium and undetected-chromedriver for web automation
- Employs multiple fallback XPath strategies to handle variations in Google Maps' HTML structure
- Threading is implemented to keep the UI responsive during scraping operations
- Matplotlib is used for data visualization

## Legal Disclaimer

This tool is intended for personal use, research, and educational purposes only. Usage of this tool should comply with Google's Terms of Service. The developers are not responsible for any misuse of this tool or violations of Google's terms.

## License

This project is available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.