from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from selenium.webdriver.support import expected_conditions as EC  # type: ignore
from selenium.common.exceptions import TimeoutException  # Added this import
import os
import time
import fitz as fitz  # type: ignore
from base64 import b64decode
from dateutil.relativedelta import relativedelta  # type: ignore
from datetime import date  # type: ignore
from datetime import datetime as dt  # type: ignore
from datetime import timedelta  # type: ignore
import streamlit as st  # type: ignore
import markdownlit
from markdownlit import mdlit as mdlit
import streamlit_toggle as stt
from streamlit_pills_multiselect import pills
import PyPDF2  # type: ignore
from PyPDF2 import PdfMerger  # type: ignore
import glob
import json
from pyluach import parshios, dates

st.set_page_config(page_title="Dvar Creator (BETA)", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
options.add_experimental_option('prefs', {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
})
chrome_driver_path = "/usr/bin/chromedriver"
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

def dvarget(session2):  # attempts to retrieve dvar malchus pdf
    print("Dvarget Running")
    driver = webdriver.Chrome(options=options)
    print("Driver Opened")
    driver.get("https://dvarmalchus.org")
    print("Dvar Malchus Opened")
    xpaths = [
        "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div/div/div/a/span/span[2]",
        "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div",
        "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div/div/div",
        '/html/body/div[1]/section[2]/div[3]/div/div/div[3]/div/div/a',
        '/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div[1]/div/div/a',
        "/html/body/div[1]/section[2]/div[3]/div/div/div[4]/div/div/section/section/div/div/div/div[2]/div/div/a",
        '/html/body/div[1]/section[9]/div/div/div/div[3]/div/div/div/div[1]/div/section/div/div/div/section/div/div/div/div/div/div/a',
        '/html/body/div[1]/section[9]/div/div/div/div[3]/div/div/div/div[2]/div/section/div/div/div/section/div/div/div/div/div/div/a'
    ]
    for each in xpaths:
        try:
            link_text = driver.find_element(By.XPATH, f"{each}/span/span[2]").text
            if link_text == "להורדת החוברת השבועית":
                print(f"clicking {each}")
                url = driver.find_element(By.XPATH, each).get_attribute("href")
                driver.get(url)
                print(f"URL: {url}")
                break
            else:
                if link_text != "להורדת החוברת השבועית - חו״ל":
                    print("skipping " + each)
                    continue
                elif link_text == "להורדת החוברת השבועית - חו״ל":
                    print(f"clicking alternate {each}")
                    url = driver.find_element(By.XPATH, each).get_attribute("href")
                    print(url)
                    driver.get(url)
                    break
        except:
            continue

    driver.save_screenshot("dvar.png")
    print("waiting")
    time.sleep(10)
    os.remove("dvar.png")

    files = os.listdir()
    sessionyear = "2023"  # set the session variable to "2023"
    for file in files:
        if file.endswith(".pdf") and sessionyear not in file:  # check if the file is a pdf and does not contain the session variable
            print("renaming " + file)
            os.rename(os.path.join("", file), os.path.join("", f"dvar{session2}.pdf"))

    driver.quit()

def chabadget(dor, opt, session):  # retrieves chumash and tanya from chabad.org
    pdf_options = {
        'scale': scale,
        'margin-top': '0.1in',
        'margin-right': '0.1in',
        'margin-bottom': '0.1in',
        'margin-left': '0.1in',
    }
    if not os.path.exists(f"Chumash{session}.pdf"):
        merger = PdfMerger()
        if 'Chumash' in opt:
            for i in dor:
                driver = webdriver.Chrome(options=options)
                driver.get(f"https://www.chabad.org/dailystudy/torahreading.asp?tdate={i}#lt=he")
                wait = WebDriverWait(driver, 10)
                element = wait.until(EC.presence_of_element_located((By.ID, "content")))
                pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
                with open(f"temp{session}.pdf", "ab") as f:
                    f.write(b64decode(pdf["data"]))
                f.close()
                driver.quit()
                merger.append(f"temp{session}.pdf")

            merger.write(f"Chumash{session}.pdf")
            merger.close()
            if os.path.exists(f"temp{session}.pdf"):
                os.remove(f"temp{session}.pdf")
    if not os.path.exists(f"Tanya{session}.pdf"):
        merger2 = PdfMerger()
        if 'Tanya' in opt:
            for i in dor:
                driver = webdriver.Chrome(options=options)
                driver.get(f"https://www.chabad.org/dailystudy/tanya.asp?tdate={i}&commentary=false#lt=he")
                wait = WebDriverWait(driver, 10)
                element = wait.until(EC.presence_of_element_located((By.ID, "content")))
                time.sleep(3)
                pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
                with open(f"temp{session}.pdf", "ab") as f:
                    f.write(b64decode(pdf["data"]))
                f.close()
                driver.quit()
                merger2.append(f"temp{session}.pdf")

            merger2.write(f"Tanya{session}.pdf")
            merger2.close()
            if os.path.exists(f"temp{session}.pdf"):
                os.remove(f"temp{session}.pdf")

def rambamenglish(dor, session, opt):  # retrieves all rambam versions from chabad.org
    pdf_options = {
        'scale': scale2,
        'margin-top': '0.1in',
        'margin-right': '0.1in',
        'margin-bottom': '0.1in',
        'margin-left': '0.1in',
    }
    merger = PdfMerger()
    if not os.path.exists(f"Rambam{session}.pdf"):
        for i in dor:
            driver = webdriver.Chrome(options=options)
            lang = ""
            chapters = ""
            if "Rambam (3)-Bilingual" in opt:
                lang = "both"
                chapters = "3"
            elif "Rambam (3)-Hebrew" in opt:
                lang = "he"
                chapters = "3"
            elif "Rambam (3)-English" in opt:
                lang = "primary"
                chapters = "3"
            elif "Rambam (1)-Bilingual" in opt:
                lang = "both"
                chapters = "1"
            elif "Rambam (1)-Hebrew" in opt:
                lang = "he"
                chapters = "1"
            elif "Rambam (1)-English" in opt:
                lang = "primary"
                chapters = "1"
            url = f"https://www.chabad.org/dailystudy/rambam.asp?rambamchapters={chapters}&tdate={i}#lt={lang}"
            print(f"Accessing URL: {url}")
            driver.get(url)
            wait = WebDriverWait(driver, 30)  # Increased timeout to 30 seconds
            try:
                wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
            except TimeoutException as e:
                print("Timeout occurred. Saving debug info.")
                driver.save_screenshot(f"error_screenshot_{session}.png")
                with open(f"error_page_source_{session}.html", "w") as f:
                    f.write(driver.page_source)
                logs = driver.get_log("browser")
                for log in logs:
                    print(f"Browser log: {log}")
                raise e
            finally:
                with open(f"temp{session}.pdf", "ab") as f:
                    f.write(b64decode(pdf["data"]))
                driver.quit()

            merger.append(f"temp{session}.pdf")

        merger.write(f"Rambam{session}.pdf")
        merger.close()
        if os.path.exists(f"temp{session}.pdf"):
            os.remove(f"temp{session}.pdf")

def hayomyom(dor, session):  # gets hayom yom from chabad.org
    pdf_options = {
        'scale': scale3,
        'margin-top': '0.1in',
        'margin-right': '0.1in',
        'margin-bottom': '0.1in',
        'margin-left': '0.1in',
    }
    merger3 = PdfMerger()
    if not os.path.exists(f"Hayom{session}.pdf"):
        for i in dor:
            driver = webdriver.Chrome(options=options)
            driver.get(f"https://www.chabad.org/dailystudy/hayomyom.asp?tdate={i}")
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.ID, "content")))
            pdf = driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
            with open(f"temp{session}.pdf", "ab") as f:
                f.write(b64decode(pdf["data"]))
            f.close()
            driver.quit()

            merger3.append(f"temp{session}.pdf")

        merger3.write(f"Hayom{session}.pdf")
        merger3.close()
        if os.path.exists(f"temp{session}.pdf"):
            os.remove(f"temp{session}.pdf")

