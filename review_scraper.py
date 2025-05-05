import time
import re
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime

class GoogleMapsReviewScraper:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Maps Review Scraper")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize variables
        self.driver = None
        self.reviews = []
        self.search_results = []
        self.place_link = None
        
        # Create main frames
        self.setup_ui()
        
    def setup_ui(self):
        # Top frame for search and input
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Search input
        ttk.Label(top_frame, text="Enter place name or Google Maps link:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=60)
        self.search_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Search button
        self.search_button = ttk.Button(top_frame, text="Search", command=self.search_place)
        self.search_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Number of reviews to scrape
        ttk.Label(top_frame, text="Number of reviews to scrape:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.num_reviews_var = tk.StringVar(value="10")
        self.num_reviews_entry = ttk.Entry(top_frame, textvariable=self.num_reviews_var, width=5)
        self.num_reviews_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Scrape button
        self.scrape_button = ttk.Button(top_frame, text="Scrape Reviews", command=self.start_scraping, state=tk.DISABLED)
        self.scrape_button.grid(row=1, column=2, padx=5, pady=5)
        
        # Create a notebook for different views
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Search results frame
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search Results")
        
        # Search results listbox
        self.results_frame = ttk.Frame(self.search_frame)
        self.results_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        self.results_listbox = tk.Listbox(self.results_frame, height=10)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)
        self.results_listbox.bind('<<ListboxSelect>>', self.on_result_select)
        
        # Reviews frame
        self.reviews_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reviews_frame, text="Reviews")
        
        # Reviews table
        self.reviews_tree = ttk.Treeview(self.reviews_frame, columns=("Name", "Rating", "Date", "Review"), show="headings")
        self.reviews_tree.heading("Name", text="Name")
        self.reviews_tree.heading("Rating", text="Rating")
        self.reviews_tree.heading("Date", text="Date")
        self.reviews_tree.heading("Review", text="Review")
        
        self.reviews_tree.column("Name", width=150)
        self.reviews_tree.column("Rating", width=50)
        self.reviews_tree.column("Date", width=100)
        self.reviews_tree.column("Review", width=500)
        
        self.reviews_tree.pack(expand=True, fill=tk.BOTH)
        
        # Add scrollbar to reviews table
        reviews_scrollbar = ttk.Scrollbar(self.reviews_tree, orient=tk.VERTICAL, command=self.reviews_tree.yview)
        self.reviews_tree.configure(yscrollcommand=reviews_scrollbar.set)
        reviews_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Analytics frame
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
        
    def search_place(self):
        query = self.search_var.get().strip()
        
        if not query:
            messagebox.showerror("Error", "Please enter a place name or Google Maps link")
            return
            
        self.status_var.set("Searching for place...")
        
        # Clear previous results
        self.results_listbox.delete(0, tk.END)
        self.search_results = []
        
        # Start search in a separate thread
        threading.Thread(target=self._search_process, args=(query,), daemon=True).start()
        
    def _search_process(self, query):
        try:
            # Check if it's a direct Google Maps link
            if "maps.google" in query or "g.co" in query:
                self.place_link = query
                self.root.after(0, lambda: self.status_var.set("Place selected"))
                self.root.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))
                return
                
            # Initialize Chrome driver if not already done
            if not self.driver:
                self._initialize_driver()
                
            # Search for the place
            self.driver.get("https://www.google.com/maps")
            
            # Accept cookies if prompted (common in EU)
            try:
                accept_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Accept')]"))
                )
                accept_button.click()
                time.sleep(1)
            except:
                pass  # No cookie dialog or different text
            
            # Wait for search box and enter query using XPath
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='searchboxinput' or @name='q' or contains(@aria-label, 'search')]"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            
            # Wait for results to load
            time.sleep(3)
            
            # Get search results using XPath
            results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@role, 'article') or contains(@jsaction, 'mouseover:pane.listItem')]"))
            )
            
            # Store results and update UI
            for i, result in enumerate(results[:10]):  # Limit to 10 results
                try:
                    # Extract name using XPath
                    try:
                        name_xpath = ".//h3 | .//span[not(contains(@jsaction, 'mouseover'))] | .//div[contains(@class, 'fontHead')]"
                        name = result.find_element(By.XPATH, name_xpath).text
                    except NoSuchElementException:
                        # Fallback XPath for name
                        name = result.find_element(By.XPATH, ".//*[self::h1 or self::h2 or self::h3 or self::h4 or self::span][string-length(text()) > 2][1]").text
                    
                    # Extract rating and address using XPath
                    try:
                        info_element = result.find_element(By.XPATH, ".//div[contains(., 'stars') or contains(., '★')]")
                        info = info_element.text.split("·")
                    except NoSuchElementException:
                        info = ["No rating", "No address"]
                    
                    rating = info[0].strip() if len(info) > 0 else "No rating"
                    address = info[-1].strip() if len(info) > 1 else "No address"
                    
                    # Get the URL using XPath
                    link = result.find_element(By.XPATH, ".//a[contains(@href, 'maps')]").get_attribute("href")
                    
                    # Store result data
                    self.search_results.append({
                        "name": name,
                        "rating": rating,
                        "address": address,
                        "link": link
                    })
                    
                    # Update UI
                    self.root.after(0, lambda i=i, name=name, rating=rating, address=address: 
                        self.results_listbox.insert(tk.END, f"{i+1}. {name} - {rating} - {address}")
                    )
                except Exception as e:
                    print(f"Error processing result: {e}")
            
            self.root.after(0, lambda: self.status_var.set(f"Found {len(self.search_results)} results"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error searching: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to search: {str(e)}"))
        
    def on_result_select(self, event):
        try:
            selection = self.results_listbox.curselection()
            if selection:
                index = selection[0]
                self.place_link = self.search_results[index]["link"]
                self.scrape_button.config(state=tk.NORMAL)
                self.status_var.set(f"Selected: {self.search_results[index]['name']}")
        except Exception as e:
            self.status_var.set(f"Error selecting place: {str(e)}")
    
    def start_scraping(self):
        if not self.place_link:
            messagebox.showerror("Error", "Please select a place first")
            return
            
        try:
            num_reviews = int(self.num_reviews_var.get())
            if num_reviews < 1:
                raise ValueError("Number of reviews must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid number of reviews: {str(e)}")
            return
            
        # Clear previous results
        for i in self.reviews_tree.get_children():
            self.reviews_tree.delete(i)
        
        self.reviews = []
        
        # Disable UI elements during scraping
        self.search_button.config(state=tk.DISABLED)
        self.scrape_button.config(state=tk.DISABLED)
        
        # Start scraping in a separate thread
        threading.Thread(target=self._scrape_process, args=(num_reviews,), daemon=True).start()
        
        # Switch to the reviews tab
        self.notebook.select(1)
        
    def _scrape_process(self, num_reviews):
        try:
            self.root.after(0, lambda: self.status_var.set("Initializing scraper..."))
            
            # Initialize Chrome driver if not already done
            if not self.driver:
                self._initialize_driver()
                
            # Navigate to the place page
            if not self.driver.get(self.place_link):
                raise ValueError("Place link is not available")
            
            #Navigate to place page
             self.root.after(0, lambda: self.status_var.set(f"Navigating to {self.place_link}"))
             self.driver.get(self.place_link)
            
            # Wait for page to load and find reviews section
            time.sleep(5)
            
            # Click on reviews tab using XPath
            reviews_found = False
            review_tab_xpaths = [
                # By text containing "reviews"
                "//button[contains(., 'review') or contains(., 'Review')]",
                # By aria-label containing "reviews"
                "//button[contains(@aria-label, 'review')]",
                # By class and structure
                "//div[contains(., 'stars')]//button",
                # By rating pattern (common in reviews section)
                "//span[contains(., '★') or contains(., 'stars')]",
                # Reviews count 
                "//span[contains(text(), '(') and contains(text(), ')')]",
                # Rating section
                "//div[contains(@aria-label, 'rating')]"
            ]
            
            for xpath in review_tab_xpaths:
                try:
                    reviews_tab = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    reviews_tab.click()
                    time.sleep(2)
                    reviews_found = True
                    break
                except:
                    continue
                    
            if not reviews_found:
                # If we can't find the reviews tab, try to continue anyway
                self.root.after(0, lambda: self.status_var.set("Couldn't find reviews tab directly, trying to locate reviews..."))
            
            # Scroll to load more reviews
            self.root.after(0, lambda: self.status_var.set(f"Scrolling to load {num_reviews} reviews..."))
            
            # Find reviews container using XPath
            try:
                reviews_section = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='feed' or contains(@jsaction, 'mouseover:pane.review')]"))
                )
            except TimeoutException:
                # Fallback XPath methods
                try:
                    reviews_section = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[.//div[contains(., 'stars')]]"))
                    )
                except TimeoutException:
                    # Last resort - try to find the body of the page and scroll there
                    reviews_section = self.driver.find_element(By.XPATH, "//body")
            
            # Scroll until we have enough reviews or can't load more
            prev_review_count = 0
            max_scroll_attempts = 50  # Limit scrolling to prevent infinite loops
            
            for scroll_attempt in range(max_scroll_attempts):
                # Scroll down in the reviews section
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviews_section)
                time.sleep(1)
                
                # Find review elements using XPath
                review_elements = self.driver.find_elements(
                    By.XPATH,
                    "//div[.//span[contains(@aria-label, 'star') or contains(@aria-label, 'Star')]]"
                )
                
                # If the above fails, try alternative XPaths
                if not review_elements:
                    review_elements = self.driver.find_elements(
                        By.XPATH,
                        "//div[.//div[contains(., '★') or contains(., 'stars')]]"
                    )
                
                # If still no results, try a more general approach
                if not review_elements:
                    review_elements = self.driver.find_elements(
                        By.XPATH,
                        "//div[.//span[@role='img'] and (.//button or .//time)]"
                    )
                    
                current_review_count = len(review_elements)
                
                # Update status
                self.root.after(0, lambda count=current_review_count: 
                                self.status_var.set(f"Loaded {count} reviews, scrolling for more..."))
                
                # If we have enough reviews or if no new reviews loaded
                if current_review_count >= num_reviews or current_review_count == prev_review_count:
                    if scroll_attempt > 3:  # Make sure we tried a few scrolls
                        break
                
                prev_review_count = current_review_count
            
            # Extract reviews
            self.root.after(0, lambda: self.status_var.set("Extracting review data..."))
            
            # Find review elements again using XPath to make sure we have the most current ones
            review_elements = self.driver.find_elements(
                By.XPATH,
                "//div[.//span[contains(@aria-label, 'star') or contains(@aria-label, 'Star')]]"
            )
            
            # If no reviews found, try alternative XPaths
            if not review_elements:
                review_elements = self.driver.find_elements(
                    By.XPATH,
                    "//div[.//div[contains(., '★') or contains(., 'stars')]]"
                )
            
            # If still no results, try a more general approach
            if not review_elements:
                review_elements = self.driver.find_elements(
                    By.XPATH,
                    "//div[.//span[@role='img'] and (.//button or .//time)]"
                )
                
            for i, review_element in enumerate(review_elements[:num_reviews]):
                try:
                    # Extract reviewer name using XPath
                    try:
                        name = review_element.find_element(By.XPATH, ".//a[1]").text
                    except NoSuchElementException:
                        try:
                            name = review_element.find_element(By.XPATH, ".//*[self::div or self::span][text()][1]").text
                        except:
                            name = "Anonymous"
                    
                    # Extract rating using XPath
                    try:
                        rating_element = review_element.find_element(By.XPATH, ".//span[contains(@aria-label, 'star') or contains(@aria-label, 'Star')]")
                        aria_label = rating_element.get_attribute('aria-label')
                        rating = re.search(r'(\d+)', aria_label).group(1) if aria_label else "N/A"
                    except:
                        try:
                            # Alternative XPath for ratings
                            rating_text = review_element.find_element(By.XPATH, ".//*[contains(., '★')]").text
                            rating = re.search(r'(\d+)', rating_text).group(1) if rating_text else "N/A"
                        except:
                            rating = "N/A"
                    
                    # Extract date using XPath
                    try:
                        date = review_element.find_element(By.XPATH, ".//time | .//span[contains(text(), 'ago') or contains(text(), '/')]").text
                    except:
                        try:
                            # Alternative XPath for dates
                            date = review_element.find_element(By.XPATH, ".//*[contains(text(), 'day') or contains(text(), 'week') or contains(text(), 'month') or contains(text(), 'year')]").text
                        except:
                            date = "Unknown date"
                    
                    # Try to expand review text using XPath
                    try:
                        more_button = review_element.find_element(By.XPATH, ".//button[contains(., 'More') or contains(., 'more')]")
                        more_button.click()
                        time.sleep(0.2)
                    except:
                        pass  # No "more" button
                    
                    # Extract review text using XPath
                    try:
                        review_text = review_element.find_element(By.XPATH, ".//span[not(contains(@jsaction, 'mouseout'))]//span[string-length(text()) > 5] | .//div[string-length(text()) > 10]").text
                    except:
                        try:
                            # Alternative XPath for review text
                            review_text = review_element.find_element(By.XPATH, ".//*[self::span or self::div][string-length(text()) > 10]").text
                        except:
                            review_text = "No review text found"
                    
                    # Store review data
                    review_data = {
                        "name": name,
                        "rating": rating,
                        "date": date,
                        "text": review_text
                    }
                    
                    self.reviews.append(review_data)
                    
                    # Update UI with each review
                    self.root.after(0, lambda review=review_data: 
                                    self.reviews_tree.insert("", tk.END, values=(
                                        review["name"],
                                        review["rating"],
                                        review["date"],
                                        review["text"]
                                    )))
                    
                except Exception as e:
                    print(f"Error extracting review data: {e}")
            
            # Generate analytics
            self.root.after(0, self.generate_analytics)
            
            # Re-enable UI elements
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))
            
            # Update status
            self.root.after(0, lambda count=len(self.reviews): 
                           self.status_var.set(f"Completed! Scraped {count} reviews"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error scraping reviews: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to scrape reviews: {str(e)}"))
            self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))
    
    def generate_analytics(self):
        # Clear previous widgets
        for widget in self.analytics_frame.winfo_children():
            widget.destroy()
            
        if not self.reviews:
            ttk.Label(self.analytics_frame, text="No reviews to analyze").pack(pady=20)
            return
            
        # Create figures for analytics
        fig = plt.Figure(figsize=(10, 8), dpi=100)
        
        # Rating distribution
        ratings = [int(review["rating"]) for review in self.reviews if review["rating"].isdigit()]
        
        ax1 = fig.add_subplot(221)
        ax1.hist(ratings, bins=5, range=(1, 6), rwidth=0.8, color='skyblue')
        ax1.set_title('Rating Distribution')
        ax1.set_xlabel('Rating')
        ax1.set_ylabel('Number of Reviews')
        ax1.set_xticks(range(1, 6))
        
        # Average rating
        avg_rating = np.mean(ratings) if ratings else 0
        ax2 = fig.add_subplot(222)
        ax2.bar(['Average Rating'], [avg_rating], color='lightgreen')
        ax2.set_title(f'Average Rating: {avg_rating:.2f}')
        ax2.set_ylim(0, 5)
        
        # Text length analysis
        text_lengths = [len(review["text"]) for review in self.reviews]
        ax3 = fig.add_subplot(223)
        ax3.hist(text_lengths, bins=10, color='salmon')
        ax3.set_title('Review Length Distribution')
        ax3.set_xlabel('Character Count')
        ax3.set_ylabel('Number of Reviews')
        
        # Add the plot to the UI
        canvas = FigureCanvasTkAgg(fig, master=self.analytics_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Export buttons frame
        export_frame = ttk.Frame(self.analytics_frame)
        export_frame.pack(fill=tk.X, pady=10)
        
        # Add export buttons
        ttk.Button(export_frame, text="Export to CSV", 
                  command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Export to Excel", 
                  command=self.export_to_excel).pack(side=tk.LEFT, padx=5)
        
    def export_to_csv(self):
        if not self.reviews:
            messagebox.showinfo("Info", "No reviews to export")
            return
            
        try:
            # Create DataFrame
            df = pd.DataFrame(self.reviews)
            
            # Get timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to file
            filename = f"google_reviews_{timestamp}.csv"
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("Success", f"Reviews exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def export_to_excel(self):
        if not self.reviews:
            messagebox.showinfo("Info", "No reviews to export")
            return
            
        try:
            # Create DataFrame
            df = pd.DataFrame(self.reviews)
            
            # Get timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to file
            filename = f"google_reviews_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            
            messagebox.showinfo("Success", f"Reviews exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def _initialize_driver(self):
        self.root.after(0, lambda: self.status_var.set("Initializing undetected-chromedriver..."))
        
        try:
            options = uc.ChromeOptions()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            
            # Initialize the undetected Chrome driver
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            self.root.after(0, lambda: self.status_var.set("Web driver initialized successfully"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error initializing driver: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", 
                           f"Failed to initialize undetected-chromedriver: {str(e)}\nPlease run 'pip install undetected-chromedriver' if not already installed."))
        
    def on_closing(self):
        if self.driver:
            self.driver.quit()
        self.root.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = GoogleMapsReviewScraper(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        # Show error if anything goes wrong
        import traceback
        traceback_text = traceback.format_exc()
        print(f"Error: {str(e)}\n{traceback_text}")
        
        # Try to show error in GUI if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error Starting Application", 
                               f"Error: {str(e)}\n\nPlease check the console for details.")
        except:
            pass