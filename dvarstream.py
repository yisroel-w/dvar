from selenium import webdriver #type: ignore
from selenium.webdriver.chrome.service import Service as ChromeService #type: ignore
from webdriver_manager.chrome import ChromeDriverManager #type: ignore
from selenium.webdriver.common.by import By #type: ignore
from selenium.webdriver.support.ui import WebDriverWait #type: ignore
from selenium.webdriver.support import expected_conditions as EC #type: ignore
import os
import time
import fitz as fitz #type: ignore
from base64 import b64decode
from dateutil.relativedelta import relativedelta #type: ignore
from datetime import date #type: ignore
from datetime import datetime as dt #type: ignore
from datetime import timedelta #type: ignore
import streamlit as st #type: ignore
import markdownlit #type: ignore
# from markdownlit import mdlit as mdlit # Alias not used if calling markdownlit.mdlit
import streamlit_toggle_switch as stt # type: ignore # Matching requirements.txt; was streamlit_toggle
from streamlit_pills_multiselect import pills #type: ignore
import PyPDF2 #type: ignore
from PyPDF2 import PdfMerger #type: ignore
import glob
# import json # Not used
from pyluach import parshios, dates #type: ignore

st.set_page_config(page_title="Dvar Creator (BETA)", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

# --- Global Selenium Options ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
# Explicitly set download directory to current working directory for consistency
# This is crucial for the download detection logic.
chrome_options.add_experimental_option('prefs', {
    "download.default_directory": os.getcwd(),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True # Helps ensure PDF is downloaded, not viewed in-browser plugin
})

# --- Helper for Filenames ---
def format_dt_for_filename(dt_obj: dt) -> str:
    """Formats a datetime object into a string suitable for filenames."""
    return dt_obj.strftime("%Y%m%d_%H%M%S_%f")

# --- Selenium Driver Creation ---
def create_driver():
    """Creates and returns a Selenium WebDriver instance."""
    try:
        # Using WebDriverManager to handle driver binaries.
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        # Implicit wait can be useful as a safety net, though explicit waits are preferred.
        # driver.implicitly_wait(5) # Optional: wait up to 5 seconds for elements if not immediately found
        return driver
    except Exception as e:
        st.error(f"Failed to create Chrome driver via WebDriverManager: {e}")
        st.info("Ensure internet connectivity for WebDriverManager to download the driver if needed.")
        # Fallback to system chromedriver if WebDriverManager fails
        try:
            st.info("Attempting to use system chromedriver from /usr/bin/chromedriver (if installed via packages.txt)")
            system_driver_path = "/usr/bin/chromedriver"
            if os.path.exists(system_driver_path):
                 driver = webdriver.Chrome(service=ChromeService(executable_path=system_driver_path), options=chrome_options)
                 # driver.implicitly_wait(5) # Optional
                 return driver
            else:
                st.error(f"System chromedriver not found at {system_driver_path}.")
                raise e # Re-raise original error if fallback also fails to find path
        except Exception as fallback_e:
            st.error(f"Fallback to system chromedriver also failed: {fallback_e}")
            # Propagate the error to stop execution if no driver can be created.
            # The calling function should handle a None return if it can proceed without a driver for some operations.
            return None


# --- Selenium-based PDF Fetching Functions ---
def dvarget(session2_dt_obj: dt):
    """
    Attempts to retrieve the Dvar Malchus PDF.
    IMPORTANT: This function relies on specific XPaths from dvarmalchus.org.
    If the website structure changes, these XPaths will likely break.
    """
    print("Dvarget Running")
    driver = create_driver()
    if not driver:
        st.error("Dvarget: Cannot proceed without a WebDriver.")
        return False

    session2_id_str = format_dt_for_filename(session2_dt_obj)
    target_filename = f"dvar{session2_id_str}.pdf"
    
    try:
        print("Driver Opened for Dvar Malchus")
        driver.get("https://dvarmalchus.org")
        print("Dvar Malchus website opened")
        
        # XPaths to potential download links. These are highly specific and fragile.
        # They should point directly to the <a> (anchor/link) elements.
        xpaths_to_links = [
            # Example structure (replace with actual, verified XPaths):
            # "/html/body/div[1]/some/path/to/a_tag_1",
            # "/html/body/div[1]/another/path/to/a_tag_2"
            # The following are from the original script, verify their current validity.
            "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div/div/div/a", # Main download link
            '/html/body/div[1]/section[2]/div[3]/div/div/div[3]/div/div/a', # Older structure?
            '/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div[1]/div/div/a', # Israel version?
            "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div[2]/div/div/a", # Diaspora version?
            # The following paths seem to be for "latest shiurim" or similar sections, less likely for the weekly booklet.
            '/html/body/div[1]/section[9]/div/div/div/div[3]/div/div/div/div[1]/div/section/div/div/div/section/div/div/div/div/div/div/a',
            '/html/body/div[1]/section[9]/div/div/div/div[3]/div/div/div/div[2]/div/section/div/div/div/section/div/div/div/div/div/div/a'
        ]
        
        found_url = None
        wait = WebDriverWait(driver, 15) # Wait for elements to be present

        for a_tag_xpath in xpaths_to_links:
            try:
                # Wait for the link element to be clickable or present
                link_element = wait.until(EC.presence_of_element_located((By.XPATH, a_tag_xpath)))
                link_text = ""
                try: # Python uses colon, not curly braces
                    # Attempt to get text from a more specific part if needed (e.g., a nested span).
                    # This specific XPath ".//span/span[2]" is based on the original script's attempt.
                    # It means: from the current link_element, find any descendant span that has a child span,
                    # and take the text of that second (child) span.
                    text_span = link_element.find_element(By.XPATH, ".//span/span[2]") 
                    link_text = text_span.text.strip()
                except Exception: # Catch if the specific nested span is not found
                    link_text = link_element.text.strip() # Fallback to the link's direct text

                print(f"Checking link with text: '{link_text}' at XPath: {a_tag_xpath}")

                if "להורדת החוברת השבועית" == link_text and "חו״ל" not in link_text : # Prioritize non-Diaspora if both present
                    print(f"Found 'להורדת החוברת השבועית' (Israel/Main), using {a_tag_xpath}")
                    found_url = link_element.get_attribute("href")
                    break
                elif "להורדת החוברת השבועית - חו״ל" == link_text:
                    print(f"Found 'להורדת החוברת השבועית - חו״ל' (Diaspora), using {a_tag_xpath}")
                    found_url = link_element.get_attribute("href")
                    # Potentially don't break, look for a non-חו״ל version if available.
                    # Or, if this is the *only* one desired, then break. For now, let's assume we take the first valid one.
                    break 
                elif "להורדת החוברת השבועית" in link_text: # More general match as a fallback
                    print(f"Found general 'להורדת החוברת השבועית' variant, using {a_tag_xpath}")
                    found_url = link_element.get_attribute("href")
                    break

            except Exception as e:
                # This XPath didn't yield a clickable element or the expected text.
                print(f"Did not find a valid link with XPath: {a_tag_xpath} (Error: {type(e).__name__})")
                continue
        
        if not found_url:
            st.error("Could not find the Dvar Malchus download link. The website structure might have changed.")
            print("Dvar Malchus download link not found after checking all XPaths.")
            return False

        print(f"Navigating to PDF URL: {found_url}")
        
        download_dir = os.getcwd()
        existing_pdfs_before_download = {f for f in os.listdir(download_dir) if f.endswith(".pdf")}
        
        driver.get(found_url) # This should trigger the download

        # Robust download waiting mechanism
        timeout_seconds = 60 # Increased timeout for potentially large PDF
        poll_interval = 2
        time_elapsed = 0
        downloaded_original_name = None
        
        print("Waiting for PDF download to complete...")
        while time_elapsed < timeout_seconds:
            current_pdfs = {f for f in os.listdir(download_dir) if f.endswith(".pdf")}
            new_pdfs = current_pdfs - existing_pdfs_before_download
            if new_pdfs:
                # Assume the first new PDF is the one we're waiting for.
                # This could be fragile if other PDFs are downloaded simultaneously.
                downloaded_original_name = new_pdfs.pop() 
                downloaded_file_path = os.path.join(download_dir, downloaded_original_name)
                # Check if the file is fully written (basic check: size > 0 and stable for a moment)
                time.sleep(1) # Wait a bit for file write to settle
                if os.path.exists(downloaded_file_path) and os.path.getsize(downloaded_file_path) > 0: # Check existence again
                    print(f"Detected downloaded file: {downloaded_original_name} with size {os.path.getsize(downloaded_file_path)}")
                    break
                else: # File found but empty, might still be downloading
                    print(f"Detected file {downloaded_original_name}, but it's empty or gone. Waiting...")
                    if downloaded_original_name in current_pdfs: # only add back if it's still there and detected by os.listdir
                         existing_pdfs_before_download.add(downloaded_original_name) # Add back to avoid re-detecting immediately
                    downloaded_original_name = None # Reset
            time.sleep(poll_interval)
            time_elapsed += poll_interval
        
        if downloaded_original_name:
            downloaded_file_path = os.path.join(download_dir, downloaded_original_name) # Re-evaluate path
            if os.path.exists(downloaded_file_path): # Ensure file still exists before renaming
                target_path = os.path.join(download_dir, target_filename)
                print(f"Renaming '{downloaded_original_name}' to '{target_filename}'")
                os.rename(downloaded_file_path, target_path)
                return True
            else:
                st.error(f"Downloaded file '{downloaded_original_name}' disappeared before it could be renamed.")
                print(f"Downloaded file '{downloaded_original_name}' disappeared before renaming.")
                return False
        else:
            st.error("Dvar Malchus PDF download timed out or the downloaded file was empty/not verified.")
            print("Dvar Malchus PDF download timed out or failed verification.")
            # driver.save_screenshot("dvar_download_failure.png") # For debugging
            # st.image("dvar_download_failure.png")
            return False

    except Exception as e:
        st.error(f"An error occurred in dvarget: {e}")
        print(f"Error in dvarget: {e}")
        # driver.save_screenshot("dvar_exception.png") # For debugging
        # st.image("dvar_exception.png")
        return False
    finally:
        if driver:
            driver.quit()
            print("Driver quit in dvarget")

def chabad_pdf_fetch_loop(driver, url_template, date_str, pdf_options, temp_pdf_path, section_name):
    """Helper function to fetch a single PDF page from Chabad.org."""
    try:
        full_url = url_template.format(date_str)
        driver.get(full_url)
        # Wait for the main content area to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "content")))
        time.sleep(2) # Allow for JavaScript rendering after content is present
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)['data']
        with open(temp_pdf_path, "ab") as f:
            f.write(b64decode(pdf_data))
        return True
    except Exception as e:
        st.warning(f"Failed to get {section_name} for date corresponding to '{date_str}': {e}")
        print(f"Failed to get {section_name} for {date_str}: {e}")
        return False