def parshaget(date1):  # get parsha from date for shnayim mikra
    year, date, month = date1.split(", ")
    year, date, month = int(year), int(date), int(month)
    parsha = parshios.getparsha_string(dates.GregorianDate(year, date, month), israel=False, hebrew=True)
    st.write(f"This week's parsha is {parsha}.")
    return parsha

def shnayimget(session2, parsha):  # get shnayim mikra from github repo
    pdf_options = {}
    parsha2 = parsha.split(" ")
    parshaurl = []
    filename = []
    for parsha in parsha2:
        if parshaurl != []:
            parshaurl.append("%20")
        parshaurl.append(parsha)
        filename.append(parsha)
        parshaurl2 = "".join(parshaurl)
        filename2 = " ".join(filename)
    print(parshaurl2)
    if not os.path.exists(f"Shnayim{session2}.pdf"):
        if 'Shnayim Mikra' in opt:
            driver = webdriver.Chrome(options=options)
            driver.get(f"https://github.com/emkay5771/shnayimfiles/blob/master/{parshaurl2}.pdf?raw=true")
            wait = WebDriverWait(driver, 10)
            time.sleep(2)
            driver.quit()
            if os.path.exists(f"{filename2}.pdf"):
                print(f"file exists {filename2}")
                os.rename(f"{filename2}.pdf", f"Shnayim{session2}.pdf")

