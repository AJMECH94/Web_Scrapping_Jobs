import requests
from celery import Celery
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from lxml.html import fromstring
from crawl import save_dice_data_to_db, save_indeed_data_to_db, save_naukri_data_to_db
import random

celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

"""
Dice Crawler
"""
@celery.task(bind=True)
def extract_dice_jobs(self, tech, location, page=1):
    FILE_NAME = 'dice.csv'
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(executable_path="C:\Program Files\Google\chromedriver\chromedriver.exe", options=options)

    driver.maximize_window()
    time.sleep(3)

    job_titles_list, company_name_list, location_list, job_types_list = [], [], [], []

    job_posted_dates_list, job_descriptions_list = [], []
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    for k in range(1, int(page)):
        URL = f"https://www.dice.com/jobs?q={tech}&location={location}&radius=30&radiusUnit=mi&page={k}&pageSize=20&language=en&eid=S2Q_,bw_1"
        driver.get(URL)
        driver.maximize_window()
        try:

            input = driver.find_element(By.ID, "typeaheadInput")
            input.click()
        except:
            time.sleep(5)

        job_titles = driver.find_elements(By.CLASS_NAME, "card-title-link")
        company_name = driver.find_elements(
            By.XPATH, '//div[@class="card-company"]/a')
        job_locations = driver.find_elements(
            By.CLASS_NAME, "search-result-location")
        job_types = driver.find_elements(
            By.XPATH, '//span[@data-cy="search-result-employment-type"]')
        job_posted_dates = driver.find_elements(By.CLASS_NAME, "posted-date")
        job_descriptions = driver.find_elements(By.CLASS_NAME, "card-description")

        # company_name
        for i in company_name:
            company_name_list.append(i.text)

        # job titles list
        for i in job_titles:
            job_titles_list.append(i.text)

        # #locations
        for i in job_locations:
            location_list.append(i.text)

        # job types
        for i in job_types:
            job_types_list.append(i.text)

        # job posted dates
        for i in job_posted_dates:
            job_posted_dates_list.append(i.text)

        # job_descriptions
        for i in job_descriptions:
            job_descriptions_list.append(i.text)
        #progress_recorder.set_progress(k+1, page,f'on iteration {k}')
        print(len(job_titles_list), len(job_descriptions_list),
              len(job_posted_dates_list), len(job_types_list),
              len(company_name_list), len(location_list))
        df = pd.DataFrame()
        df['Job Title'] = job_titles_list
        df['Company Name'] = company_name_list
        df['description'] = job_descriptions_list
        df['Posted Date'] = job_posted_dates_list
        df['Job Type'] = job_types_list
        df['Location'] = location_list
        df.to_csv(f'./static/{FILE_NAME}', index=False)
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS', meta={'current': k, 'total': page, 'status': message})
    return {'current': 100, 'total': 100, 'status': 'Task completed!'}

"""
Indeed.com crawler
"""
BASE_URL = 'https://in.indeed.com'
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument(f'user-agent={user_agent}')
options.add_argument("--window-size=1920,1080")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-running-insecure-content')
options.add_argument("--disable-extensions")
options.add_argument("--proxy-server='direct://'")
options.add_argument("--proxy-bypass-list=*")
options.add_argument("--start-maximized")
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
description_list, company_name_list, designation_list, salary_list, company_url = [], [], [], [], []
location_list, qualification_list = [], []
driver = webdriver.Chrome(executable_path="C:\Program Files\Google\chromedriver\chromedriver.exe", options=options)
job_detail_links = []
job_posted_dates_list, job_descriptions_list = [], []


@celery.task(bind=True)
def get_job_detail_links(tech, location, page):
    for page in range(0, page):
        time.sleep(5)
        URL = f"https://in.indeed.com/jobs?q={tech}&l={location}&start={page * 10}"
        try:
            driver.get(URL)
        except WebDriverException:
            print("page down")

        soup = BeautifulSoup(driver.page_source, 'lxml')

        for outer_artical in soup.findAll(attrs={'class': "css-1m4cuuf e37uo190"}):
            for inner_links in outer_artical.findAll(
                    attrs={'class': "jobTitle jobTitle-newJob css-bdjp2m eu4oa1w0"}):
                job_detail_links.append(
                    f"{BASE_URL}{inner_links.a.get('href')}")