def chabadget(dor, opt, session_dt_obj: dt, scale_val: float):
    """Retrieves Chumash and Tanya from Chabad.org for the given dates."""
    session_id_str = format_dt_for_filename(session_dt_obj)
    pdf_options = {
        'scale': scale_val,
        'marginTop': 0.1, 'marginRight': 0.1, 'marginBottom': 0.1, 'marginLeft': 0.1,
        'printBackground': True
    }
    
    driver = None # Initialize driver to None

    # --- Chumash ---
    chumash_filename = f"Chumash{session_id_str}.pdf"
    if 'Chumash' in opt and not os.path.exists(chumash_filename):
        if not driver: driver = create_driver() # Create driver only if needed and not already created
        if not driver: 
            st.error("Chabadget (Chumash): WebDriver not available.")
            return # Cannot proceed

        merger = PdfMerger()
        temp_pdf_path = f"temp_chumash_{session_id_str}.pdf"
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path) # Clean up from previous failed run

        print(f"Fetching Chumash for dates: {dor}")
        for date_param in dor: # 'dor' contains date strings like "MM%2FDD%2FYYYY"
            chabad_pdf_fetch_loop(driver, "https://www.chabad.org/dailystudy/torahreading.asp?tdate={0}#lt=he", 
                                  date_param, pdf_options, temp_pdf_path, "Chumash")
        
        if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 0:
            merger.append(temp_pdf_path)
            merger.write(chumash_filename)
            merger.close()
            os.remove(temp_pdf_path)
            print(f"Chumash PDF created: {chumash_filename}")
        elif not os.path.exists(chumash_filename):
             st.warning("Chumash PDF could not be created as no parts were successfully downloaded.")

    # --- Tanya ---
    tanya_filename = f"Tanya{session_id_str}.pdf"
    if 'Tanya' in opt and not os.path.exists(tanya_filename):
        if not driver: driver = create_driver() # Create driver only if needed
        if not driver:
            st.error("Chabadget (Tanya): WebDriver not available.")
            if 'driver' in locals() and driver: driver.quit() # Clean up if partially created
            return

        merger2 = PdfMerger()
        temp_pdf_path = f"temp_tanya_{session_id_str}.pdf"
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)

        print(f"Fetching Tanya for dates: {dor}")
        for date_param in dor:
            chabad_pdf_fetch_loop(driver, "https://www.chabad.org/dailystudy/tanya.asp?tdate={0}&commentary=false#lt=he",
                                  date_param, pdf_options, temp_pdf_path, "Tanya")

        if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 0:
            merger2.append(temp_pdf_path)
            merger2.write(tanya_filename)
            merger2.close()
            os.remove(temp_pdf_path)
            print(f"Tanya PDF created: {tanya_filename}")
        elif not os.path.exists(tanya_filename):
            st.warning("Tanya PDF could not be created as no parts were successfully downloaded.")
    
    if driver: # Quit driver if it was created and used in this function
        driver.quit()
        print("Driver quit in chabadget")


def rambamenglish(dor, session_dt_obj: dt, opt, scale_val: float):
    """Retrieves various Rambam versions from Chabad.org."""
    session_id_str = format_dt_for_filename(session_dt_obj)
    rambam_filename = f"Rambam{session_id_str}.pdf"

    selected_rambam_opt_str = None
    for r_opt_key in ['Rambam (3)-Bilingual', 'Rambam (3)-Hebrew', 'Rambam (3)-English', 
                      'Rambam (1)-Bilingual', 'Rambam (1)-Hebrew', 'Rambam (1)-English']:
        if r_opt_key in opt:
            selected_rambam_opt_str = r_opt_key
            break
    
    if not selected_rambam_opt_str:
        return # No relevant Rambam option selected

    if os.path.exists(rambam_filename):
        print(f"Rambam PDF {rambam_filename} already exists. Skipping.")
        return

    pdf_options = {
        'scale': scale_val,
        'marginTop': 0.1, 'marginRight': 0.1, 'marginBottom': 0.1, 'marginLeft': 0.1,
        'printBackground': True
    }
    
    lang_code, chapter_count_str = "", ""
    if "Rambam (3)-Bilingual" == selected_rambam_opt_str: lang_code, chapter_count_str = "both", "3"
    elif "Rambam (3)-Hebrew" == selected_rambam_opt_str: lang_code, chapter_count_str = "he", "3"
    elif "Rambam (3)-English" == selected_rambam_opt_str: lang_code, chapter_count_str = "primary", "3"
    elif "Rambam (1)-Bilingual" == selected_rambam_opt_str: lang_code, chapter_count_str = "both", "1"
    elif "Rambam (1)-Hebrew" == selected_rambam_opt_str: lang_code, chapter_count_str = "he", "1"
    elif "Rambam (1)-English" == selected_rambam_opt_str: lang_code, chapter_count_str = "primary", "1"
    
    if not lang_code or not chapter_count_str:
        st.warning(f"Could not determine Rambam URL parameters for option: {selected_rambam_opt_str}")
        return

    driver = create_driver()
    if not driver:
        st.error(f"Rambamenglish ({selected_rambam_opt_str}): WebDriver not available.")
        return

    merger = PdfMerger()
    temp_pdf_path = f"temp_rambam_{session_id_str}.pdf"
    if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)

    print(f"Fetching Rambam ({selected_rambam_opt_str}) for dates: {dor}")
    url_template = f"https://www.chabad.org/dailystudy/rambam.asp?rambamchapters={chapter_count_str}&tdate={{0}}#lt={lang_code}"
    for date_param in dor:
        chabad_pdf_fetch_loop(driver, url_template, date_param, pdf_options, temp_pdf_path, f"Rambam ({selected_rambam_opt_str})")
    
    if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 0:
        merger.append(temp_pdf_path)
        merger.write(rambam_filename)
        merger.close()
        os.remove(temp_pdf_path)
        print(f"Rambam PDF created: {rambam_filename}")
    elif not os.path.exists(rambam_filename):
        st.warning(f"Rambam PDF ({selected_rambam_opt_str}) could not be created.")
    
    if driver:
        driver.quit()
        print("Driver quit in rambamenglish")


