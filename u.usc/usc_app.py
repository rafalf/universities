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
from sys import platform
import csv
import json

parser = argparse.ArgumentParser()
parser.add_argument("--parse", help="parse the user data folder", required=True)
parser.add_argument("--debug", help="test mode. throws exceptions", action='store_true')
args = parser.parse_args()
arg_dict = vars(args)
parse = arg_dict['parse']
debug = arg_dict['debug']

logger = logging.getLogger('u.usc')
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
plat = platform
if plat == 'darwin': # OSX
    driver = webdriver.Chrome()
else:
    driver = webdriver.Chrome(os.path.join(root_path, 'driver', 'chromedriver.exe'))
driver.maximize_window()

def application(user_data):

    school_urls = _get_urls('usc-1')
    if not school_urls:
        logger.info('school urls not found')
        sys.exit(1)
    else:
        login_url = school_urls[0][2]

    jsn = _load_json(os.path.join(user_data, 'user.json'))
    logger.info('Loaded json:')
    for section in jsn:
        logger.info(section)

    try:
        driver.get(login_url)
        # login form
        el = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#cas-login-field-username')))
        el.send_keys(jsn[6]['username'])
        driver.find_element_by_css_selector("input[type='password']").send_keys(jsn[6]['password'])
        driver.find_element_by_css_selector("button.cas-login-sign-in-button").click()
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.cas-signout-link')))
        logger.info('Signed in')
    except:
        logger.info("Log in failed. Please check login credentials and run the script again")
        raw_input('Please press ENTER to continue')

    if not _wait_for_element_not_present('.cas-welcome-container', 2):
        raw_input('Please start the application.'
              '\nOnce the application is started, press ENTER to begin with the forms.')

    # ______________
    # FORMS
    # ______________
    # PERSONAL INFORMATION PAGES

    school_urls = _get_urls('usc-personal')

    # BIO
    # *******************************
    logger.info('Bio form')

    try:
        driver.get(school_urls[0][1])
        logger.info('Page url: {}'.format(school_urls[0][1]))

        wait_for_angular()

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[name="biographicInfoForm"]')))

        # Birth Information
        dob_ = _parse_date(jsn[3]['dob'])
        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                        'input#personalInfo-biographicInfo-birthInfo-dob')))
        el.clear()
        el.send_keys(dob_)

        # City:
        el_city = driver.find_element_by_css_selector("input#personalInfo-birthInfo-city")
        el_city.clear()
        el_city.send_keys(jsn[3]['citybirth'])

        # Country:
        country_ = jsn[3]['countrybirth']
        select = Select(driver.find_element_by_css_selector("select#personalInfo-biographicInfo-birthInfo-country"))
        select.select_by_visible_text(country_)

        wait_for_angular()

        # State
        state_locator = "select#personalInfo-biographicInfo-birthInfo-state"
        el_state = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, state_locator)))
        select = Select(el_state)
        select.select_by_visible_text('Other/Unknown')

        wait_for_angular()

        county_locator = "select#personalInfo-biographicInfo-birthInfo-county"
        el_county = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, county_locator)))
        select = Select(el_county)
        select.select_by_visible_text('N/A')

        gender = jsn[3]['gendre']
        if gender == 'Male':
            driver.find_element_by_css_selector("div#personalInfo-biographicInfo-gender-gender-male").click()
        else:
            driver.find_element_by_css_selector("div#personalInfo-biographicInfo-gender-gender-female").click()

        wait_for_angular()

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
              "\nMake sure when the form is submitted you close the successful message"
              "\nThen press ENTER to continue on with other forms")

    # CONTACT INFO
    # *******************************
    logger.info('Contact info form')

    try:
        driver.get(school_urls[0][2])
        logger.info('Page url: {}'.format(school_urls[0][2]))
        wait_for_angular()

        address_1 = jsn[1]['current_mail']
        address_2 = jsn[1]['current_mail_line2']
        city = jsn[1]['current_city']
        us_state = jsn[1]['current_us_state']
        country = jsn[1]['current_mailcountry']
        post_code = jsn[1]['current_postalcode']

        # Current address:
        el_address = driver.find_element_by_css_selector("input#personalInfo-birthInfo-streetAddress1")
        el_address.clear()
        el_address.send_keys(address_1)
        el_address= driver.find_element_by_css_selector("input#personalInfo-birthInfo-streetAddress2")
        el_address.clear()
        el_address.send_keys(address_2)
        el_address =driver.find_element_by_css_selector("input#personalInfo-contactInfo-city")
        el_address.clear()
        el_address.send_keys(city)

        country_locator = "select#personalInfo-birthInfo-country"
        el_country = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, country_locator)))
        select = Select(el_country)
        select.select_by_visible_text(country)

        wait_for_angular()

        if country == "United States":
            state = us_state
        else:
            state = 'Other/Unknown'

        country_locator = "select#personalInfo-birthInfo-state"
        el_state = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, country_locator)))
        select = Select(el_state)
        select.select_by_visible_text(state)

        wait_for_angular()

        el_zip = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[name="zipCode"]')))
        el_zip.send_keys(post_code)

        # permanent
        driver.find_element_by_css_selector("div#personalInfo-birthInfo-isPermanentAddress-yes").click()

        wait_for_angular()

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
              "\nMake sure when the form is submitted you close the successful message"
              "\nThen press ENTER to continue on with other forms")

    # CITIZEN INFO
    # *******************************
    logger.info('Citizen info form')

    try:
        driver.get(school_urls[0][3])
        logger.info('Page url: {}'.format(school_urls[0][3]))
        wait_for_angular()

        logger.info('Citizenship Details to fill out manually')

        # State of Residence
        state_resident = jsn[3]['legal_state_resident']
        state_locator = "select#personalInfo-citizenshipInfo-residencyInfo-legalState"
        el_state = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, state_locator)))
        select = Select(el_state)
        select.select_by_visible_text(state_resident)

        wait_for_angular()

        # County
        if state_resident in ['International', 'Other/Unknown']:
            legal_county_resident = 'N/A'
        else:
            legal_county_resident = jsn[3]['legal_county_resident']

        county_locator = "select#personalInfo-citizenshipInfo-residencyInfo-legalCounty"
        el_county = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, county_locator)))
        select = Select(el_county)
        select.select_by_visible_text(legal_county_resident)

        wait_for_angular()

        # Visa
        if jsn[6]['usa_visa'].lower() == 'yes':
            visa = 'div#personalInfo-citizenshipInfo-visaInfo-holder-yes'
        elif jsn[6]['usa_visa'].lower() == 'no':
            visa = 'div#personalInfo-citizenshipInfo-visaInfo-holder-no'
        else:
            logger.info('Visa unrecognized')
            visa = None
        if visa:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, visa))).click()

        wait_for_angular()

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # RACE
    # *******************************
    logger.info('Race form')

    try:
        driver.get(school_urls[0][4])
        logger.info('Page url: {}'.format(school_urls[0][4]))
        wait_for_angular()

        county_locator = "select#cas-personalInfo-raceAndEthnicity-ethnicity-hispanicOrLatino"
        el_county = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, county_locator)))
        select = Select(el_county)
        if jsn[3]['hispanic'] == 'no':
            select.select_by_visible_text('No')
        else:
            select.select_by_visible_text('Yes')

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
              "\nMake sure when the form is submitted you close the successful message"
              "\nThen press ENTER to continue on with other forms")

    # OTHER INFO
    # *******************************
    logger.info('Citizen info form')

    try:
        driver.get(school_urls[0][5])
        logger.info('Page url: {}'.format(school_urls[0][5]))

        wait_for_angular()

        # native language
        if jsn[5]['language1_prof'].lower() == 'native':
            native_lang = jsn[5]['language1']
        elif jsn[5]['language2_prof'].lower() == 'native':
            native_lang = jsn[5]['language2']

        # another
        another_lang = None
        if jsn[5]['language1_prof'].lower() != 'native':
            another_lang = jsn[5]['language1']
            another_prof = jsn[5]['language1_prof']
        elif jsn[5]['language2_prof'].lower() != 'native':
            another_lang = jsn[5]['language2']
            another_prof = jsn[5]['language2_prof']

        native_locator = "select#personalInfo-otherInfo-languageProficiency-nativeLanguage"
        el_native = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, native_locator)))
        select = Select(el_native)
        select.select_by_visible_text(native_lang)

        wait_for_angular()

        # we might need to test out what is json and
        # if it fits in Select , because now it causes this form to fail

        if another_lang:
            add_button = 'button.cas-primary-button-small-add'
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, add_button))).click()

            wait_for_angular()

            another_locator = "select#personalInfo-otherInfo-languageProficiency-additionalLanguage-language"
            el_another = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, another_locator)))
            select = Select(el_another)
            select.select_by_visible_text(another_lang)

            wait_for_angular()

        # we might need to test out what is json and
        # if it fits in Select , because now it causes this form to fail

        #
        #     another_prof_locator = "select#personalInfo-otherInfo-languageProficiency-additionalLanguage-language"
        #     el_prof_another = WebDriverWait(driver, 5).until(
        #         EC.presence_of_element_located((By.CSS_SELECTOR, another_prof_locator)))
        #     select = Select(el_prof_another)
        #     select.select_by_visible_text(another_prof)
        #
        #     wait_for_angular()

        family_usc = jsn[6]['Did your parents or siblings attend USC?']
        first_to_college = jsn[6]['Are you the first-generation in your family to go to college?']
        employed_usc = jsn[6]['Are your parents or spouse employed at USC?']
        apply_dual = jsn[6]['Are you applying for a dual degree at USC?']
        apply_before = jsn[6]['Have you previously applied to or attended USC?']
        sponsorship = jsn[6]['Have you applied for, received, or are planning to apply for a financial' \
                             ' sponsorship from your employer?']

        radios = []
        if family_usc.lower() == 'yes':
            radios.append("div#cas-program-questions-251727-577861>div")
        elif family_usc.lower() == 'no':
            radios.append("div#cas-program-questions-251727-577862>div")

        if first_to_college.lower() == 'yes':
            radios.append("div#cas-program-questions-251728-577863>div")
        elif first_to_college.lower() == 'no':
            radios.append("div#cas-program-questions-251728-577864>div")

        if employed_usc.lower() == 'yes':
            radios.append("div#cas-program-questions-251729-577865>div")
        elif employed_usc.lower() == 'no':
            radios.append("div#cas-program-questions-251729-577866>div")

        if apply_dual.lower() == 'yes':
            radios.append("div#cas-program-questions-251730-577867>div")
        elif apply_dual.lower() == 'no':
            radios.append("div#cas-program-questions-251730-577868>div")

        if apply_before.lower() == 'yes':
            radios.append("div#cas-program-questions-251731-577869>div")
        elif apply_before.lower() == 'no':
            radios.append("div#cas-program-questions-251731-577870>div")

        # employer
        if sponsorship.lower() == 'yes':
            radios.append("div#cas-program-questions-251737-577896>div")
        elif sponsorship.lower() == 'no':
            radios.append("div#cas-program-questions-251737-577897>div")

        for radio in radios:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, radio))).click()

        submit_form()


    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # _______________________
    # SUPPORTING INFORMATION

    school_urls = _get_urls('usc-supporting')

    # EXPERIENCE
    # *******************************

    logger.info('Experience form')

    try:
        driver.get(school_urls[0][1])

        wait_for_angular()

        if jsn[2]['current_emp_company_name']:
            company_name = jsn[2]['current_emp_company_name']
            company_type = jsn[2]['current_emp_type']
            company_emp_nature = jsn[2]['current_emp_nature']
            company_position = jsn[2]['current_emp_position']
            company_end_date = _parse_date(jsn[2]['current_emp_end_date'])
            company_start_date = _parse_date(jsn[2]['current_emp_start_date'])

            logger.info('Adding experience')

            el = _wait_for_element('a[href="#/supportingInfo/experiences/experience"]')
            if el:
                el.click()
                wait_for_angular()

                exp_type = 'select#supportingInfo-experiences-experience-type'
                el_experience = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, exp_type)))
                select = Select(el_experience)
                select.select_by_visible_text('Employment')

                el_name = driver.find_element_by_css_selector("[name='orgName']")
                el_name.clear()
                el_name.send_keys(company_name)

                current_exp = '#supportingInfo-experiences-experience-employmentDates-yes'
                driver.find_element_by_css_selector(current_exp).click()

                # country - your current address country
                exp_country = 'select#supportingInfo-experiences-experience-organization-orgCountry'
                el_experience = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, exp_country)))
                select = Select(el_experience)
                select.select_by_visible_text(country)
                wait_for_angular()

                # state
                if country != 'United States':
                    exp_state = 'div[label="State"] select'
                    el_experience = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, exp_state)))
                    select = Select(el_experience)
                    select.select_by_visible_text('Other/Unknown')
                    wait_for_angular()

                # start date
                start_data_locator = 'input#supportingInfo-experiences-experience-employmentDates-startDate'
                el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, start_data_locator)))
                el.clear()
                el.send_keys(company_start_date)

                wait_for_angular()

                # contact company
                current_exp = '#supportingInfo-experiences-experience-employmentDetails-yes'
                driver.find_element_by_css_selector(current_exp).click()

                # end date
                # start_data_locator = 'input#supportingInfo-experiences-experience-employmentDates-endDate'
                # el = WebDriverWait(driver, 5).until(
                #     EC.presence_of_element_located((By.CSS_SELECTOR, start_data_locator)))
                # el.clear()
                # el.send_keys(company_end_date)

                wait_for_angular()

                el_name = driver.find_element_by_css_selector("[name='jobTitle']")
                el_name.clear()
                el_name.send_keys(company_position)

                # type
                visible_text = None
                if company_type.count('Full'):
                    visible_text = 'Full time'
                elif company_type.count('Part'):
                    visible_text = 'Part time'
                elif company_type.count('Temp'):
                    visible_text = 'Temporary'

                if visible_text:
                    exp_type = 'select#supportingInfo-experiences-experience-employmentDates-status'
                    el_experience = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, exp_type)))
                    select = Select(el_experience)
                    select.select_by_visible_text(visible_text)
                    wait_for_angular()
                else:
                    logger.info('Status not provided')
        else:
            logger.info('I am not adding any experience. Opt out')

            el = _wait_for_element('.cas-experiences-opted-out button')
            el.click()

        submit_form('experience')

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
              "\nMake sure when the form is submitted you close the successful message"
              "\nThen press ENTER to continue on with other forms")

    # ACHIEVEMENT
    # *******************************

    logger.info('Achievement form')

    try:
        driver.get(school_urls[0][2])

        wait_for_angular()

        if _wait_for_element('.cas-opted-out-background', 1):
            logger.info('Achievement already added')
        else:
            logger.info('I am not adding any achievements')

            el = _wait_for_element('.cas-achievements-opt-out-button-container button')
            if el:
                el.click()

            if _wait_for_element('.cas-opted-out-background'):
                logger.info('Form completed')

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # CONFERENCES
    # *******************************

    logger.info('Conferences attended form')

    try:
        driver.get(school_urls[0][3])

        wait_for_angular()

        if _wait_for_element('.cas-opted-out-background', 1):
            logger.info('Conferences already opted out')
        else:
            logger.info('I am not adding any conferences. Opt out')

            el = _wait_for_element('.cas-conferences-attended-opt-out-button-container button')
            if el:
                el.click()

            if _wait_for_element('.cas-opted-out-background'):
                logger.info('Form completed')

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # MEMBERSHIPS
    # *******************************

    logger.info('Membership attended form')

    try:
        driver.get(school_urls[0][4])

        wait_for_angular()

        if _wait_for_element('.cas-opted-out-background', 1):
            logger.info('Memberships already opted out')
        else:
            logger.info('I am not adding any memberships. Opt out')

            el = _wait_for_element('.cas-memberships-opt-out-button-container button')
            if el:
                el.click()

            if _wait_for_element('.cas-opted-out-background'):
                logger.info('Form completed')

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # DOCUMENTS (CV)
    # *******************************

    logger.info('Documents form')

    try:
        driver.get(school_urls[0][5])

        wait_for_angular()

        resume = jsn[6]['resume_file_name']

        if _wait_for_element('.cas-complete', 0.5):
            logger.info('Uploaded already')

        elif resume:
            list_content = os.listdir(parse)
            if not resume in list_content:
                logger.info('Resume: {} doesnot exist in parsed folder'.format(resume))
            else:
                resume_file = os.path.join(parse, resume)

                el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, '.cas-documents-list li:nth-of-type(1) button')))
                el.click()

                wait_for_angular()

                el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'input.cas-file-input')))
                el.send_keys(resume_file)

                # save document
                wait_for_angular()
                el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 'button.cas-subsection-form-save-button')))
                el.click()

                wait_for_angular()

                if not _wait_for_element_not_present('.cas-system-error-message', 2):
                    logger.info('Error uploading csv...')
                    raise
                elif not _wait_for_element('.cas-complete', 2):
                    logger.info('Uploading csv failed ?...')
                    raise

                logger.info('Resume: {} added'.format(resume_file))
        else:
            logger.info('No resume to upload!')

        logger.info('Form completed')
    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    raw_input("We went through all forms. \n"
              "Please review all forms and press ENTER to stop the script")