def daytoheb(week, dow):  # converts day of week from week in streamlit to hebrew date
    for i in week:
        if i == 'Sunday':
            dow.append('יום ראשון')
        elif i == 'Monday':
            dow.append('יום שני')
        elif i == 'Tuesday':
            dow.append('יום שלישי')
        elif i == 'Wednesday':
            dow.append('יום רביעי')
        elif i == 'Thursday':
            dow.append('יום חמישי')
        elif i == 'Friday':
            dow.append('יום שישי')
        elif i == 'Shabbos':
            dow.append('שבת קודש')
    return dow

def opttouse(opt, optconv):  # sorts through options from opt to optconv
    for i in opt:
        if i == 'Chumash':
            optconv.append('חומש יומי')
        elif i == 'Tanya':
            optconv.append('תניא יומי')
        elif i == 'Rambam (3)-Hebrew':
            optconv.append('רמב"ם - שלושה פרקים ליום')
        elif i == 'Haftorah' or i == 'Krias Hatorah (includes Haftorah)':
            print("appended haftorah")
            optconv.append('חומש לקריאה בציבור')
        elif i == 'Project Likutei Sichos (Hebrew)':
            optconv.append('לקוטי שיחות')
        elif i == 'Maamarim':
            optconv.append('מאמרים')
        elif i == 'Shnayim Mikra':
            optconv.append('Shnayim Mikra')
        elif 'Rambam' in i or 'Hayom Yom' in i:
            optconv.append(i)
    return optconv

def daytorambam(week, dor):  # converts day of week to date format for chabad.org
    today = date.today()
    day_to_n = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Shabbos': 5, 'Sunday': 6}
    for i in week:
        n = day_to_n[i]
        print(n)
        linkappend = today + relativedelta(weekday=n)
        y, m, d = str(linkappend).split("-")
        dor.append(f'{m}%2F{d}%2F{y}')
    return dor

def find_next_top_level_bookmark(toc, current_index):
    for i in range(current_index + 1, len(toc)):
        if toc[i][0] == 1:
            return toc[i][2] - 2
    return None