def hayomyom(dor, session_dt_obj: dt, scale_val: float):
    """Gets Hayom Yom from Chabad.org."""
    session_id_str = format_dt_for_filename(session_dt_obj)
    hayom_filename = f"Hayom{session_id_str}.pdf"

    if os.path.exists(hayom_filename):
        print(f"Hayom Yom PDF {hayom_filename} already exists. Skipping.")
        return

    pdf_options = {
        'scale': scale_val,
        'marginTop': 0.1, 'marginRight': 0.1, 'marginBottom': 0.1, 'marginLeft': 0.1,
        'printBackground': True
    }
    
    driver = create_driver()
    if not driver:
        st.error("Hayomyom: WebDriver not available.")
        return

    merger3 = PdfMerger()
    temp_pdf_path = f"temp_hayom_{session_id_str}.pdf"
    if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)

    print(f"Fetching Hayom Yom for dates: {dor}")
    url_template = "https://www.chabad.org/dailystudy/hayomyom.asp?tdate={0}"
    for date_param in dor:
        chabad_pdf_fetch_loop(driver, url_template, date_param, pdf_options, temp_pdf_path, "Hayom Yom")
            
    if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 0:
        merger3.append(temp_pdf_path)
        merger3.write(hayom_filename)
        merger3.close()
        os.remove(temp_pdf_path)
        print(f"Hayom Yom PDF created: {hayom_filename}")
    elif not os.path.exists(hayom_filename):
        st.warning("Hayom Yom PDF could not be created.")
    
    if driver:
        driver.quit()
        print("Driver quit in hayomyom")

def parshaget(date1_str: str):
    """Gets parsha from date for Shnayim Mikra."""
    year, month, day = map(int, date1_str.split(", "))
    parsha = parshios.getparsha_string(dates.GregorianDate(year, month, day), israel=False, hebrew=True)
    # st.write(f"This week's parsha is {parsha}.") # Displayed in pill label now
    return parsha

def shnayimget(session2_dt_obj: dt, parsha: str):
    """Gets Shnayim Mikra PDF from a GitHub repository."""
    session2_id_str = format_dt_for_filename(session2_dt_obj)
    target_filename = f"Shnayim{session2_id_str}.pdf"

    if os.path.exists(target_filename):
        print(f"Shnayim Mikra PDF {target_filename} for {parsha} already exists. Skipping.")
        return True

    # Construct URL and expected downloaded filename (GitHub raw usually preserves it)
    parsha_url_segment = "%20".join(parsha.split(" "))
    github_url = f"https://github.com/emkay5771/shnayimfiles/blob/master/{parsha_url_segment}.pdf?raw=true"
    # The name GitHub will likely use for the downloaded file
    expected_downloaded_filename = f"{parsha}.pdf" 

    driver = create_driver()
    if not driver:
        st.error(f"Shnayimget (Parsha {parsha}): WebDriver not available.")
        return False
    
    download_success = False
    try:
        print(f"Attempting to download Shnayim Mikra for {parsha} from: {github_url}")

        download_dir = os.getcwd()
        # Set of PDFs before attempting download
        existing_pdfs_before_download = {f for f in os.listdir(download_dir) if f.endswith(".pdf")}
        
        driver.get(github_url) # Triggers download

        # Wait for download completion
        timeout_seconds = 45  # Increased timeout
        poll_interval = 1
        time_elapsed = 0
        actual_downloaded_name = None
        
        print(f"Waiting for Shnayim Mikra PDF '{expected_downloaded_filename}' to download...")
        while time_elapsed < timeout_seconds:
            current_pdfs = {f for f in os.listdir(download_dir) if f.endswith(".pdf")}
            new_pdfs = current_pdfs - existing_pdfs_before_download
            
            for new_pdf_filename in new_pdfs:
                if new_pdf_filename == expected_downloaded_filename: # Exact match
                    actual_downloaded_name = new_pdf_filename
                    break
                # Optional: more lenient check if filename varies slightly (e.g. "(1)" suffix)
                # For now, requires exact match or takes the first new PDF if no exact match.
            
            if actual_downloaded_name: # Exact match found
                break
            elif not actual_downloaded_name and new_pdfs: # No exact match, but a new PDF appeared
                actual_downloaded_name = new_pdfs.pop() # Take one of them
                st.warning(f"Shnayim Mikra downloaded as '{actual_downloaded_name}', expected '{expected_downloaded_filename}'. Proceeding with the downloaded file.")
                break 

            time.sleep(poll_interval)
            time_elapsed += poll_interval

        if actual_downloaded_name:
            downloaded_file_path = os.path.join(download_dir, actual_downloaded_name)
            # Verify file is not empty
            if os.path.exists(downloaded_file_path) and os.path.getsize(downloaded_file_path) > 0:
                print(f"Successfully downloaded Shnayim Mikra: {actual_downloaded_name}")
                os.rename(downloaded_file_path, target_filename)
                print(f"Renamed Shnayim Mikra to: {target_filename}")
                download_success = True
            else:
                st.error(f"Shnayim Mikra PDF '{actual_downloaded_name}' downloaded but is empty or missing.")
                if os.path.exists(downloaded_file_path): os.remove(downloaded_file_path) # Clean up empty file
        else:
            st.error(f"Shnayim Mikra PDF download for '{parsha}' timed out or file not found/verified.")
            print(f"Shnayim Mikra PDF download for '{parsha}' timed out.")
    
    except Exception as e:
        st.error(f"Error in shnayimget for parsha '{parsha}': {e}")
        print(f"Error in shnayimget: {e}")
    finally:
        if driver:
            driver.quit()
            print("Driver quit in shnayimget")
    return download_success


def daytoheb(week_days_en, dow_hebrew_list):
    """Converts English day names to Hebrew for Dvar Malchus parsing."""
    day_map_en_to_he = {
        'Sunday': 'יום ראשון', 'Monday': 'יום שני', 'Tuesday': 'יום שלישי', 
        'Wednesday': 'יום רביעי', 'Thursday': 'יום חמישי', 'Friday': 'יום שישי', 
        'Shabbos': 'שבת קודש'
    }
    for day_en in week_days_en:
        dow_hebrew_list.append(day_map_en_to_he.get(day_en, day_en)) # Append original if not in map
    return dow_hebrew_list

