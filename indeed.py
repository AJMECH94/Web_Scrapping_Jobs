from flask import Flask, send_file, jsonify, url_for
from flask import redirect, request, session, render_template
import os
from celery import Celery
from celery.states import state, PENDING, SUCCESS
from flask_session import Session
import pandas as pd
from celery.result import AsyncResult
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from login_required_decorator import login_required
import csv
import mysql.connector
from flask_migrate import Migrate
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time
import pandas as pd

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
sess = Session()
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@localhost/scrap'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)



"""
Indeed.com crawler
"""
import random

import pandas as pd

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
    #save_indeed_data_to_db()

