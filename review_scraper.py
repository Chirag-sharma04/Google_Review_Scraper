import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import re
import streamlit as st
import pandas as pd
import random

class GoogleMapsReviewScraper:
    def __init__(self):
        self.driver = None
        
    def initialize_browser(self):
        """Initialize the undetected Chrome browser with improved settings"""
        options = uc.ChromeOptions()
        
        # Comment out headless mode as it can sometimes be detected
        # options.add_argument('--headless')
        
        # Add additional options to make the browser more human-like
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--window-size={random.randint(1050, 1200)},{random.randint(800, 900)}')
        options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(0, 150)} Safari/537.36')
        
        # Initialize the driver with a longer page load timeout
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        
    def close_browser(self):
        """Close the browser safely"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            
    def extract_place_id(self, url):
        """Extract place ID from Google Maps URL"""
        # Try to extract from shortened URL
        pattern = r'g\.co/kgs/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
        # Try to extract from regular URL
        pattern = r'maps/place/[^/]+/([^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
        return None
    
    def search_place(self, place_name):
        """Search for a place and return suggestions with improved error handling"""
        try:
            self.driver.get("https://www.google.com/maps")
            
            # Wait for the page to fully load
            time.sleep(3)
            
            # Accept cookies if the dialog appears
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass  # No cookie dialog or couldn't find it
            
            # Multiple possible XPaths for the search box
            search_box_xpaths = [
                "//input[@id='searchboxinput']",
                "//input[contains(@aria-label, 'Search')]",
                "//input[contains(@placeholder, 'Search')]",
                "//input[@name='q']"
            ]
            
            search_box = None
            for xpath in search_box_xpaths:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if search_box:
                        break
                except:
                    continue
            
            if not search_box:
                st.error("Could not find the search box. Please try again.")
                return []
            
            # Clear and enter the place name with human-like typing
            search_box.clear()
            for char in place_name:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
            
            # Wait for suggestions to appear
            time.sleep(3)
            
            # Try multiple XPaths for suggestions
            suggestion_xpaths = [
                "//div[@role='option']",
                "//div[contains(@class, 'suggestions-')]//div[@role='option']",
                "//div[contains(@class, 'suggest')]//div[@role='listitem']",
                "//div[contains(@class, 'suggest')]//li",
                "//div[contains(@class, 'search-result')]"
            ]
            
            suggestions = []
            for xpath in suggestion_xpaths:
                try:
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, xpath))
                    )
                    if elements and len(elements) > 0:
                        suggestions = elements
                        break
                except:
                    continue
            
            if not suggestions:
                # If no suggestions found, try pressing Enter and then scraping the first result
                search_box.send_keys(Keys.ENTER)
                time.sleep(5)
                st.info("No suggestions found. Proceeding with direct search.")
                return [{
                    'id': 0,
                    'text': place_name,
                    'direct_search': True
                }]
            
            # Extract suggestion text and data
            suggestion_data = []
            for i, suggestion in enumerate(suggestions[:5]):  # Limit to 5 suggestions
                try:
                    text = suggestion.text.strip()
                    if text:
                        suggestion_data.append({
                            'id': i,
                            'text': text,
                            'element': suggestion,
                            'direct_search': False
                        })
                except StaleElementReferenceException:
                    # If element is stale, try to find it again
                    continue
                except Exception as e:
                    st.warning(f"Error processing suggestion: {str(e)}")
                    continue
            
            return suggestion_data
            
        except Exception as e:
            st.error(f"Error during place search: {str(e)}")
            return []
    
    def select_suggestion(self, suggestion):
        """Select a suggestion from the dropdown with improved error handling"""
        try:
            # Handle direct search case
            if suggestion.get('direct_search', False):
                # We already pressed Enter in the search_place method
                pass
            else:
                # Click on the suggestion element
                try:
                    suggestion['element'].click()
                except:
                    # If clicking fails, try JavaScript click
                    self.driver.execute_script("arguments[0].click();", suggestion['element'])
            
            # Wait for the page to load
            time.sleep(5)
            
            # Click on reviews tab - try multiple possible XPaths
            review_tab_xpaths = [
                "//button[contains(@aria-label, 'Reviews')]",
                "//div[contains(text(), 'Reviews')]",
                "//a[contains(text(), 'reviews')]",
                "//button[contains(text(), 'Reviews')]",
                "//span[contains(text(), 'Reviews')]/parent::*"
            ]
            
            clicked = False
            for xpath in review_tab_xpaths:
                try:
                    reviews_tab = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    reviews_tab.click()
                    clicked = True
                    break
                except:
                    continue
            
            if not clicked:
                st.warning("Could not find reviews tab. Attempting to scrape reviews from current page.")
            
            # Additional wait for reviews to load
            time.sleep(3)
            
        except Exception as e:
            st.error(f"Error selecting suggestion: {str(e)}")
    
    def go_to_url(self, url):
        """Navigate directly to a Google Maps URL with improved error handling"""
        try:
            self.driver.get(url)
            
            # Wait for the page to load
            time.sleep(5)
            
            # Accept cookies if the dialog appears
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass  # No cookie dialog or couldn't find it
            
            # Click on reviews tab - try multiple possible XPaths
            review_tab_xpaths = [
                "//button[contains(@aria-label, 'Reviews')]",
                "//div[contains(text(), 'Reviews')]",
                "//a[contains(text(), 'reviews')]",
                "//button[contains(text(), 'Reviews')]",
                "//span[contains(text(), 'Reviews')]/parent::*"
            ]
            
            clicked = False
            for xpath in review_tab_xpaths:
                try:
                    reviews_tab = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    reviews_tab.click()
                    clicked = True
                    break
                except:
                    continue
            
            if not clicked:
                st.warning("Could not find reviews tab. Attempting to scrape reviews from current page.")
            
            # Additional wait for reviews to load
            time.sleep(3)
            
        except Exception as e:
            st.error(f"Error navigating to URL: {str(e)}")
    
    def scrape_reviews(self, min_reviews=10):
        """Scrape reviews from the current page with improved selectors and error handling"""
        reviews = []
        
        # Scroll to load more reviews until we have at least min_reviews
        scroll_attempts = 0
        max_scroll_attempts = 15  # Increased max attempts
        
        # Multiple possible XPaths for review containers
        review_container_xpaths = [
            "//div[@data-review-id]",
            "//div[contains(@class, 'review-')]",
            "//div[contains(@class, 'section-review')]",
            "//div[contains(@class, 'jftiEf')]",  # A common Google Maps review container class
            "//div[contains(@class, 'fontBodyMedium')]//div[contains(@class, 'fontBodyMedium')]"  # Nested structure often used for reviews
        ]
        
        # Try each XPath until we find reviews
        review_container_xpath = None
        for xpath in review_container_xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements and len(elements) > 0:
                    review_container_xpath = xpath
                    break
            except:
                continue
        
        if not review_container_xpath:
            st.error("Could not find review containers. The page structure might have changed.")
            return []
        
        while len(reviews) < min_reviews and scroll_attempts < max_scroll_attempts:
            # Get current reviews
            try:
                review_elements = self.driver.find_elements(By.XPATH, review_container_xpath)
            except:
                st.warning("Error finding review elements. Trying alternative approach.")
                # Try an alternative approach - look for elements with rating information
                try:
                    review_elements = self.driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'stars')]/ancestor::div[3]")
                except:
                    st.error("Could not find reviews with alternative approach.")
                    break
            
            # If we found new reviews, process them
            new_reviews_found = False
            for element in review_elements:
                try:
                    # Try to get a unique identifier for the review
                    review_id = None
                    try:
                        review_id = element.get_attribute('data-review-id')
                    except:
                        # If no data-review-id, create a hash from the content
                        review_id = hash(element.text)
                    
                    # Skip if we already processed this review
                    if any(r.get('id') == review_id for r in reviews):
                        continue
                    
                    new_reviews_found = True
                    
                    # Extract reviewer name - try multiple XPaths
                    reviewer_name = "Anonymous"
                    name_xpaths = [
                        ".//div[contains(@class, 'fontHeadlineSmall')]",
                        ".//div[contains(@class, 'section-review-title')]",
                        ".//div[contains(@class, 'd4r55')]",  # Another common class for reviewer names
                        ".//div[contains(@class, 'fontBodyMedium')][1]"  # Often the first medium text is the name
                    ]
                    
                    for xpath in name_xpaths:
                        try:
                            name_element = element.find_element(By.XPATH, xpath)
                            if name_element and name_element.text.strip():
                                reviewer_name = name_element.text.strip()
                                break
                        except:
                            continue
                    
                    # Extract rating - try multiple approaches
                    rating = "N/A"
                    rating_xpaths = [
                        ".//span[contains(@aria-label, 'stars')]",
                        ".//span[contains(@aria-label, 'Rated')]",
                        ".//div[contains(@class, 'rating')]"
                    ]
                    
                    for xpath in rating_xpaths:
                        try:
                            rating_element = element.find_element(By.XPATH, xpath)
                            aria_label = rating_element.get_attribute('aria-label')
                            if aria_label:
                                # Extract the first number from the aria-label
                                rating_match = re.search(r'(\d+(\.\d+)?)', aria_label)
                                if rating_match:
                                    rating = rating_match.group(1)
                                    break
                        except:
                            continue
                    
                    # Extract review text - try multiple XPaths
                    review_text = "No review text"
                    text_xpaths = [
                        ".//span[contains(@class, 'fontBodyMedium')]",
                        ".//div[contains(@class, 'review-full-text')]",
                        ".//div[contains(@class, 'section-review-text')]",
                        ".//div[contains(@class, 'review-content')]",
                        ".//div[contains(@class, 'fontBodyMedium')][2]"  # Often the second medium text is the review
                    ]
                    
                    for xpath in text_xpaths:
                        try:
                            text_element = element.find_element(By.XPATH, xpath)
                            if text_element and text_element.text.strip():
                                review_text = text_element.text.strip()
                                break
                        except:
                            continue
                    
                    # Extract date - try multiple XPaths
                    date = "Unknown date"
                    date_xpaths = [
                        ".//span[contains(@class, 'fontBodySmall')]",
                        ".//span[contains(@class, 'section-review-publish-date')]",
                        ".//span[contains(@class, 'section-review-date')]",
                        ".//div[contains(@class, 'fontBodyMedium')][3]"  # Often the third medium text is the date
                    ]
                    
                    for xpath in date_xpaths:
                        try:
                            date_element = element.find_element(By.XPATH, xpath)
                            if date_element and date_element.text.strip():
                                date = date_element.text.strip()
                                break
                        except:
                            continue
                    
                    reviews.append({
                        'id': review_id,
                        'reviewer': reviewer_name,
                        'rating': rating,
                        'text': review_text,
                        'date': date
                    })
                    
                    # Break if we have enough reviews
                    if len(reviews) >= min_reviews:
                        break
                        
                except Exception as e:
                    st.warning(f"Error extracting review: {str(e)}")
                    continue
            
            # If we didn't find any new reviews in this iteration, we might be at the end
            if not new_reviews_found and len(reviews) > 0:
                scroll_attempts += 2  # Increment more to exit sooner
            
            # Scroll down to load more reviews - try different scroll methods
            try:
                # Method 1: Scroll to the last review element
                if review_elements:
                    self.driver.execute_script("arguments[0].scrollIntoView();", review_elements[-1])
                
                # Method 2: Scroll down by a fixed amount
                self.driver.execute_script("window.scrollBy(0, 500);")
                
                # Add random human-like delay
                time.sleep(random.uniform(1.5, 3.0))
                
                # Method 3: Try to click "More reviews" button if it exists
                try:
                    more_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'More') or contains(text(), 'more') or contains(@aria-label, 'More reviews')]")
                    more_button.click()
                    time.sleep(2)
                except:
                    pass
                
            except Exception as e:
                st.warning(f"Error scrolling: {str(e)}")
            
            scroll_attempts += 1
        
        # If we couldn't find enough reviews, return what we have
        if len(reviews) < min_reviews:
            st.warning(f"Could only find {len(reviews)} reviews, which is less than the requested {min_reviews}.")
        
        return reviews[:min_reviews] if len(reviews) >= min_reviews else reviews

# Streamlit UI
st.title("Google Maps Review Scraper")
st.markdown("Scrape reviews from any Google Maps business listing")

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []
if 'reviews' not in st.session_state:
    st.session_state.reviews = []
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# Display any error from previous run
if st.session_state.error_message:
    st.error(st.session_state.error_message)
    st.session_state.error_message = None

# Input method selection
input_method = st.radio("Select input method:", ["URL", "Place Name"])

if input_method == "URL":
    url = st.text_input("Enter Google Maps URL")
    
    if st.button("Scrape Reviews from URL"):
        try:
            with st.spinner("Initializing browser..."):
                # Close previous browser instance if exists
                if st.session_state.scraper:
                    st.session_state.scraper.close_browser()
                
                # Initialize new scraper
                st.session_state.scraper = GoogleMapsReviewScraper()
                st.session_state.scraper.initialize_browser()
            
            with st.spinner("Scraping reviews..."):
                st.session_state.scraper.go_to_url(url)
                st.session_state.reviews = st.session_state.scraper.scrape_reviews(min_reviews=10)
                
                if not st.session_state.reviews:
                    st.error("No reviews found. The business might not have any reviews or the scraper couldn't access them.")
                
                # Close browser after scraping
                st.session_state.scraper.close_browser()
        except Exception as e:
            st.session_state.error_message = f"Error: {str(e)}"
            # Ensure browser is closed on error
            if st.session_state.scraper:
                st.session_state.scraper.close_browser()
            st.experimental_rerun()

else:  # Place Name
    place_name = st.text_input("Enter place name:")
    
    if st.button("Search Place"):
        try:
            with st.spinner("Initializing browser..."):
                # Close previous browser instance if exists
                if st.session_state.scraper:
                    st.session_state.scraper.close_browser()
                
                # Initialize new scraper
                st.session_state.scraper = GoogleMapsReviewScraper()
                st.session_state.scraper.initialize_browser()
            
            with st.spinner("Searching for place..."):
                st.session_state.suggestions = st.session_state.scraper.search_place(place_name)
                
                if not st.session_state.suggestions:
                    st.error("No places found. Please try a different search term.")
                    st.session_state.scraper.close_browser()
        except Exception as e:
            st.session_state.error_message = f"Error during search: {str(e)}"
            # Ensure browser is closed on error
            if st.session_state.scraper:
                st.session_state.scraper.close_browser()
            st.experimental_rerun()
    
    # Display suggestions
    if st.session_state.suggestions:
        st.subheader("Select a place:")
        
        # Handle direct search case
        direct_search_suggestion = next((s for s in st.session_state.suggestions if s.get('direct_search', False)), None)
        
        if direct_search_suggestion:
            st.info(f"Proceeding with direct search for '{direct_search_suggestion['text']}'")
            try:
                with st.spinner("Scraping reviews..."):
                    st.session_state.scraper.select_suggestion(direct_search_suggestion)
                    st.session_state.reviews = st.session_state.scraper.scrape_reviews(min_reviews=10)
                    st.session_state.scraper.close_browser()
            except Exception as e:
                st.session_state.error_message = f"Error scraping reviews: {str(e)}"
                if st.session_state.scraper:
                    st.session_state.scraper.close_browser()
                st.experimental_rerun()
        else:
            # Display regular suggestions
            for suggestion in st.session_state.suggestions:
                if st.button(f"{suggestion['text']}", key=f"suggestion_{suggestion['id']}"):
                    try:
                        with st.spinner("Scraping reviews..."):
                            st.session_state.scraper.select_suggestion(suggestion)
                            st.session_state.reviews = st.session_state.scraper.scrape_reviews(min_reviews=10)
                            st.session_state.scraper.close_browser()
                    except Exception as e:
                        st.session_state.error_message = f"Error scraping reviews: {str(e)}"
                        if st.session_state.scraper:
                            st.session_state.scraper.close_browser()
                        st.experimental_rerun()

# Display reviews
if st.session_state.reviews:
    st.subheader(f"Found {len(st.session_state.reviews)} Reviews")
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(st.session_state.reviews)
    
    # Display as cards
    for i, review in enumerate(st.session_state.reviews):
        with st.expander(f"Review {i+1} - {review['reviewer']} ({review['rating']} stars)"):
            st.write(f"**Date:** {review['date']}")
            st.write(f"**Review:** {review['text']}")
    
    # Also display as a table for easy export
    st.subheader("Reviews Table")
    st.dataframe(df[['reviewer', 'rating', 'date', 'text']])
    
    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Reviews as CSV",
        data=csv,
        file_name="google_maps_reviews.csv",
        mime="text/csv"
    )

# Cleanup on session end
if st.button("Close Browser"):
    if st.session_state.scraper:
        st.session_state.scraper.close_browser()
        st.session_state.scraper = None
        st.success("Browser closed successfully")