def opttouse(selected_options_en, options_for_dvar_malchus_he):
    """Converts selected English option names to Hebrew/specific names for Dvar Malchus TOC parsing."""
    for opt_item_en in selected_options_en:
        converted_opt = None
        if opt_item_en == 'Chumash': converted_opt = 'חומש יומי'
        elif opt_item_en == 'Tanya': converted_opt = 'תניא יומי'
        elif opt_item_en == 'Rambam (3)-Hebrew': converted_opt = 'רמב"ם - שלושה פרקים ליום' # Dvar Malchus specific Rambam
        elif opt_item_en == 'Haftorah' or opt_item_en == 'Krias Hatorah (includes Haftorah)':
            converted_opt = 'חומש לקריאה בציבור' # This Dvar Malchus section contains both
        elif opt_item_en == 'Project Likutei Sichos (Hebrew)': converted_opt = 'לקוטי שיחות'
        elif opt_item_en == 'Maamarim': converted_opt = 'מאמרים'
        # Options handled by separate Chabad.org downloads or specific files, but still need to be in optconv for dynamicmake logic
        elif 'Rambam' in opt_item_en and opt_item_en != 'Rambam (3)-Hebrew': # Other Rambam versions
             converted_opt = opt_item_en
        elif opt_item_en == 'Hayom Yom': converted_opt = opt_item_en
        elif opt_item_en == 'Shnayim Mikra': converted_opt = opt_item_en
        
        if converted_opt and converted_opt not in options_for_dvar_malchus_he:
            options_for_dvar_malchus_he.append(converted_opt)
    return options_for_dvar_malchus_he
        
def daytorambam(week_days_en, dates_for_chabad_url_list):
    """Converts selected English day names to date strings (M/D/Y) for Chabad.org URLs."""
    today = date.today()
    # map English day name to integer offset for relativedelta
    day_to_weekday_offset = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Shabbos': 5, 'Sunday': 6}
    for day_en in week_days_en:
        offset = day_to_weekday_offset.get(day_en)
        if offset is not None:
            # Calculate the date for the upcoming occurrence of that day of the week
            target_date = today + relativedelta(weekday=offset)
            year_str, month_str, day_str = str(target_date).split("-")
            # Format for Chabad.org URL: MM%2FDD%2FYYYY
            dates_for_chabad_url_list.append(f'{month_str}%2F{day_str}%2F{year_str}')
    return dates_for_chabad_url_list

def find_next_top_level_bookmark(toc_list, current_bookmark_index):
    """
    Finds the page number of the next top-level bookmark in a PyMuPDF TOC list.
    A top-level bookmark has level 1.
    Returns page number (1-indexed) or None.
    """
    current_level = toc_list[current_bookmark_index][0]
    for i in range(current_bookmark_index + 1, len(toc_list)):
        if toc_list[i][0] <= current_level: # Found next bookmark at same or higher level
             # If it's a top-level bookmark (level 1), this is what we want for sections like Maamarim/Sichos
            if toc_list[i][0] == 1:
                return toc_list[i][2] # Return page number (1-indexed)
            # If it's not level 1, but same or higher than current, it still defines the end of current section
            # This part of logic depends on how deep the TOC structure is for the item.
            # For now, focusing on next top-level for simplicity as in original for Maamarim/Sichos.
            # For day-specific items, the end page is determined by the *next item at the same sub-level*.
            # The subtraction of 1 or 2 from the page number happens in the caller.
    return None # No subsequent top-level bookmark found

# The 'dedupe' function attempts to prevent overlapping page ranges when extracting from Dvar Malchus.
# Its logic is based on the observed structure and bookmarking of Dvar Malchus PDFs.
# It maintains lists (pages, pages2, pages3) that seem to track used pages/ranges.
# This function is highly specific and potentially fragile if Dvar Malchus PDF structure changes.
def dedupe(pages_already_used_set, # Using a set for faster lookups of individual pages
           _pages2_list_unused, # This list was appended to but not read in the original. Keep for now.
           _pages3_list_unused, # This list was appended to but not read in the original. Keep for now.
           start_page_0idx, end_page_0idx):
    """Adjusts start/end pages to avoid overlap with previously used pages."""
    
    # _pages2_list_unused.append(start_page_0idx) # Original script did this
    # _pages2_list_unused.append(end_page_0idx)   # Original script did this

    adjusted_start_page = start_page_0idx
    adjusted_end_page = end_page_0idx

    # If the proposed start page is already used, try to shift start by one.
    if start_page_0idx in pages_already_used_set:
        adjusted_start_page = start_page_0idx + 1
    
    # If the proposed end page is already used, try to shift end by one.
    if end_page_0idx in pages_already_used_set: # Check original end_page_0idx before adjustment
        adjusted_end_page = end_page_0idx - 1

    # Add the (potentially adjusted) new pages to the set of used pages.
    # This simple addition might not perfectly capture ranges, but reflects original intent.
    # A more robust approach would be to store ranges and check for overlaps.
    if adjusted_start_page <= adjusted_end_page: # Only add if range is valid
        for p in range(adjusted_start_page, adjusted_end_page + 1):
            pages_already_used_set.add(p)
    
    # _pages3_list_unused.append(adjusted_start_page) # Original script did this
    # _pages3_list_unused.append(adjusted_end_page)   # Original script did this
    
    return adjusted_start_page, adjusted_end_page


