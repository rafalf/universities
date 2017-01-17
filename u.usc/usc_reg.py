import logging
import time
import os
import sys
import argparse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import getopt
import csv
import json


logger = logging.getLogger('u.usc')
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
driver = webdriver.Chrome(os.path.join(root_path, 'driver', 'chromedriver.exe'))


def register(user_data):

    school_urls = _get_urls('usc')
    if not school_urls:
        logger.info('school urls not found')
        sys.exit(1)
    else:
        reg_url = school_urls[1]

    jsn = _load_json(os.path.join(user_data, 'user.json'))

    driver.get(reg_url)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#newUserAccount-name-title')))

    # Optional Your Name
    driver.find_element_by_css_selector("input[name='firstName']").send_keys(jsn[3]['name'])
    driver.find_element_by_css_selector("input[name='middleInitial']").send_keys(jsn[3]['middle-name'])
    driver.find_element_by_css_selector("input[name='lastName']").send_keys(jsn[3]['last-name'])
    # driver.find_element_by_css_selector("input[name='suffix']").send_keys()
    driver.find_element_by_css_selector("input[name='displayName']").send_keys(jsn[3]['name'])

    # Contact Information
    driver.find_element_by_css_selector("input[name='email']").send_keys(jsn[3]['email'])
    driver.find_element_by_css_selector("input[name='confirmEmail']").send_keys(jsn[3]['email'])
    driver.find_element_by_css_selector("input[name='phoneNumber']").send_keys(jsn[1]['phone2'])
    # driver.find_element_by_css_selector("input[name='alternatePhoneNumber']").send_keys()

    # Username and password
    # driver.find_element_by_css_selector("input[name='userName']").send_keys()
    # driver.find_element_by_css_selector("input[name='password']").send_keys()
    # driver.find_element_by_css_selector("input[name='confirmPassword']").send_keys()

    # security
    select = Select(driver.find_element_by_css_selector("select[name='securityQuestions']"))
    select.select_by_visible_text('What is your favorite color?')
    driver.find_element_by_css_selector("input[name='securityAnswer']").send_keys('black')

    driver.find_element_by_css_selector("#cas-newUserAccount-termsAndConditions-agreement>div").click()

    # Submit form
    submit_button = driver.find_element_by_css_selector("button[type='submit']")
    if submit_button.is_enabled():
        submit_button.click()
        logger.info('Form submitted successfully!')
        raw_input('Please press any key to close the script ...')
    else:
        logger.info('Form not completely filled in.')
        raw_input('Please correct the form and press any key to submit!')
        if submit_button.is_enabled():
            submit_button.click()
        else:
            raw_input('The form still not correct. Correct the form and click on the submit button')


def set_logger():

    log_file = os.path.join(root_path, 'logs',
                                time.strftime('%d%m%y%H%M', time.localtime()) + ".log")
    file_hndlr = logging.FileHandler(log_file)
    logger.addHandler(file_hndlr)
    console = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(console)
    ch = logging.Formatter('[%(levelname)s] %(message)s')
    console.setFormatter(ch)
    file_hndlr.setFormatter(ch)
    logger.setLevel(logging.getLevelName('DEBUG'))


def _get_urls(school):
    with open('urls.csv', 'rb') as hlr:
        rd = csv.reader(hlr, delimiter=',', quotechar='"')
        return  [row for row in rd[1:] if row[0] == school]


def _load_json(file_):
    with open(file_) as hlr:
        return json.load(hlr)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--parse", help="echo the string you use here", required=True)
    args = parser.parse_args()
    arg_dict = vars(args)

    parse = arg_dict['parse']

    set_logger()
    register(parse)
    driver.quit()