def dedupe(pages, pages2, pages3, start_page, end_page):  # dedupes pages when appending
    pages2.append(start_page)
    pages2.append(end_page)
    if start_page in pages:
        start_page = start_page + 1
        pages.append(start_page)
        pages3.append(start_page)
    if end_page in pages:
        end_page = end_page - 1
        pages.append(end_page)
        pages3.append(end_page)
    if start_page not in pages:
        pages.append(start_page)
    if end_page not in pages:
        pages.append(end_page)
    return start_page, end_page

def dynamicmake(dow, optconv, opt, source, session):  # compiles pdf after collecting files
    output_dir = ""
    toc = []
    doc_out = fitz.open()
    pages = []
    pages2 = []
    pages3 = []
    kriahattatch = False
    if source:
        try:
            doc = fitz.open(f"dvar{session2}.pdf")
            toc = doc.get_toc()
            if cover:
                doc_out.insert_pdf(doc, from_page=0, to_page=0)
        except:
            st.write("Something went wrong with Dvar Malchus. Attempting to use Chabad.org.")
            print(opt)
            if all(option not in chabadoptions for option in opt) and any(option in opt for option in ['Project Likutei Sichos', 'Maamarim', 'Haftorah']):
                st.error("Project Likutei Sichos, the Haftorah, and Maamarim are not available from Chabad.org. Please try again.")
                st.stop()
            source = False
            chabadget(dor, opt, session)

    if not source:
        print("Chabad.org")
        print(opt)
        for option in opt:
            if option == 'Chumash':
                doc_out.insert_pdf(fitz.open(f"Chumash{session}.pdf"))
            elif option == 'Tanya':
                doc_out.insert_pdf(fitz.open(f"Tanya{session}.pdf"))
            elif 'Rambam' in option:
                doc_out.insert_pdf(fitz.open(f"Rambam{session}.pdf"))
            elif option == 'Hayom Yom':
                doc_out.insert_pdf(fitz.open(f"Hayom{session}.pdf"))
            elif option == 'Shnayim Mikra':
                doc_out.insert_pdf(fitz.open(f"Shnayim{session2}.pdf"))
            if all(option not in chabadoptions for option in opt) and any(option in opt for option in ['Project Likutei Sichos', 'Maamarim', 'Haftorah', 'Krias Hatorah (includes Haftorah)']):
                st.error("Project Likutei Sichos, Kriah, the Haftorah, and Maamarim are not available from Chabad.org. Please try again.")
                st.stop()
    else:
        for q in optconv:
            for z in dow:
                for i, top_level in enumerate(toc):
                    if not top_level[2]:
                        continue
                    if top_level[1] == q:
                        for j, sub_level in enumerate(toc[i+1:], start=i+1):
                            if sub_level[0] != top_level[0] + 1:
                                break
                            if z in sub_level[1]:
                                start_page = sub_level[2] - 1
                                if top_level[1] == "חומש יומי":
                                    if z == 'שבת קודש':
                                        end_page = toc[j+1][2] - 2
                                    else:
                                        end_page = toc[j+1][2] - 1
                                    print("Chumash found")
                                if top_level[1] == "תניא יומי":
                                    end_page = toc[j+1][2] - 2
                                    print("Tanya found")
                                if top_level[1] == 'רמב"ם - שלושה פרקים ליום':
                                    end_page = toc[j+1][2] - 1
                                    print("Rambam found")
                                print(f"Current Start Page: {start_page}. Current End Page: {end_page}")
                                start_page, end_page = dedupe(pages, pages2, pages3, start_page, end_page)
                                print(f"New Start Page: {start_page}. New End Page: {end_page}")
                                doc_out.insert_pdf(doc, from_page=start_page, to_page=end_page)
                                continue

            if q == 'חומש לקריאה בציבור' or q == 'מאמרים' or q == 'לקוטי שיחות':
                for i, item in enumerate(toc):
                    if q == 'לקוטי שיחות':
                        for word in item[1].split():
                            if word == 'לקוטי' and item[1].split()[item[1].split().index(word) + 1] == 'שיחות':
                                print("Likutei Sichos found")
                                pdf_file = open(f"dvar{session2}.pdf", "rb")
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                page_num_start = item[2] - 1
                                print(page_num_start)
                                page_num_end = find_next_top_level_bookmark(toc, i)
                                print(page_num_end)
                                doc_out.insert_pdf(doc, from_page=page_num_start, to_page=page_num_end)
                    if q == 'מאמרים':
                        for word in item[1].split():
                            if word == 'מאמר':
                                print("Maamarim found")
                                pdf_file = open(f"dvar{session2}.pdf", "rb")
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                page_num_start = item[2] - 1
                                print(page_num_start)
                                page_num_end = find_next_top_level_bookmark(toc, i)
                                print(page_num_end)
                                doc_out.insert_pdf(doc, from_page=page_num_start, to_page=page_num_end)
                    if item[1] == 'חומש לקריאה בציבור' and q == 'חומש לקריאה בציבור':
                        pdf_file = open(f"dvar{session2}.pdf", "rb")
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        page_num_start = item[2] - 1
                        page_num_end = toc[i+1][2] - 3
                        print("Torah reading found")
                        if "Krias Hatorah (includes Haftorah)" in opt and not kriahattatch:
                            print("Kriah found")
                            doc_out.insert_pdf(doc, from_page=page_num_start, to_page=page_num_end)
                            kriahattatch = True
                        elif 'Haftorah' in opt and 'Krias Hatorah (includes Haftorah)' not in opt:
                            for page_num in range(page_num_start, page_num_end):
                                print("Haftorah found")
                                page = pdf_reader.pages[page_num]
                                text = page.extract_text()
                                if "ברכת הפטורה" in text or "xtd enk dxhtdd renyl" in text:
                                    doc_out.insert_pdf(doc, from_page=page_num, to_page=page_num_end)
                                    continue

            if 'Rambam' in q:
                print("Appending Rambam")
                doc_out.insert_pdf(fitz.open(f"Rambam{session}.pdf"))
                print("Appended")
                continue

            if q == 'Hayom Yom':
                print("Hayom Yom found")
                doc_out.insert_pdf(fitz.open(f"Hayom{session}.pdf"))
                print("Appended")
                continue

            if q == 'Shnayim Mikra':
                print("Shnayim Mikra found")
                doc_out.insert_pdf(fitz.open(f"Shnayim{session2}.pdf"))
                print("Appended")
                continue

    doc_out.save(os.path.join(output_dir, f"output_dynamic{session}.pdf"))
    doc_out.close()