def dynamicmake(dow_hebrew_selected_days, optconv_dvar_malchus_sections, opt_selected_overall, 
                source_is_dvar_malchus_primary, session_dt_obj: dt, session2_dt_obj_for_weekly_files: dt, 
                include_dvar_malchus_cover: bool):
    """
    Compiles the final PDF from various sources based on user selections.
    - session_dt_obj: For files unique to this run (Chabad.org daily, final output).
    - session2_dt_obj_for_weekly_files: For potentially cached weekly files (Dvar Malchus, Shnayim Mikra).
    """
    session_id_str = format_dt_for_filename(session_dt_obj)
    session2_id_str = format_dt_for_filename(session2_dt_obj_for_weekly_files)
    
    output_filename = f"output_dynamic{session_id_str}.pdf"
    doc_out = fitz.open() # The final output PDF document
    
    # --- Dvar Malchus Processing Variables ---
    dvar_malchus_doc_source = None # PyMuPDF document object for Dvar Malchus
    dvar_malchus_toc_list = []    # Table of Contents from Dvar Malchus PDF
    
    # Set for tracking pages extracted from Dvar Malchus to attempt to avoid duplicates via `dedupe`
    dvar_malchus_pages_extracted_set = set() 
    # These lists were part of the original `dedupe` logic, their exact use was unclear but maintained.
    # They are not directly used for decision making in the revised `dedupe` but were passed.
    _legacy_dedupe_pages2_list = [] 
    _legacy_dedupe_pages3_list = []


    # --- Attempt to Load Dvar Malchus if it's the primary source ---
    if source_is_dvar_malchus_primary:
        dvar_malchus_pdf_path = f"dvar{session2_id_str}.pdf"
        if os.path.exists(dvar_malchus_pdf_path):
            try:
                print(f"Opening Dvar Malchus PDF: {dvar_malchus_pdf_path}")
                dvar_malchus_doc_source = fitz.open(dvar_malchus_pdf_path)
                dvar_malchus_toc_list = dvar_malchus_doc_source.get_toc()
                print(f"Dvar Malchus TOC loaded with {len(dvar_malchus_toc_list)} entries.")
                if include_dvar_malchus_cover and dvar_malchus_doc_source.page_count > 0:
                    doc_out.insert_pdf(dvar_malchus_doc_source, from_page=0, to_page=0)
                    print("Added Dvar Malchus cover page.")
            except Exception as e:
                st.warning(f"Could not open/process Dvar Malchus PDF '{dvar_malchus_pdf_path}': {e}. Will fall back to Chabad.org for relevant content.")
                source_is_dvar_malchus_primary = False # Fallback
                if dvar_malchus_doc_source: dvar_malchus_doc_source.close()
                dvar_malchus_doc_source = None
                dvar_malchus_toc_list = []
        else:
            st.warning(f"Dvar Malchus PDF '{dvar_malchus_pdf_path}' not found. Will use Chabad.org for relevant content.")
            source_is_dvar_malchus_primary = False # Fallback

    # --- Main Content Assembly ---
    # If Dvar Malchus is NOT the source (either by choice, or due to fallback)
    if not source_is_dvar_malchus_primary:
        print("Processing with Chabad.org as primary source (or due to Dvar Malchus fallback).")
        for option_name in opt_selected_overall:
            pdf_to_add_path = None
            if option_name == 'Chumash': pdf_to_add_path = f"Chumash{session_id_str}.pdf"
            elif option_name == 'Tanya': pdf_to_add_path = f"Tanya{session_id_str}.pdf"
            # Generic catch for any Rambam variant if sourced from Chabad.org
            elif 'Rambam' in option_name: pdf_to_add_path = f"Rambam{session_id_str}.pdf"
            elif option_name == 'Hayom Yom': pdf_to_add_path = f"Hayom{session_id_str}.pdf"
            elif option_name == 'Shnayim Mikra': pdf_to_add_path = f"Shnayim{session2_id_str}.pdf" # Uses weekly session ID

            if pdf_to_add_path:
                if os.path.exists(pdf_to_add_path):
                    print(f"Adding Chabad.org/local file: {pdf_to_add_path}")
                    doc_out.insert_pdf(fitz.open(pdf_to_add_path))
                else:
                    st.warning(f"PDF for '{option_name}' ({pdf_to_add_path}) not found. Skipping.")
            
        # Warn about Dvar Malchus-only options if DM was not used
        dvar_malchus_exclusive_options = ['Project Likutei Sichos (Hebrew)', 'Maamarim', 'Haftorah', 'Krias Hatorah (includes Haftorah)']
        for opt_item in opt_selected_overall:
            if opt_item in dvar_malchus_exclusive_options:
                st.error(f"'{opt_item}' is typically sourced from Dvar Malchus. Since Dvar Malchus was not used or failed, this item cannot be included.")

    else: # Source IS Dvar Malchus, and dvar_malchus_doc_source is available
        print("Processing with Dvar Malchus as primary source.")
        kriah_haftorah_section_added_flag = False # To ensure "חומש לקריאה בציבור" section is processed once for Kriah/Haftorah
        
        # Iterate through the Dvar Malchus specific section names derived from user's overall selections
        for dvar_section_target_name in optconv_dvar_malchus_sections:
            print(f"Looking for Dvar Malchus section: '{dvar_section_target_name}'")

            # --- Handle Day-Dependent Sections from Dvar Malchus TOC (Chumash, Tanya, Rambam 3-hebrew) ---
            if dvar_section_target_name in ['חומש יומי', 'תניא יומי', 'רמב"ם - שלושה פרקים ליום']:
                for day_hebrew_name in dow_hebrew_selected_days:
                    print(f"  Searching for day: '{day_hebrew_name}' within section '{dvar_section_target_name}'")
                    found_day_section = False
                    for i, top_level_bm in enumerate(dvar_malchus_toc_list):
                        if top_level_bm[1] == dvar_section_target_name: # Matched the main section (e.g., "חומש יומי")
                            # Now search for the sub-level bookmark for the specific day
                            for j, sub_level_bm in enumerate(dvar_malchus_toc_list[i+1:], start=i+1):
                                if sub_level_bm[0] <= top_level_bm[0]: break # Reached next top-level or higher, day not found in this section block
                                if sub_level_bm[0] == top_level_bm[0] + 1 and day_hebrew_name in sub_level_bm[1]:
                                    # Found the specific day's bookmark!
                                    start_page_1idx = sub_level_bm[2] # TOC page numbers are 1-indexed
                                    
                                    # Determine end_page: find next bookmark at the same sub-level or a higher level
                                    end_page_1idx = dvar_malchus_doc_source.page_count # Default to end of doc
                                    for k_next_bm in range(j + 1, len(dvar_malchus_toc_list)):
                                        if dvar_malchus_toc_list[k_next_bm][0] <= sub_level_bm[0]: # Next item at same or higher level
                                            end_page_1idx = dvar_malchus_toc_list[k_next_bm][2]
                                            break
                                    
                                    page_from_0idx = start_page_1idx - 1
                                    page_to_0idx = end_page_1idx - 1 # Tentative end, to be adjusted by offsets

                                    # Original script's specific end-page adjustments:
                                    if dvar_section_target_name == "חומש יומי" and day_hebrew_name == 'שבת קודש':
                                        page_to_0idx = end_page_1idx - 2 #  (end_page_1idx - 1) - 1
                                    elif dvar_section_target_name == "תניא יומי":
                                        page_to_0idx = end_page_1idx - 2 #  (end_page_1idx - 1) - 1
                                    else: # Default for other daily items was often next_item_page - 1
                                          # if end_page_1idx is next_item_page, then (end_page_1idx - 1)
                                          # The original had "toc[j+1][2] - 1" for Rambam, "toc[j+1][2] - 2" for Kriah
                                          # If end_page_1idx = toc[j+1][2], then it's end_page_1idx - 1 for Rambam
                                          # Let's stick to -2 as a general offset from next bookmark if not specified
                                        page_to_0idx = end_page_1idx - 2 
                                        if dvar_section_target_name == 'רמב"ם - שלושה פרקים ליום': # Original had -1 for this
                                            page_to_0idx = end_page_1idx - 1


                                    if page_from_0idx <= page_to_0idx:
                                        adj_start, adj_end = dedupe(dvar_malchus_pages_extracted_set, _legacy_dedupe_pages2_list, _legacy_dedupe_pages3_list, page_from_0idx, page_to_0idx)
                                        if adj_start <= adj_end:
                                            print(f"    Adding Dvar Malchus: '{dvar_section_target_name} - {day_hebrew_name}', pages {adj_start+1}-{adj_end+1}")
                                            doc_out.insert_pdf(dvar_malchus_doc_source, from_page=adj_start, to_page=adj_end)
                                        else: st.info(f"Section '{dvar_section_target_name} - {day_hebrew_name}' resulted in an invalid page range ({adj_start}-{adj_end}) after deduplication. Skipping.")
                                    else: st.info(f"Section '{dvar_section_target_name} - {day_hebrew_name}' initial page range ({page_from_0idx}-{page_to_0idx}) invalid. Skipping.")
                                    found_day_section = True
                                    break # Found day, move to next Hebrew day or Dvar section
                            if found_day_section: break # Processed this top-level section for the current day
                # End of day loop for this Dvar Malchus daily section
            
            # --- Handle Non-Day-Dependent Sections from Dvar Malchus (Sichos, Maamarim, Kriah/Haftorah) ---
            elif dvar_section_target_name in ['לקוטי שיחות', 'מאמרים', 'חומש לקריאה בציבור']:
                for i, item_bm in enumerate(dvar_malchus_toc_list):
                    # Match bookmark title for these sections
                    section_found_in_toc = False
                    if dvar_section_target_name == 'לקוטי שיחות' and 'לקוטי שיחות' in item_bm[1]: section_found_in_toc = True
                    elif dvar_section_target_name == 'מאמרים' and ('מאמר' in item_bm[1] or 'מאמרים' in item_bm[1]): section_found_in_toc = True
                    elif dvar_section_target_name == 'חומש לקריאה בציבור' and item_bm[1] == 'חומש לקריאה בציבור': section_found_in_toc = True
                    
                    if section_found_in_toc:
                        start_page_1idx = item_bm[2]
                        # End page is determined by the next top-level bookmark, or end of document
                        next_top_level_bm_page_1idx = find_next_top_level_bookmark(dvar_malchus_toc_list, i)
                        
                        # page_to_0idx calculation for these sections
                        page_from_0idx = start_page_1idx - 1
                        
                        if next_top_level_bm_page_1idx is not None:
                            # Original for Sichos/Maamarim was `find_next_top_level_bookmark(toc, i)` (which is page P of next top bm)
                            # then `to_page=P-2`. So, (next_top_level_bm_page_1idx - 1) - 1 = next_top_level_bm_page_1idx - 2 (0-indexed)
                            page_to_0idx = next_top_level_bm_page_1idx - 2 
                        else: # No next top-level bookmark, go to end of document
                            page_to_0idx = dvar_malchus_doc_source.page_count - 1

                        # For Kriah, original was `toc[i+1][2] - 3`. This is next bookmark (any level) page - 3 (0-indexed)
                        if dvar_section_target_name == 'חומש לקריאה בציבור' and (i + 1 < len(dvar_malchus_toc_list)) and dvar_malchus_toc_list[i+1][2] is not None:
                             page_to_0idx = dvar_malchus_toc_list[i+1][2] - 1 - 2 # (page of next bm -1 for 0-index) -2 for offset = page of next bm -3 (0-indexed)

                        if page_from_0idx <= page_to_0idx:
                            if dvar_section_target_name == 'חומש לקריאה בציבור': # Special handling for Kriah/Haftorah
                                if kriah_haftorah_section_added_flag: continue # Already processed this combined section
                                kriah_haftorah_section_added_flag = True

                                kriah_start_0idx, kriah_end_0idx = page_from_0idx, page_to_0idx
                                
                                if "Krias Hatorah (includes Haftorah)" in opt_selected_overall:
                                    print(f"    Adding Dvar Malchus: Krias Hatorah (full section), pages {kriah_start_0idx+1}-{kriah_end_0idx+1}")
                                    doc_out.insert_pdf(dvar_malchus_doc_source, from_page=kriah_start_0idx, to_page=kriah_end_0idx)
                                elif 'Haftorah' in opt_selected_overall: # Only Haftorah part
                                    haftorah_actual_start_0idx = -1
                                    # Scan pages in the "חומש לקריאה בציבור" section for Haftorah start
                                    for p_num in range(kriah_start_0idx, kriah_end_0idx + 1):
                                        # Ensure p_num is within valid page range for the document
                                        if p_num < dvar_malchus_doc_source.page_count:
                                            page_text = dvar_malchus_doc_source.load_page(p_num).get_text("text", sort=True)
                                            if "ברכת הפטורה" in page_text or "xtd enk dxhtdd renyl" in page_text: # Heuristic
                                                haftorah_actual_start_0idx = p_num
                                                break
                                        else: # p_num out of bounds
                                            st.warning(f"Attempted to scan page {p_num+1} for Haftorah, but doc only has {dvar_malchus_doc_source.page_count} pages.")
                                            break 
                                            
                                    if haftorah_actual_start_0idx != -1 and haftorah_actual_start_0idx <= kriah_end_0idx:
                                        print(f"    Adding Dvar Malchus: Haftorah only, pages {haftorah_actual_start_0idx+1}-{kriah_end_0idx+1}")
                                        doc_out.insert_pdf(dvar_malchus_doc_source, from_page=haftorah_actual_start_0idx, to_page=kriah_end_0idx)
                                    else: st.warning("Haftorah start not found within 'Krias Hatorah' section. Haftorah not added.")
                            else: # For Sichos, Maamarim
                                print(f"    Adding Dvar Malchus: '{dvar_section_target_name}', pages {page_from_0idx+1}-{page_to_0idx+1}")
                                doc_out.insert_pdf(dvar_malchus_doc_source, from_page=page_from_0idx, to_page=page_to_0idx)
                        else: st.info(f"Section '{dvar_section_target_name}' resulted in an invalid page range ({page_from_0idx}-{page_to_0idx}). Skipping.")
                        break # Found and processed this non-daily section, move to next dvar_section_target_name
            
            # --- Handle Separately Downloaded Files (Rambam-non-3Hebrew, Hayom Yom, Shnayim Mikra) ---
            # These are added even if Dvar Malchus is primary, as they come from other sources.
            # Their presence in `optconv_dvar_malchus_sections` signals they were selected by the user.
            pdf_to_add_path_extra = None
            if 'Rambam' in dvar_section_target_name and dvar_section_target_name != 'רמב"ם - שלושה פרקים ליום':
                pdf_to_add_path_extra = f"Rambam{session_id_str}.pdf" # Assumes these are always from Chabad.org session
            elif dvar_section_target_name == 'Hayom Yom':
                pdf_to_add_path_extra = f"Hayom{session_id_str}.pdf"
            elif dvar_section_target_name == 'Shnayim Mikra':
                pdf_to_add_path_extra = f"Shnayim{session2_id_str}.pdf"

            if pdf_to_add_path_extra:
                if os.path.exists(pdf_to_add_path_extra):
                    print(f"Adding separately sourced file: {pdf_to_add_path_extra}")
                    doc_out.insert_pdf(fitz.open(pdf_to_add_path_extra))
                else:
                    st.warning(f"PDF for '{dvar_section_target_name}' ({pdf_to_add_path_extra}) was expected but not found. Skipping.")
        # End of loop for Dvar Malchus sections
        
    # --- Finalize and Save ---
    if dvar_malchus_doc_source:
        dvar_malchus_doc_source.close() # Close the Dvar Malchus source PDF

    if doc_out.page_count > 0:
        doc_out.save(output_filename)
        print(f"Output PDF '{output_filename}' saved with {doc_out.page_count} pages.")
    else:
        st.error("No content was added to the PDF. Output file not created. Please check selections and logs.")
    doc_out.close()