@celery.task(bind=True)
def scrap_details(self, tech, location, page):
    print("___________", "Indeed")
    get_job_detail_links(tech, location, page)
    time.sleep(2)

    for link in range(len(job_detail_links)):

        time.sleep(5)
        driver.get(job_detail_links[link])
        soup = BeautifulSoup(driver.page_source, 'lxml')
        a = soup.findAll(
            attrs={'class': "jobsearch-InlineCompanyRating-companyHeader"})
        company_name_list.append(a[1].text)
        try:
            company_url.append(a[1].a.get('href'))
        except:
            company_url.append('NA')

        salary = soup.findAll(
            attrs={'class': "jobsearch-JobMetadataHeader-item"})
        if salary:
            for i in salary:
                x = i.find('span')
                if x:
                    salary_list.append(x.text)
                else:
                    salary_list.append('NA')
        else:
            salary_list.append('NA')

        description = soup.findAll(
            attrs={'class': "jobsearch-jobDescriptionText"})

        if description:
            for i in description:
                description_list.append(i.text)
        else:
            description_list.append('NA')

        designation = soup.findAll(
            attrs={'class': 'jobsearch-JobInfoHeader-title-container'})
        if designation:
            designation_list.append(designation[0].text)
        else:
            designation_list.append('NA')


        for Tag in soup.find_all('div', class_="icl-Ratings-count"):
            Tag.decompose()
        for Tag in soup.find_all('div', class_="jobsearch-CompanyReview--heading"):
            Tag.decompose()
        location = soup.findAll(
            attrs={'class': "jobsearch-CompanyInfoWithoutHeaderImage"})
        if location:
            for i in location:
                location_list.append(i.text)
        else:
            location_list.append('NA')

            # Qualification
        qualification = soup.findAll(
            attrs={"class": 'jobsearch-ReqAndQualSection-item--wrapper'})
        if qualification:
            for i in qualification:
                qualification_list.append(i.text)
        else:
            qualification_list.append('NA')
        verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
        adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
        noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
        message = ''
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                            random.choice(adjective),
                                            random.choice(noun))
        self.update_state(state='PROGRESS', meta={'current': link, 'total': page, 'status': message})
        return {'current': 100, 'total': 100, 'status': 'Task completed!'}
    FILE_NAME = 'indeed.csv'
    df = pd.DataFrame()
    df['Company Name'] = company_name_list
    df['Company_url'] = company_url
    df['salary'] = salary_list
    # df['description_list'] = description_list
    df['designation_list'] = designation_list
    df['location_list'] = location_list
    df['qualification_list'] = qualification_list
    df.to_csv(f'./static/{FILE_NAME}', index=False)
    save_indeed_data_to_db()



"""
Naukari.com Crawler
"""
BASE_URL_naukari = 'https://www.naukri.com/'
FILE_NAME = 'naukri.csv'
CTC_FILTER_QUERY_PARAMS = '&ctcFilter=101&ctcFilter=15to25&ctcFilter=25to50&ctcFilter=50to75&ctcFilter=75to100'
CITY_FILTER_PARAMS = '&cityTypeGid=6&cityTypeGid=17&cityTypeGid=51&cityTypeGid=73&cityTypeGid=97&cityTypeGid=134&cityTypeGid=139&cityTypeGid=183&cityTypeGid=220&cityTypeGid=232&cityTypeGid=9508&cityTypeGid=9509'
INDUSTRY_FILTER_PARAMS = '&industryTypeIdGid=103&industryTypeIdGid=107&industryTypeIdGid=108&industryTypeIdGid=110&industryTypeIdGid=111&industryTypeIdGid=112&industryTypeIdGid=113&industryTypeIdGid=119&industryTypeIdGid=127&industryTypeIdGid=131&industryTypeIdGid=132&industryTypeIdGid=133&industryTypeIdGid=137&industryTypeIdGid=149&industryTypeIdGid=155&industryTypeIdGid=156&industryTypeIdGid=164&industryTypeIdGid=167&industryTypeIdGid=172&industryTypeIdGid=175'

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
options = webdriver.ChromeOptions()
options.headless = True
options.add_argument(f'user-agent={user_agent}')
options.add_argument("--window-size=1920,1080")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-running-insecure-content')
options.add_argument("--disable-extensions")
options.add_argument("--proxy-server='direct://'")
options.add_argument("--proxy-bypass-list=*")
options.add_argument("--start-maximized")
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
description_list_naukari, company_name_list_naukari, designation_list_naukari, salary_list_naukari, company_url_naukari = [], [], [], [], []
location_list_naukari, qualification_list_naukari = [], []
driver_naukari = webdriver.Chrome(executable_path="C:\Program Files\Google\chromedriver\chromedriver.exe",
                          options=options)
