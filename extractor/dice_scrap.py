from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time


def extract_dice_jobs(tech, page):
    FILE_NAME = 'job_dice.csv'
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
    for k in range(1, int(page)):
        URL = f"https://www.dice.com/jobs?q={tech}&countryCode=US&radius=30&radiusUnit=mi&page={k}&pageSize=20&language=en&eid=S2Q_,bw_1"

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