# --- Streamlit UI and Main Logic ---
@st.cache_data(ttl="12h") # Cache for 12 hours
def dateset_for_weekly_files():
    """
    Provides a cached datetime object. This is used to generate filenames for
    Dvar Malchus and Shnayim Mikra, allowing them to be cached across user sessions
    if downloaded within the TTL window.
    """
    now = dt.now()
    print(f"dateset_for_weekly_files() called or cache retrieved. Cached time: {now}")
    return now

# --- Main App Form ---
with st.form(key="dvarform", clear_on_submit=False): # Clear on submit is False to keep selections
    st.title("Dvar Creator 📚 (BETA)")
    st.info("Consolidate your weekly Chitas, Rambam, and other study materials into a single PDF.")
    markdownlit.mdlit("""Sources: @(**[blue]Dvar Malchus[/blue]**)(https://dvarmalchus.org/)
    and @(🔥)(**[orange]Chabad.org[/orange]**)(https://www.chabad.org/dailystudy/). Please support the original publishers.
    """)
    
    # session2_dt_obj: For weekly files (Dvar Malchus, Shnayim) - uses cached datetime
    session2_dt_obj = dateset_for_weekly_files() 
    
    # Determine current Parsha for display and Shnayim Mikra
    today_date_str_for_parsha = date.today().strftime('%Y, %m, %d') 
    current_parsha_name = parshaget(today_date_str_for_parsha) # parshaget also calls st.write
    
    # --- User Selections ---
    selected_week_days_en = pills(f"Days of the week (Current Parsha: {current_parsha_name}):", 
                                  options=['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Shabbos'], 
                                  multiselect=True, clearable=True, index=None)
    
    st.write("**Select materials to print:**")
    selected_basics = pills('Basics (Chumash, Tanya, Hayom Yom):', 
                            options=['Chumash', 'Tanya', 'Hayom Yom'], 
                            multiselect=True, clearable=True, index=None)
    selected_rambam_opts = pills('Rambam (Chabad.org versions, or Hebrew from Dvar Malchus):', 
                                 options=['Rambam (3)-Hebrew',    # Can come from Dvar Malchus or Chabad.org
                                          'Rambam (3)-Bilingual', # Chabad.org
                                          'Rambam (3)-English',   # Chabad.org
                                          'Rambam (1)-Hebrew',    # Chabad.org
                                          'Rambam (1)-Bilingual', # Chabad.org
                                          'Rambam (1)-English'],  # Chabad.org
                                 multiselect=True, clearable=True, index=None)
    selected_extras = pills('Extras (Dvar Malchus for Sichos/Maamarim/Kriah; GitHub for Shnayim Mikra):', 
                            options=['Project Likutei Sichos (Hebrew)', # Dvar Malchus
                                     'Maamarim',                         # Dvar Malchus
                                     'Krias Hatorah (includes Haftorah)',# Dvar Malchus
                                     'Haftorah',                         # Dvar Malchus (subset of Kriah)
                                     'Shnayim Mikra'],                   # GitHub
                            multiselect=True, clearable=True, index=None)
    
    source_try_dvar_malchus_first = stt.st_toggle_switch(
        label='Prefer Dvar Malchus? (Green=Yes). If off or fails for an item, Chabad.org will be used as fallback.', 
        default_value=True, label_after=True, 
        inactive_color='#D3D3D3', active_color='#4CAF50', track_color='#90EE90'
    )  
    with st.expander("Advanced Options (for Chabad.org PDFs & Dvar Malchus Cover)"):
        include_dm_cover = st.checkbox('Include Dvar Malchus cover page? (Only if Dvar Malchus is used)', value=False)
        # Scale values are floats (e.g., 1.0 for 100%)
        pdf_scale_chumash_tanya = st.slider('Scale: Chumash/Tanya (Chabad.org)', 0.3, 1.5, 1.0, 0.05, format="%.2f")
        pdf_scale_rambam = st.slider('Scale: Rambam (Chabad.org)', 0.3, 1.5, 0.7, 0.05, format="%.2f") # Defaulted to 0.7 (70%)
        pdf_scale_hayomyom = st.slider('Scale: Hayom Yom (Chabad.org)', 0.3, 1.5, 0.9, 0.05, format="%.2f") # Defaulted to 0.9 (90%)
        
    submit_button = st.form_submit_button(label="Generate Custom PDF 🚀")