language = "python"
job_detail_links_naukari = []


def get_job_detail_links_naukari(tech, page):
    for page in range(1, page):
        query_param = f'{tech}-jobs'
        time.sleep(5)
        if CITY_FILTER_PARAMS != (
                '&cityTypeGid=4' or '&cityTypeGid=72' or '&cityTypeGid=135' or '&cityTypeGid=184' or '&cityTypeGid=187' or '&cityTypeGid=213' or '&cityTypeGid=229' or '&cityTypeGid=260' or '&cityTypeGid=325' or '&cityTypeGid=350' or '&cityTypeGid=507' or '&cityTypeGid=542' or '&cityTypeGid=9513' or '&cityTypeGid=101'):
            URL = f"{BASE_URL_naukari}{query_param}?k={tech}{CITY_FILTER_PARAMS}{CTC_FILTER_QUERY_PARAMS}{INDUSTRY_FILTER_PARAMS}" if page == 1 else f"{BASE_URL_naukari}{query_param}-{str(page)}?k={language}{CITY_FILTER_PARAMS}{CTC_FILTER_QUERY_PARAMS}{INDUSTRY_FILTER_PARAMS}"
            driver_naukari.get(URL)
            time.sleep(5)
        else:
            continue
        soup = BeautifulSoup(driver_naukari.page_source, 'lxml')

        for outer_artical in soup.findAll(attrs={'class': "jobTuple bgWhite br4 mb-8"}):
            for inner_links in outer_artical.find(attrs={'class': "jobTupleHeader"}).findAll(
                    attrs={'class': "title fw500 ellipsis"}):
                job_detail_links_naukari.append(inner_links.get('href'))

