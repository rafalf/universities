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

    os.system('cls')

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

        middle_name = jsn[3]['middle-name']
        if not middle_name:
            logger.debug('Theres no middle name')

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
              "\nMake sure when the form is submitted you close the successful message"
              "\nThen press ENTER to continue on with other forms")

    os.system('cls')

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

    os.system('cls')

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

        # Type of visa ( optional )
        visa_type = jsn[6]['intended_visa_type']
        options = _get_text_options("#cas-program-questions-230277>option")
        if visa_type in options:
            type_locator = "select#cas-program-questions-230277"
            el_type = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, type_locator)))
            select = Select(el_type)
            select.select_by_visible_text(visa_type)
            logger.info('Visa type selected : {}'.format(visa_type))
        else:
            logger.info('Could not select visa type: {}'.format(visa_type))

        wait_for_angular()

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    os.system('cls')

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

    os.system('cls')

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

            web_options = _get_text_options('#personalInfo-otherInfo-languageProficiency-additionalLanguage-proficiencyLevel>option')
            select_lang = 'Advanced'
            if another_prof in web_options:
                select_lang = another_prof
            another_prof_locator = "select#personalInfo-otherInfo-languageProficiency-additionalLanguage-proficiencyLevel"
            el_prof_another = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, another_prof_locator)))
            select = Select(el_prof_another)
            select.select_by_visible_text(select_lang)

            wait_for_angular()

        disciplined = jsn[5]['Have you ever been disciplined for academic performance']
        disciplined2 = jsn[5]['Have you ever been disciplined for student conduct violation']
        family_usc = jsn[6]['Did your parents or siblings attend USC?']
        first_to_college = jsn[6]['Are you the first-generation in your family to go to college?']
        employed_usc = jsn[6]['Are your parents or spouse employed at USC?']
        apply_dual = jsn[6]['Are you applying for a dual degree at USC?']
        apply_before = jsn[6]['Have you previously applied to or attended USC?']
        sponsorship = jsn[6]['Have you applied for, received, or are planning to apply for a financial' \
                             ' sponsorship from your employer?']
        competitive_award = jsn[6]['non-USC fellowship or nationally competitive award?']

        radios = []
        if disciplined.lower() == 'yes':
            radios.append("div#personalInfo-otherInfo-infractions-academic4-yes>div")
        elif disciplined.lower() == 'no':
            radios.append("div#personalInfo-otherInfo-infractions-academic4-no>div")

        if disciplined2.lower() == 'yes':
            radios.append("div#personalInfo-otherInfo-infractions-academic1-yes>div")
        elif disciplined2.lower() == 'no':
            radios.append("div#personalInfo-otherInfo-infractions-academic1-no>div")

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

        # interested in financail assistance
        radios.append("div#cas-program-questions-251733-577872>div")

        # award
        if competitive_award.lower() == 'yes':
            radios.append("div#cas-program-questions-251734-577874>div")
        elif competitive_award.lower() == 'no':
            radios.append("div#cas-program-questions-251734-577875>div")

        # Do you wish to be considered for a graduate fellowship or assistantship
        radios.append("div#cas-program-questions-251740-577905>div")

        for radio in radios:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, radio))).click()

        # Marital status
        marital_status = jsn[3]['maritial']
        if marital_status and marital_status.lower() == 'single':
            marital_status = 'Single'
        elif marital_status and marital_status.lower() == 'married':
            marital_status = 'Married'
        else:
            marital_status = None

        if marital_status:
            marital_locator = "select#cas-program-questions-251726"
            el_marital = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, marital_locator)))
            select = Select(el_marital)
            select.select_by_visible_text(marital_status)

        submit_form()

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    # _______________________
    # SUPPORTING INFORMATION

    school_urls = _get_urls('usc-supporting')

    os.system('cls')

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
                if company_type.lower().count('full'):
                    visible_text = 'Full time'
                elif company_type.lower().count('part'):
                    visible_text = 'Part time'
                elif company_type.lower().count('temp'):
                    visible_text = 'Temporary'

                if visible_text:
                    exp_type = 'select#supportingInfo-experiences-experience-employmentDates-status'
                    el_experience = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, exp_type)))
                    select = Select(el_experience)
                    select.select_by_visible_text(visible_text)
                    wait_for_angular()
                else:
                    logger.info('Status not provided')

                # hours
                el_name = driver.find_element_by_css_selector("[name='averageWeeklyHours']")
                el_name.clear()
                el_name.send_keys('40')
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

    os.system('cls')

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

    os.system('cls')

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

    os.system('cls')

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

    os.system('cls')

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

    # _______________________
    # ACADEMIC HISTORY

    school_urls = _get_urls('usc-history')

    os.system('cls')

    # HIGH SCHOOL ATTENDED
    # *******************************

    logger.info('High school attended form')

    try:
        driver.get(school_urls[0][1])

        wait_for_angular()

        highs = []
        if jsn[0]['univ_1_degree']:
            high_school = []
            high_school.append(jsn[0]['univ_1_degree'])
            high_school.append(jsn[0]['univ_state_1'])
            high_school.append(jsn[0]['univ_name_1'])
            high_school.append(jsn[0]['univ_city_1'])
            high_school.append(jsn[0]['univ_1_graduation_date'])
            highs.append(high_school)
        if jsn[0]['univ_2_degree']:
            high_school = []
            high_school.append(jsn[0]['univ_2_degree'])
            high_school.append(jsn[0]['univ_state_2'])
            high_school.append(jsn[0]['univ_name_2'])
            high_school.append(jsn[0]['univ_city_2'])
            high_school.append(jsn[0]['univ_2_graduation_date'])
            highs.append(high_school)
        if jsn[0]['univ_3_degree']:
            high_school = []
            high_school.append(jsn[0]['univ_3_degree'])
            high_school.append(jsn[0]['univ_state_3'])
            high_school.append(jsn[0]['univ_name_3'])
            high_school.append(jsn[0]['univ_city_3'])
            high_school.append(jsn[0]['univ_3_graduation_date'])
            highs.append(high_school)

        if _wait_for_element('.cas-opted-out-background', 1) > 0:
            logger.info('High school already opted out')

        for h in highs:
            logger.info('Found the following high schools: {}'.format(h))

        if len(highs) > 0:

            for h in highs:

                raw_input('Please click on Add high schools. We\'ll add high schools now ... \n'
                          'press ENTER when you are on the actual form: \'Add Your High School\'')

                wait_for_angular()

                el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'input[name="highSchoolName"]')))
                el.send_keys(h[2])

                driver.find_element_by_css_selector('[name="city"]').send_keys(h[3])

                wait_for_angular()

                # always graduate
                el = driver.find_element_by_css_selector('#academicHistory-highSchoolAttended-highSchool-graduated-yes')
                el.click()
                wait_for_angular()

                split_date = h[4].split('-')
                month_ = split_date[1]
                month = _convert_month(month_)
                year = split_date[0]

                month_sel = 'select#academicHistory-highSchoolAttended-highSchool-graduationDate-month'
                el_month = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, month_sel)))
                select = Select(el_month)
                select.select_by_visible_text(month)
                wait_for_angular()

                year_sel = 'select#academicHistory-highSchoolAttended-highSchool-graduationDate-year'
                el_year = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, year_sel)))
                select = Select(el_year)
                select.select_by_visible_text(year)
                wait_for_angular()

                raw_input('Please fill the remaining fields and click on the Save This School button')

    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    os.system('cls')

    # COLLEGE ATTENDED
    # *******************************

    logger.info('College attended form')

    try:
        driver.get(school_urls[0][2])

        wait_for_angular()

        if jsn[0]['school_name']:
            logger.info('Found the following school: \nName: {} \nCountry: {} \nCity: {} \nGraduation date: {} \
                        \nStart date: {} \nEnd date: {}'.format(
                        jsn[0]['school_name'], jsn[0]['school_country'], jsn[0]['school_city'],
                        jsn[0]['school_grad_date'], jsn[0]['school_date_from'], jsn[0]['school_date_to']))

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '.cas-primary-button-large-add'))).click()

        wait_for_angular()

        el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input[name="name"]')))
        el.send_keys(jsn[0]['school_name'])

        wait_for_angular()

        first_suggested = '.cas-college-suggestions-list>li:nth-of-type(1)'
        suggested_element = _wait_for_clickable(first_suggested, 5)
        if suggested_element:
            suggested_element.click()
            wait_for_angular()

            if jsn[0]['school_grad_date']:
                # graduated (Did you obtain a degree from this college?)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'div#academicHistory-collegesAttended-college-degreeObtained-yes'))).click()
            else:
                # in progress
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'div#academicHistory-collegesAttended-college-degreeObtained-inProgress'))).click()

            wait_for_angular()

            # graduate
            split_date = jsn[0]['school_grad_date'].split('-')
            grad_month = _convert_month(split_date[1])
            grad_year = split_date[0]

            month_sel = 'select#academicHistory-collegesAttended-college-graduated-degreeDate-month'
            el_month = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, month_sel)))
            select = Select(el_month)
            select.select_by_visible_text(grad_month)
            wait_for_angular()

            year_sel = 'select#academicHistory-collegesAttended-college-graduated-degreeDate-year'
            el_year = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, year_sel)))
            select = Select(el_year)
            select.select_by_visible_text(grad_year)
            wait_for_angular()

            # Semester
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                By.CSS_SELECTOR, '[label="Semester"]'))).click()
            wait_for_angular()

            # First Semester

            # start date
            split_date = jsn[0]['school_date_from'].split('-')
            start_month = _convert_month(split_date[1])
            start_year = split_date[0]

            month_sel = 'select#academicHistory-collegesAttended-college-degreeDate-termStart-month'
            el_month = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, month_sel)))
            select = Select(el_month)
            select.select_by_visible_text(start_month)
            wait_for_angular()

            year_sel = 'select#academicHistory-collegesAttended-college-degreeDate-termStart-year'
            el_year = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, year_sel)))
            select = Select(el_year)
            select.select_by_visible_text(start_year)
            wait_for_angular()

            # Last Semester

            # end date
            split_date = jsn[0]['school_date_to'].split('-')
            end_month = _convert_month(split_date[1])
            end_year = split_date[0]

            month_sel = 'select#academicHistory-collegesAttended-college-degreeDate-termEnd-month'
            el_month = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, month_sel)))
            select = Select(el_month)
            select.select_by_visible_text(end_month)
            wait_for_angular()

            year_sel = 'select#academicHistory-collegesAttended-college-degreeDate-termEnd-year'
            el_year = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, year_sel)))
            select = Select(el_year)
            select.select_by_visible_text(end_year)
            wait_for_angular()

        raw_input("Please help me fill out this form ... and click Save this College\n"
                  "Press ENTER when you are ready to move to the next form")
    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    os.system('cls')

    # GPA ENTRIES
    # *******************************

    logger.info('GPA Entries')

    try:
        driver.get(school_urls[0][3])

        wait_for_angular()

        raw_input("Please help me fill out this form ...\n"
                  "Press ENTER when you are ready to move to the next form")
    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    os.system('cls')

    # EDUCATIONAL GAP
    # *******************************

    logger.info('Eduational Gap')

    try:
        driver.get(school_urls[0][4])

        wait_for_angular()

        educational_gap = jsn[6]['education_gap']
        educational_gap_exp = jsn[6]['education_gap_explain']

        web_options = ['Not applicable', 'Working', 'Traveling',
                       'Taking care of personal matters', 'Military enrollment', 'Other']

        logger.info("Found educational gap: type {}, why: {}".format(educational_gap, educational_gap_exp))

        if educational_gap and educational_gap in web_options:

            gap_locator = 'select#cas-custom-questions-180266'
            el_gap = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, gap_locator)))
            select = Select(el_gap)
            select.select_by_visible_text(educational_gap)
            wait_for_angular()

            if educational_gap == 'Other':
                text_area = '#cas-custom-questions-180267'
                el_gap_text = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, text_area)))
                el_gap_text.send_keys(educational_gap_exp)

        raw_input("Please help me fill out this form, if you are happy with this form, click on Save and Continue ...\n"
                  "Press ENTER when you are ready to move to the next form")
    except:
        logger.info('an error happened when filling this form.', exc_info=debug)
        raw_input("Please manually fill out this form and submit it."
                  "\nMake sure when the form is submitted you close the successful message"
                  "\nThen press ENTER to continue on with other forms")

    os.system('cls')

    # TESTS
    # *******************************

    logger.info('Standardized Tests')

    try:
        driver.get(school_urls[0][5])

        wait_for_angular()

        logger.info("Tefl and IELTS:")
        if jsn[4]['toefl_date']:
            logger.info('Tefl: Speaking score: {}'.format(jsn[4]['toefl_speaking_score']))
            logger.info('Tefl: Total score: {}'.format(jsn[4]['toefl_total_score']))
            logger.info('Tefl: Writing score: {}'.format(jsn[4]['toefl_writing_score']))
            logger.info('Tefl: Reading score: {}'.format(jsn[4]['toefl_reading_score']))
            logger.info('Tefl: Date: {}'.format(jsn[4]['toefl_date']))
        if jsn[4]['ielts_date']:
            logger.info('Ielts: Listening: {}'.format(jsn[4]['ielts_listning']))
            logger.info('Ielts: Total score: {}'.format(jsn[4]['ielts_total_score']))
            logger.info('Ielts: Writing score: {}'.format(jsn[4]['ielts_writing_score']))
            logger.info('Ielts: Speaking score: {}'.format(jsn[4]['ielts_speaking_score']))
            logger.info('Ielts: Reading score: {}'.format(jsn[4]['ielts_reading_score']))
            logger.info('Ielts: Date: {}'.format(jsn[4]['ielts_date']))

        logger.info("All tests data: \n")

        ielts_items  = _group_relevant_items(jsn[4], 'ielts')
        for key, value in ielts_items.iteritems():
            logger.info('key: {} value: {}'.format(key, value))

        if jsn[4]['toefl_date']:

            logger.info("Adding TOEFL")
            button = 'ul li:nth-of-type(5) button'

            if _wait_for_element(button, 1):

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, button))).click()
                wait_for_angular()
                toefl_date = _parse_date(jsn[4]['toefl_date'])

                taken = 'div#academicHistory-standardizedtests-addToeflTest-takenTest-yes>div'
                WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, taken))).click()
                wait_for_angular()

                paper_test = 'select#academicHistory-standardizedtests-toefltest-testTaken'
                el_test = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, paper_test)))
                select = Select(el_test)
                select.select_by_visible_text('Paper-based')
                wait_for_angular()

                css = '[name="readingScorePBT"]'
                reading = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                reading.send_keys(jsn[4]['toefl_reading_score'])

                css = '[name="totalScorePBT"]'
                total = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                total.send_keys(jsn[4]['toefl_total_score'])

                css = '[name="testOfWrittenEnglishScorePBT"]'
                reading = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                reading.send_keys(jsn[4]['toefl_writing_score'])

                raw_input("Please select date: {} and press Save This Test to continue".format(toefl_date))
            else:
                logger.info('Tefl already added (?)')

        elif jsn[4]['ielts_date']:

            logger.info("Adding IELTS")
            button = 'ul li:nth-of-type(4) button'

            if _wait_for_element(button, 1):

                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, button))).click()
                wait_for_angular()
                ielts_date = _parse_date(jsn[4]['ielts_date'])

                taken = 'div#academicHistory-standardizedtests-addAllTest-yes>div'
                WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, taken))).click()
                wait_for_angular()

                raw_input("Please select date: {} and press Save This Test to continue".format(ielts_date))
            else:
                logger.info('Tefl already added (?)')

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

    log_file = os.path.join(parse, "output.log")
    file_hndlr = logging.FileHandler(log_file)
    logger.addHandler(file_hndlr)
    console = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(console)
    ch = logging.Formatter('[%(levelname)s] %(message)s')
    console.setFormatter(ch)
    file_hndlr.setFormatter(ch)
    logger.setLevel(logging.getLevelName('DEBUG'))


def _convert_month(month):
    m_ = time.strptime(month, '%m')
    return time.strftime('%B', m_)


def _parse_date(date_):

    d = date_.split('-')
    return "{}/{}/{}".format(d[1], d[2], d[0])


def _group_relevant_items(section, group_by):

    r = {}
    for key, value in section.iteritems():
        if key.count(group_by):
            r[key] = value
    return r


def _get_text_options(selector):

    try:
        els =  WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
        return [el.text for el in els]
    except:
        logger.warning('Options not found. This might be an issue with selector ... ')


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


def _wait_for_clickable(el, time_=5):
    try:
        return WebDriverWait(driver, time_).until(EC.element_to_be_clickable((By.CSS_SELECTOR, el)))
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