# --- Actions on Form Submit ---
if submit_button:
    generation_start_time = time.time()

    # session_dt_obj_for_run: For files unique to this specific generation run (Chabad.org daily, final output PDF)
    # Uses st.session_state to persist across reruns *within the same interaction* if form is resubmitted.
    # This is different from session2_dt_obj which is for weekly file caching across broader time.
    if 'session_dt_obj_for_run' not in st.session_state:
        st.session_state['session_dt_obj_for_run'] = dt.now()
    session_dt_obj_for_run = st.session_state['session_dt_obj_for_run']

    # Combine all selected options into one list
    all_selected_opts = []
    if selected_basics: all_selected_opts.extend(selected_basics)
    if selected_rambam_opts: all_selected_opts.extend(selected_rambam_opts)
    if selected_extras: all_selected_opts.extend(selected_extras)

    if not all_selected_opts:
        st.error("No materials selected. Please choose at least one item.")
        st.stop()

    # Define canonical order for processing and output consistency
    canonical_opt_order = [
        'Chumash', 'Tanya', 'Hayom Yom', # Basics
        'Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', # Rambam 3-ch
        'Rambam (1)-Hebrew', 'Rambam (1)-Bilingual', 'Rambam (1)-English', # Rambam 1-ch
        'Project Likutei Sichos (Hebrew)', 'Maamarim', # Dvar Malchus extras
        'Krias Hatorah (includes Haftorah)', 'Haftorah', # Dvar Malchus Kriah/Haftorah
        'Shnayim Mikra' # GitHub extra
    ]
    # Sort selected options according to the canonical order
    all_selected_opts_sorted = sorted(
        all_selected_opts, 
        key=lambda x: canonical_opt_order.index(x) if x in canonical_opt_order else float('inf')
    )

    # --- Prepare Day Lists and Date Strings ---
    day_order_en = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Shabbos']
    # Ensure selected_week_days_en is a list, even if pills returns None
    actual_selected_week_days_en = sorted(
        selected_week_days_en if selected_week_days_en else [], 
        key=lambda x: day_order_en.index(x) if x in day_order_en else float('inf')
    )
    
    hebrew_day_names_for_dvar = [] # For Dvar Malchus day matching
    chabad_url_date_params = []    # For Chabad.org URL date params (M/D/Y)

    if actual_selected_week_days_en:
        daytoheb(actual_selected_week_days_en, hebrew_day_names_for_dvar)
        daytorambam(actual_selected_week_days_en, chabad_url_date_params)

    # Check if days are selected for day-dependent materials
    day_dependent_material_options = ['Chumash', 'Tanya', 'Hayom Yom'] + [r for r in canonical_opt_order if 'Rambam' in r]
    if not actual_selected_week_days_en and any(opt_name in all_selected_opts_sorted for opt_name in day_dependent_material_options):
        st.error("Day-dependent materials (Chumash, Tanya, Rambam, Hayom Yom) require at least one day of the week to be selected.")
        st.stop()

    # Convert selected English options to Dvar Malchus specific names/groupings for TOC parsing
    optconv_dvar_malchus_target_sections = []
    opttouse(all_selected_opts_sorted, optconv_dvar_malchus_target_sections)

    # --- Determine Effective Source and Download Weekly Files if Needed ---
    # Will Dvar Malchus be attempted as the primary source?
    effective_use_dvar_malchus = source_try_dvar_malchus_first
    
    # Options that can potentially come from Dvar Malchus
    options_potentially_from_dvar = [
        'Chumash', 'Tanya', 'Rambam (3)-Hebrew', # Daily study
        'Project Likutei Sichos (Hebrew)', 'Maamarim', 
        'Krias Hatorah (includes Haftorah)', 'Haftorah'  # Weekly sections
    ]
    
    # If user prefers Dvar Malchus AND has selected options that could come from it:
    if effective_use_dvar_malchus and any(opt_name in all_selected_opts_sorted for opt_name in options_potentially_from_dvar):
        dvar_malchus_target_pdf_path = f"dvar{format_dt_for_filename(session2_dt_obj)}.pdf"
        if not os.path.exists(dvar_malchus_target_pdf_path):
            with st.spinner('Attempting Dvar Malchus download... (this can take a moment)'):
                if not dvarget(session2_dt_obj): # dvarget returns True on success
                    st.warning("Failed to download Dvar Malchus. Will use Chabad.org as fallback for all applicable content.")
                    effective_use_dvar_malchus = False # Fallback to Chabad.org
        else:
            print(f"Using existing (cached) Dvar Malchus PDF: {dvar_malchus_target_pdf_path}")
    elif effective_use_dvar_malchus:
        # User chose Dvar Malchus, but no selected options are typically from it.
        # No Dvar Malchus download needed in this specific case.
        print("Dvar Malchus preferred, but no selected options require it. Proceeding with Chabad.org/other sources.")
        effective_use_dvar_malchus = False # Effectively, DM won't be primary source of content.

    # Determine if Dvar Malchus cover page should be included
    effective_include_dm_cover = include_dm_cover and effective_use_dvar_malchus

    # --- Download Chabad.org Daily Content (if not covered by Dvar Malchus or DM failed) ---
    with st.spinner('Gathering materials from Chabad.org as needed...'):
        # Chumash and Tanya
        if any(opt_name in all_selected_opts_sorted for opt_name in ['Chumash', 'Tanya']):
            # Get from Chabad.org if (DM not preferred) OR (DM preferred but failed) OR (DM preferred but these items are not DM-exclusive)
            # Simplified: if DM is not effectively used for these, get from Chabad.
            if not effective_use_dvar_malchus or not all(item in options_potentially_from_dvar for item in ['Chumash', 'Tanya']):
                 chabadget(chabad_url_date_params, all_selected_opts_sorted, session_dt_obj_for_run, pdf_scale_chumash_tanya)

        # Rambam versions from Chabad.org
        # Includes: Bilingual, English, Rambam (1)-Hebrew.
        # Also includes Rambam (3)-Hebrew if Dvar Malchus is not effectively used OR if this specific option wasn't found in DM.
        rambam_opts_for_chabad_dl = [r for r in all_selected_opts_sorted if 'Rambam' in r and 
                                     (r != 'Rambam (3)-Hebrew' or not effective_use_dvar_malchus)]
        if rambam_opts_for_chabad_dl:
            # rambamenglish handles which specific Rambam variant to download based on opt_selected_overall
            rambamenglish(chabad_url_date_params, session_dt_obj_for_run, all_selected_opts_sorted, pdf_scale_rambam)
        
        if 'Hayom Yom' in all_selected_opts_sorted:
            hayomyom(chabad_url_date_params, session_dt_obj_for_run, pdf_scale_hayomyom)

    # --- Download Shnayim Mikra (from GitHub) ---
    if 'Shnayim Mikra' in all_selected_opts_sorted:
        with st.spinner(f"Getting Shnayim Mikra for Parshas {current_parsha_name}..."):
            shnayimget(session2_dt_obj, current_parsha_name) 

    # --- Compile the Final PDF ---
    with st.spinner('Compiling your custom PDF... Please wait.'):
        dynamicmake(
            hebrew_day_names_for_dvar, 
            optconv_dvar_malchus_target_sections, 
            all_selected_opts_sorted, 
            effective_use_dvar_malchus, 
            session_dt_obj_for_run,        # For this run's unique files
            session2_dt_obj,               # For weekly cached files (DM, Shnayim)
            effective_include_dm_cover
        )

    # --- Display Download Button for Final PDF ---
    final_output_pdf_path = f"output_dynamic{format_dt_for_filename(session_dt_obj_for_run)}.pdf"
    if os.path.exists(final_output_pdf_path) and os.path.getsize(final_output_pdf_path) > 100: # Basic check for non-empty PDF
        st.success(f"🎉 Your custom PDF is ready! (Generation time: {time.time() - generation_start_time:.2f} seconds)")
        st.balloons()
        with open(final_output_pdf_path, "rb") as f_pdf:
            st.download_button(
                label="Download Your Custom PDF ⬇️", 
                data=f_pdf, 
                file_name="My_Custom_Dvar_Chitas.pdf", # User-friendly download name
                mime="application/pdf"
            )
    else:
        st.error("Failed to create the PDF, or the PDF is empty. Please review any warnings above and try again.")


    # --- File Cleanup Logic ---
    # Deletes older temporary and output files to save space.
    # Uses precise filenames with session IDs for current files to avoid deleting them.
    current_time_for_cleanup = dt.now()
    # ID for files unique to this run (Chabad.org daily, final output)
    current_run_session_id_str = format_dt_for_filename(session_dt_obj_for_run)
    # ID for weekly cached files (Dvar Malchus, Shnayim Mikra)
    current_weekly_session_id_str = format_dt_for_filename(session2_dt_obj)

    # Pattern: (age_limit_timedelta, name_of_current_file_to_preserve_if_any)
    cleanup_patterns_map = {
        "Rambam*.pdf": (timedelta(minutes=20), f"Rambam{current_run_session_id_str}.pdf"),
        "Chumash*.pdf": (timedelta(minutes=20), f"Chumash{current_run_session_id_str}.pdf"),
        "Tanya*.pdf": (timedelta(minutes=20), f"Tanya{current_run_session_id_str}.pdf"),
        "Hayom*.pdf": (timedelta(minutes=20), f"Hayom{current_run_session_id_str}.pdf"),
        "dvar*.pdf": (timedelta(hours=14), f"dvar{current_weekly_session_id_str}.pdf"),
        "Shnayim*.pdf": (timedelta(hours=14), f"Shnayim{current_weekly_session_id_str}.pdf"),
        "output_dynamic*.pdf": (timedelta(minutes=20), f"output_dynamic{current_run_session_id_str}.pdf"),
        "temp_*.pdf": (timedelta(minutes=10), None) # Temp files for merging, None means don't preserve any current one.
    }

    print("\n--- Starting File Cleanup ---")
    for file_pattern, (age_limit, current_file_to_preserve) in cleanup_patterns_map.items():
        for old_file_path in glob.glob(file_pattern):
            old_file_basename = os.path.basename(old_file_path)
            
            if current_file_to_preserve and old_file_basename == current_file_to_preserve:
                continue # Skip deleting the file generated in the current session

            try:
                # Attempt to parse timestamp from filename (assumes YYYYMMDD_HHMMSS_ffffff format)
                file_prefix = file_pattern.split("*")[0]
                timestamp_str_from_filename = old_file_basename.lstrip(file_prefix).rstrip(".pdf")
                
                file_dt_object = dt.strptime(timestamp_str_from_filename, "%Y%m%d_%H%M%S_%f")
                if current_time_for_cleanup - file_dt_object > age_limit:
                    print(f"Cleaning up old file (by filename timestamp): {old_file_path}")
                    os.remove(old_file_path)
            except ValueError: # Timestamp parsing failed (e.g., different format, or not a timestamped file)
                # Fallback: Check file modification time for temp files or unparsable names
                try:
                    file_mod_time = dt.fromtimestamp(os.path.getmtime(old_file_path))
                    if current_time_for_cleanup - file_mod_time > age_limit:
                        print(f"Cleaning up old file (by modification time): {old_file_path}")
                        os.remove(old_file_path)
                except OSError as e_os:
                    print(f"Skipping cleanup for {old_file_path} due to OS error: {e_os}") # File might have been deleted
            except OSError as e_os_outer:
                print(f"Skipping cleanup for {old_file_path} due to OS error during initial check: {e_os_outer}")
    print("--- File Cleanup Finished ---\n")