@celery.task(bind=True)
def scrap_naukari(self, tech, page):
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    get_job_detail_links_naukari(tech, page)
    time.sleep(2)
    designation_list_naukari, company_name_list_naukari, experience_list, salary_list__naukari = [], [], [], []
    location_list__naukari, job_description_list, role_list, industry_type_list = [], [], [], []
    functional_area_list, employment_type_list, role_category_list, education_list = [], [], [], []
    key_skill_list, about_company_list, address_list, post_by_list = [], [], [], []
    post_date_list, website_list, url_list = [], [], []

    for link in range(len(job_detail_links_naukari)):
        time.sleep(5)
        driver_naukari.get(job_detail_links_naukari[link])
        soup = BeautifulSoup(driver_naukari.page_source, 'lxml')

        if soup.find(attrs={'class': "salary"}) == None or soup.find(attrs={'class': 'loc'}) == "Remote":
            continue
        else:
            company_name_list_naukari.append("NA" if soup.find(attrs={'class': "jd-header-comp-name"}) == None else soup.find(
                attrs={'class': "jd-header-comp-name"}).text)
            experience_list.append(
                "NA" if soup.find(attrs={'class': "exp"}) == None else soup.find(attrs={'class': "exp"}).text)
            salary_list_naukari.append(
                "NA" if soup.find(attrs={'class': "salary"}) == None else soup.find(attrs={'class': "salary"}).text)
            loca = []
            location = (
                "NA" if soup.find(attrs={'class': 'loc'}) == None else soup.find(attrs={'class': 'loc'}).findAll('a'))
            for i in location:
                try:
                    loca.append(i.text)
                except AttributeError:
                    loca.append(i)
                except:
                    loca.append(i)

            location_list_naukari.append(",".join(loca))

            designation_list_naukari.append("NA" if soup.find(attrs={'class': "jd-header-title"}) == None else soup.find(
                attrs={'class': "jd-header-title"}).text)
            job_description_list.append(
                "NA" if soup.find(attrs={'class': "job-desc"}) == None else soup.find(attrs={'class': "job-desc"}).text)
            post_date_list.append(["NA"] if soup.find(attrs={'class': "jd-stats"}) == None else
                                  [i for i in soup.find(attrs={'class': "jd-stats"})][0].text.split(':')[1])
            try:
                website_list.append(
                    "NA" if soup.find(attrs={'class': "jd-header-comp-name"}).contents[0]['href'] == None else
                    soup.find(attrs={'class': "jd-header-comp-name"}).contents[0]['href'])
            except KeyError or ValueError:
                website_list.append("NA")
            except:
                website_list.append("NA")
            try:
                url_list.append(
                    "NA" if soup.find(attrs={'class': "jd-header-comp-name"}).contents[0]['href'] == None else
                    soup.find(attrs={'class': "jd-header-comp-name"}).contents[0]['href'])
            except KeyError or ValueError:
                website_list.append("NA")
            except:
                website_list.append("NA")

            details = []
            try:
                for i in soup.find(attrs={'class': "other-details"}).findAll(attrs={'class': "details"}):
                    details.append(i.text)
                role_list.append(details[0].replace('Role', ''))
                industry_type_list.append(details[1].replace('Industry Type', ''))
                functional_area_list.append(details[2].replace('Functional Area', ''))
                employment_type_list.append(details[3].replace('Employment Type', ''))
                role_category_list.append(details[4].replace('Role Category', ''))

                qual = []
                for i in soup.find(attrs={'class': "education"}).findAll(attrs={'class': 'details'}):
                    qual.append(i.text)
                education_list.append(qual)

                sk = []
                for i in soup.find(attrs={'class': "key-skill"}).findAll('a'):
                    sk.append(i.text)
                key_skill_list.append(",".join(sk))

                if soup.find(attrs={'class': "name-designation"}) == None:
                    post_by_list.append("NA")
                else:
                    post_by_list.append(soup.find(attrs={'class': "name-designation"}).text)

                if soup.find(attrs={'class': "about-company"}) == None:
                    about_company_list.append("NA")
                else:
                    address_list.append("NA" if soup.find(attrs={'class': "about-company"}).find(
                        attrs={'class': "comp-info-detail"}) == None else soup.find(
                        attrs={'class': "about-company"}).find(attrs={'class': "comp-info-detail"}).text)
                    about_company_list.append(soup.find(attrs={'class': "about-company"}).find(
                        attrs={'class': "detail dang-inner-html"}).text)
            except:
                pass
            if not message or random.random() < 0.25:
                message = '{0} {1} {2}...'.format(random.choice(verb),
                                                  random.choice(adjective),
                                                  random.choice(noun))
            self.update_state(state='PROGRESS', meta={'current': link, 'total': page, 'status': message})
            return {'current': 100, 'total': 100, 'status': 'Task completed!'}
    df = pd.DataFrame()
    df['Designation'] = designation_list_naukari
    df['Company Name'] = company_name_list_naukari
    df['Salary'] = salary_list_naukari
    df['Experience'] = experience_list
    df['Location'] = location_list_naukari
    df['Role'] = role_list
    df['Skills'] = key_skill_list
    df['Qualification'] = education_list
    df['Industry Type'] = industry_type_list
    df['Functional Area'] = functional_area_list
    df['Employment Type'] = employment_type_list
    df['Role Category'] = role_category_list
    df['Address'] = address_list
    df['Post By'] = post_by_list
    df['Post Date'] = post_date_list
    df['Website'] = website_list
    df['Url'] = url_list
    df['Job Description'] = job_description_list
    df['About Company'] = about_company_list
    df.to_csv(f'./static/{FILE_NAME}', index=False)
    save_naukri_data_to_db()
    driver_naukari.close()