@st.cache_data(ttl="12h")
def dateset():
    session2 = dt.now()
    print(f"Session: {session2}")
    return session2

with st.form(key="dvarform", clear_on_submit=False):  # streamlit form for user input
    st.title("Dvar Creator 📚 (BETA)")
    st.info("Need more than 1 week? Check out 📖[Chitas Collator](https://chitas-collator.streamlit.app/)!")
    markdownlit.mdlit("""This app is designed to create a printout for Chitas, Rambam, plus a few other things. To get the materials directly and support the original publishers, go to @(**[blue]Dvar Malchus[/blue]**)(https://dvarmalchus.org/)
    and @(🔥)(**[orange]Chabad.org[/orange]**)(https://www.chabad.org/dailystudy/default_cdo/jewish/Daily-Study.htm/).
    """)
    session2 = dateset()
    print(f"test {session2}")
    date1 = date.today().strftime('%Y, %-m, %-d')
    year, day, month = date1.split(", ")
    year, day, month = int(year), int(day), int(month)
    parsha = parshios.getparsha_string(dates.GregorianDate(year, day, month), israel=False, hebrew=True)
    week = pills("Select which days of the week you would like to print.", options=['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Shabbos'], multiselect=True, clearable=True, index=None)
    st.write("**Select which materials you would like to print.** (Select as many as you'd like!)")
    basics = pills('Basics:', options=['Chumash', 'Tanya', 'Hayom Yom'], multiselect=True, clearable=True, index=None)
    rambamopts = pills('Rambam:', options=['Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Hebrew', 'Rambam (1)-Bilingual', 'Rambam (1)-English'], multiselect=True, clearable=True, index=None)
    extras = pills('MISC:', options=['Project Likutei Sichos (Hebrew)', 'Maamarim', 'Krias Hatorah (includes Haftorah)', 'Haftorah', 'Shnayim Mikra'], multiselect=True, clearable=True, index=None)
    source = stt.st_toggle_switch(label='Try to use Dvar Malchus, or get from Chabad.org? If toggled on (green), it will attempt to get from Dvar Malchus.', default_value=True, label_after=True, inactive_color='#780c21', active_color='#0c7822', track_color='#0c4c78')
    with st.expander("Advanced Options"):
        cover = st.checkbox('Include the cover page from Dvar Malchus?', value=False)
        scaleslide = st.slider('Change the scale of Chumash and Tanya from Chabad.Org. Default is 100%.', 30, 100, 100)
        st.write("Scale is", scaleslide, "%")
        scale = scaleslide / 100
        scaleslide2 = st.slider('Change the scale of Rambam from Chabad.Org. Default is 50%.', 30, 100, 50)
        st.write("Scale is", scaleslide2, "%")
        scale2 = scaleslide2 / 100
        scaleslide3 = st.slider('Change the scale of Hayom Yom from Chabad.Org. Default is 80%.', 30, 100, 80)
        st.write("Scale is", scaleslide3, "%")
        scale3 = scaleslide3 / 100

    submit_button = st.form_submit_button(label="Generate PDF ▶️")