def wait_for_angular():
    driver.set_script_timeout(10)
    driver.execute_async_script("""
        callback = arguments[arguments.length - 1];
        angular.element('html').injector().get('$browser').notifyWhenNoOutstandingRequests(callback);""")


def submit_form(button='submit'):

    map_buttons = {'submit': "button[type='submit']"}
    map_buttons['experience'] = '[name="addExperienceForm"] button.cas-subsection-form-save-button'

    # Submit form
    submit_button = driver.find_element_by_css_selector(map_buttons[button])
    if submit_button.is_enabled():
        submit_button.click()
        wait_for_angular()
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.cas-saved-successfully-modal')))

        # close alert
        el = driver.find_element_by_css_selector('.cas-icon-button-close')
        el.click()
        wait_for_angular()
        logger.info('Form submitted successfully!')
    else:
        logger.info('Submit button disabled. Form not completely filled out.')
        raw_input('Please correct the form and press ENTER to submit!')
        if submit_button.is_enabled():
            submit_button.click()
        else:
            raw_input('\nSubmit button disabled. The form still not correct. '
                  '\nCorrect the form and click on the submit button.'
                  '\nMake sure when the form is submitted you close the successful message'
                  '\nThen press ENTER to continue on with other forms')


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


def _parse_date(date_):

    d = date_.split('-')
    return "{}/{}/{}".format(d[1], d[2], d[0])


def _get_urls(school):
    with open(os.path.join(root_path, 'urls.csv'), 'rb') as hlr:
        rd = csv.reader(hlr, delimiter=',', quotechar='"')
        return [row for row in rd if row[0] == school]


def _load_json(file_):
    with open(file_) as hlr:
        return json.load(hlr)


def _wait_for_element(el, time_=5):
    try:
        return WebDriverWait(driver, time_).until(EC.presence_of_element_located((By.CSS_SELECTOR, el)))
    except:
        logger.info('Element {} not present.'.format(el))


def _wait_for_element_not_present(el, time_):
    try:
        WebDriverWait(driver, time_).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, el)))
        return True
    except:
        logger.info('Element {} present.'.format(el))





if __name__ == '__main__':
    set_logger()
    application(parse)
    driver.quit()