import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from selenium_stealth import stealth
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Job, Post, JobLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacebookGroupScraper:
    def __init__(self, job_id: int):
        self.job_id = job_id
        self.driver = None
        self.db = SessionLocal()
        self.user_agent = UserAgent()
        
    def setup_driver(self):
        """Setup Chrome driver with stealth configuration"""
        try:
            # Chrome options for stealth mode
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument(f'--user-agent={self.user_agent.random}')
            
            # Use undetected-chromedriver
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Apply selenium-stealth
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            # Additional stealth measures
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Driver setup completed for job {self.job_id}")
            self.log_message("INFO", "Browser driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup driver: {str(e)}")
            self.log_message("ERROR", f"Failed to setup driver: {str(e)}")
            raise
    
    def human_like_scroll(self):
        """Simulate human-like scrolling behavior"""
        scroll_pause_time = random.uniform(2, 5)
        scroll_height = random.randint(300, 800)
        
        self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
        time.sleep(scroll_pause_time)
        
        # Random chance to scroll back up a bit
        if random.random() < 0.3:
            back_scroll = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
            time.sleep(random.uniform(1, 2))
    
    def random_delay(self, min_seconds=2, max_seconds=10):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scrape_group(self, group_url: str, max_posts: int = 100) -> List[Dict]:
        """Scrape posts from a Facebook group"""
        posts_data = []
        
        try:
            self.log_message("INFO", f"Starting to scrape group: {group_url}")
            
            # Navigate to the group
            self.driver.get(group_url)
            self.random_delay(3, 7)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract group name
            group_name = self.extract_group_name()
            
            posts_scraped = 0
            scroll_attempts = 0
            max_scroll_attempts = 50
            
            while posts_scraped < max_posts and scroll_attempts < max_scroll_attempts:
                # Find post elements
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-pagelet="FeedUnit_0"], [role="article"]')
                
                for post_element in post_elements[posts_scraped:]:
                    try:
                        post_data = self.extract_post_data(post_element, group_name, group_url)
                        if post_data and not self.is_duplicate_post(post_data['post_id']):
                            posts_data.append(post_data)
                            posts_scraped += 1
                            
                            if posts_scraped >= max_posts:
                                break
                                
                    except Exception as e:
                        logger.warning(f"Error extracting post data: {str(e)}")
                        continue
                
                # Scroll to load more posts
                self.human_like_scroll()
                scroll_attempts += 1
                
                # Check if we've reached the end
                if scroll_attempts % 10 == 0:
                    self.log_message("INFO", f"Scraped {posts_scraped} posts so far...")
            
            self.log_message("INFO", f"Completed scraping group. Total posts: {len(posts_data)}")
            
        except Exception as e:
            logger.error(f"Error scraping group {group_url}: {str(e)}")
            self.log_message("ERROR", f"Error scraping group: {str(e)}")
        
        return posts_data
    
    def extract_group_name(self) -> str:
        """Extract the group name from the page"""
        try:
            # Try multiple selectors for group name
            selectors = [
                'h1[data-testid="group-name"]',
                'h1',
                '[data-testid="page-title"]'
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.text.strip():
                        return element.text.strip()
                except NoSuchElementException:
                    continue
            
            return "Unknown Group"
            
        except Exception as e:
            logger.warning(f"Could not extract group name: {str(e)}")
            return "Unknown Group"
    
    def extract_post_data(self, post_element, group_name: str, group_url: str) -> Dict:
        """Extract data from a single post element"""
        try:
            post_data = {
                'group_name': group_name,
                'author_name': '',
                'author_url': '',
                'content': '',
                'timestamp': None,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'post_url': '',
                'post_id': '',
                'media_urls': []
            }
            
            # Extract author information
            try:
                author_link = post_element.find_element(By.CSS_SELECTOR, 'a[role="link"]')
                post_data['author_name'] = author_link.text.strip()
                post_data['author_url'] = author_link.get_attribute('href')
            except NoSuchElementException:
                pass
            
            # Extract post content
            try:
                content_selectors = [
                    '[data-testid="post_message"]',
                    '[data-ad-preview="message"]',
                    '.userContent',
                    'div[data-testid="post_message"] span'
                ]
                
                for selector in content_selectors:
                    try:
                        content_element = post_element.find_element(By.CSS_SELECTOR, selector)
                        if content_element.text.strip():
                            post_data['content'] = content_element.text.strip()
                            break
                    except NoSuchElementException:
                        continue
            except Exception:
                pass
            
            # Extract engagement metrics
            try:
                # Likes
                like_elements = post_element.find_elements(By.CSS_SELECTOR, '[aria-label*="like"], [aria-label*="reaction"]')
                for element in like_elements:
                    aria_label = element.get_attribute('aria-label') or ''
                    if 'like' in aria_label.lower():
                        # Extract number from aria-label
                        import re
                        numbers = re.findall(r'\d+', aria_label)
                        if numbers:
                            post_data['likes'] = int(numbers[0])
                        break
                
                # Comments
                comment_elements = post_element.find_elements(By.CSS_SELECTOR, '[aria-label*="comment"]')
                for element in comment_elements:
                    aria_label = element.get_attribute('aria-label') or ''
                    if 'comment' in aria_label.lower():
                        import re
                        numbers = re.findall(r'\d+', aria_label)
                        if numbers:
                            post_data['comments'] = int(numbers[0])
                        break
                
                # Shares
                share_elements = post_element.find_elements(By.CSS_SELECTOR, '[aria-label*="share"]')
                for element in share_elements:
                    aria_label = element.get_attribute('aria-label') or ''
                    if 'share' in aria_label.lower():
                        import re
                        numbers = re.findall(r'\d+', aria_label)
                        if numbers:
                            post_data['shares'] = int(numbers[0])
                        break
                        
            except Exception as e:
                logger.debug(f"Could not extract engagement metrics: {str(e)}")
            
            # Generate a unique post ID based on content and author
            import hashlib
            unique_string = f"{post_data['author_name']}_{post_data['content'][:100]}_{group_name}"
            post_data['post_id'] = hashlib.md5(unique_string.encode()).hexdigest()
            
            # Set timestamp to current time if not found
            post_data['timestamp'] = datetime.now()
            
            return post_data
            
        except Exception as e:
            logger.error(f"Error extracting post data: {str(e)}")
            return None
    
    def is_duplicate_post(self, post_id: str) -> bool:
        """Check if post already exists in database"""
        existing_post = self.db.query(Post).filter(Post.post_id == post_id).first()
        return existing_post is not None
    
    def save_posts_to_db(self, posts_data: List[Dict]):
        """Save scraped posts to database"""
        try:
            for post_data in posts_data:
                if not self.is_duplicate_post(post_data['post_id']):
                    post = Post(
                        job_id=self.job_id,
                        post_id=post_data['post_id'],
                        group_name=post_data['group_name'],
                        author_name=post_data['author_name'],
                        author_url=post_data['author_url'],
                        content=post_data['content'],
                        timestamp=post_data['timestamp'],
                        likes=post_data['likes'],
                        comments=post_data['comments'],
                        shares=post_data['shares'],
                        post_url=post_data['post_url'],
                        media_urls=post_data['media_urls']
                    )
                    self.db.add(post)
            
            self.db.commit()
            self.log_message("INFO", f"Saved {len(posts_data)} posts to database")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving posts to database: {str(e)}")
            self.log_message("ERROR", f"Error saving posts: {str(e)}")
    
    def log_message(self, level: str, message: str):
        """Log message to database"""
        try:
            log_entry = JobLog(
                job_id=self.job_id,
                level=level,
                message=message
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log message: {str(e)}")
    
    def run_scraping_job(self):
        """Main method to run the scraping job"""
        try:
            # Get job details
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if not job:
                raise Exception(f"Job {self.job_id} not found")
            
            # Update job status
            job.status = "running"
            job.last_run = datetime.now()
            self.db.commit()
            
            self.setup_driver()
            
            all_posts = []
            config = job.config or {}
            max_posts_per_group = config.get('max_posts_per_group', 50)
            
            for group_url in job.group_urls:
                self.log_message("INFO", f"Processing group: {group_url}")
                posts = self.scrape_group(group_url, max_posts_per_group)
                all_posts.extend(posts)
                
                # Random delay between groups
                self.random_delay(5, 15)
            
            # Save all posts to database
            self.save_posts_to_db(all_posts)
            
            # Update job completion
            job.status = "completed"
            job.total_posts = len(all_posts)
            self.db.commit()
            
            self.log_message("INFO", f"Job completed successfully. Total posts scraped: {len(all_posts)}")
            
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {str(e)}")
            self.log_message("ERROR", f"Job failed: {str(e)}")
            
            # Update job status to failed
            job = self.db.query(Job).filter(Job.id == self.job_id).first()
            if job:
                job.status = "failed"
                self.db.commit()
                
        finally:
            if self.driver:
                self.driver.quit()
            self.db.close()

def run_scraping_job(job_id: int):
    """Function to run scraping job - called by Celery task"""
    scraper = FacebookGroupScraper(job_id)
    scraper.run_scraping_job()