# --- Static Content Below Form (Changelog, Clear Cache Button) ---
markdownlit.mdlit("---") # Visual separator
markdownlit.mdlit("Found a bug? Have a feature request? [📧 Email Me!](mailto:mkievman@outlook.com)")

if not submit_button: # Show changelog only if form hasn't been submitted in this interaction
    with st.expander("**Changelog & Updates:**"):
        markdownlit.mdlit("""
        **Latest (Refactor Round 2 - Syntax Fix):**
        *   Corrected Python syntax error in `dvarget` function (try/except block).
        *   Improved Selenium WebDriver reuse for Chabad.org daily sections (faster fetching).
        *   Enhanced download logic for Dvar Malchus and Shnayim Mikra with better verification.
        *   Refined PDF generation logic in `dynamicmake` for clarity.
        *   Added more comments and print statements for easier debugging.
        *   Streamlined `devcontainer.json` and `requirements.txt`.
        *   UI tweaks for clarity (slider formats, button labels).

        **Previous (Refactor Round 1):**
        *   Robust Selenium WebDriver initialization with fallback.
        *   Standardized filename formatting using datetime.
        *   Improved PDF download detection in `dvarget` and `shnayimget`.
        *   Clearer separation of session IDs for run-specific vs. weekly cached files.
        *   Corrected file cleanup logic to use new filename format.

        **Original (1-17-24):**
        *   **[FIX]** Updated location of Dvar Malchus download button (website structure dependent).
        *   **(7-17-23):** Faster Dvar Malchus/Shnayim Mikra on reruns; Maamarim/Sichos fixes.
        """)

# Option to clear the cached datetime for weekly files (Dvar Malchus, Shnayim Mikra)
# This button appears after a PDF has been generated (i.e., submit_button was True)
# or if the form was submitted and then something caused a rerun where submit_button is now False.
# So, more robustly, show if the session_dt_obj_for_run exists (meaning a submit happened).
if st.session_state.get('session_dt_obj_for_run'): # True if PDF generation was attempted
    # Check if the output PDF from that run actually exists before showing the button
    final_output_pdf_path_for_cache_button = f"output_dynamic{format_dt_for_filename(st.session_state['session_dt_obj_for_run'])}.pdf"
    if os.path.exists(final_output_pdf_path_for_cache_button): 
        with st.expander("⚠️ Advanced: Troubleshooting Old Weekly Materials"):
            st.write("""
            If Dvar Malchus or Shnayim Mikra seem to be from a previous week despite a new one being available,
            their download might be cached. Click below to clear this cache.
            The app will then try to download them fresh on the next PDF generation.
            """)
            if st.button("Clear Cache for Weekly Files (Dvar Malchus/Shnayim)", key="clear_weekly_cache_btn"):
                dateset_for_weekly_files.clear() # Clears the @st.cache_data
                st.success("Weekly file cache cleared! Next generation will attempt fresh downloads for Dvar Malchus & Shnayim Mikra.")
                # No automatic rerun here, user will initiate next PDF generation.