if submit_button:  # if the user submits the form, run the following code
    if 'id' not in st.session_state:
        st.session_state['id'] = dt.now()
    opt = []
    try:
        if len(basics) > 0:
            print("appending selected basics")
            opt += basics
    except:
        pass
    try:
        if len(rambamopts) > 0:
            print("appending selected rambam")
            opt += rambamopts
    except:
        pass
    try:
        if len(extras) > 0:
            print("appending selected extras")
            opt += extras
    except:
        pass
    print(opt)
    session = st.session_state['id']
    weekorder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Shabbos']
    optorder = ['Chumash', 'Tanya', 'Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Hebrew', 'Rambam (1)-Bilingual', 'Rambam (1)-English', 'Hayom Yom', 'Project Likutei Sichos (Hebrew)', 'Maamarim', 'Haftorah', 'Krias Hatorah (includes Haftorah)', 'Shnayim Mikra']
    daydependent = ['Chumash', 'Tanya', 'Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Hebrew', 'Rambam (1)-Bilingual', 'Rambam (1)-English', 'Hayom Yom']
    chabadoptions = ['Chumash', 'Tanya', 'Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Hebrew', 'Rambam (1)-Bilingual', 'Rambam (1)-English', 'Hayom Yom']
    dow = []
    optconv = []
    dor = []
    opt = sorted(opt, key=optorder.index)
    try:
        week = sorted(week, key=weekorder.index)
        daytoheb(week, dow)
        daytorambam(week, dor)
    except:
        pass

    opttouse(opt, optconv)
    print(optconv)
    print(source)
    if not week and any(x in opt for x in daydependent):
        st.error("Please select at least one day of the week if trying to select anything from the 'Basics' or 'Rambam' sections.")
        st.stop()
    if not week and ('חומש לקריאה בציבור' in optconv or 'מאמרים' in optconv or 'לקוטי שיחות' in optconv or 'Shnayim Mikra' in optconv):
        week = ['Sunday']
        print(optconv)
    print(week)
    if source:
        if any(x in opt for x in ['Chumash', 'Tanya', 'Haftorah', 'Rambam (3)-Hebrew', 'Project Likutei Sichos (Hebrew)', 'Maamarim', 'Krias Hatorah (includes Haftorah)']):
            if not os.path.exists(f"dvar{session2}.pdf"):
                try:
                    with st.spinner('Attempting to download Dvar Malchus...'):
                        dvarget(session2)
                except:
                    st.write("Dvar Malchus not found. Using Chabad.org...")
                    source = False
                    cover = False
        else:
            st.write("Dvar Malchus not needed. Using Chabad.org...")
            source = False
            cover = False
    with st.spinner('Creating PDF...'):
        if not source:
            chabadget(dor, opt, session)
            if any(x in opt for x in ['Rambam (3)-Hebrew', 'Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Bilingual', 'Rambam (1)-English', 'Rambam (1)-Hebrew']):
                rambamenglish(dor, session, opt)
        if source:
            if any(x in opt for x in ['Rambam (3)-Bilingual', 'Rambam (3)-English', 'Rambam (1)-Bilingual', 'Rambam (1)-English', 'Rambam (1)-Hebrew']) or ('Rambam (3)-Hebrew' in opt and not os.path.exists(f"dvar{session2}.pdf")):
                rambamenglish(dor, session, opt)

        if 'Hayom Yom' in opt:
            hayomyom(dor, session)

        if 'Shnayim Mikra' in opt:
            shnayimget(session2, parsha)

        dynamicmake(dow, optconv, opt, source, session)

    if os.path.exists(f"output_dynamic{session}.pdf"):
        st.success("PDF created successfully!")
        st.balloons()
        with open(f"output_dynamic{session}.pdf", "rb") as f:
            st.download_button(label="Download ⬇️", data=f, file_name="Custom_Chitas.pdf", mime="application/pdf")

    if glob.glob("Rambam*.pdf"):
        for file in glob.glob("Rambam*.pdf"):
            timestamp = file.lstrip("Rambam").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(minutes=1) and file != f'Rambam{session}.pdf':
                os.remove(file)

    if glob.glob("Chumash*.pdf"):
        for file in glob.glob("Chumash*.pdf"):
            timestamp = file.lstrip("Chumash").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(minutes=1) and file != f'Chumash{session}.pdf':
                os.remove(file)

    if glob.glob("Tanya*.pdf"):
        for file in glob.glob("Tanya*.pdf"):
            timestamp = file.lstrip("Tanya").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(minutes=1) and file != f'Tanya{session}.pdf':
                os.remove(file)

    if glob.glob("dvar*.pdf"):
        for file in glob.glob("dvar*.pdf"):
            timestamp = file.lstrip("dvar").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(hours=14) and file != f'dvar{session2}.pdf':
                os.remove(file)

    if glob.glob('Shnayim*.pdf'):
        for file in glob.glob('Shnayim*.pdf'):
            timestamp = file.lstrip("Shnayim").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(hours=14) and file != f'Shnayim{session2}.pdf':
                os.remove(file)

    if glob.glob("output_dynamic*.pdf"):
        for file in glob.glob("output_dynamic*.pdf"):
            timestamp = file.lstrip("output_dynamic").rstrip(".pdf")
            file_datetime = dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if dt.now() - file_datetime > timedelta(minutes=1) and file != f'output_dynamic{session}.pdf':
                os.remove(file)

markdownlit.mdlit("**Any major bugs noticed? Features that you'd like to see? Comments? Email me [📧 here!](mailto:mkievman@outlook.com)**")

if not submit_button:
    with st.expander("**Changelog:**"):
        markdownlit.mdlit("**New in latest update (1-17-24)**: <br/> **[FIX]** Updated location of Dvar Malchus download button.")
        markdownlit.mdlit("**Past Changes (7-17-23)**: <br/> **1:** Repeated compilations of materials from Dvar Malchus should be considerably faster. <br/> **2:** Shnayim mikra gets considerably faster on subsequent reruns. <br/> **3:** Fixes to maamarim and sichos to fail less often.")

if submit_button:
    if os.path.exists(f"output_dynamic{session}.pdf"):
        with st.expander("NOTE: If you are receiving last week's materials, please click here."):
            newtime = st.button("Clear Cached Time", on_click=dateset.clear)