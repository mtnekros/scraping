import re
import csv
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# WAIT DURATIONS
SHORT_WAIT_DURATION_SECS = 1
WAIT_DURATION_SECS = 2
LONG_WAIT_DURATION_SECS = 4
MAX_WAIT_DURATION = 10
# MIN ZOOM LEVEL
MIN_ZOOM_LEVEL = 11
# SELECTORS
RESULT_FROM = '#pane > div > div.widget-pane-content.cYB2Ge-oHo7ed > div > div > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ > div.UTvBab > div > div:nth-child(1) > span > span:nth-child(1)'
RESULT_TO = '#pane > div > div.widget-pane-content.cYB2Ge-oHo7ed > div > div > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ > div.UTvBab > div > div:nth-child(1) > span > span:nth-child(2)'
NEXT_BTN = "#ppdPk-Ej1Yeb-LgbsSe-tJiF1e"
PREV_BTN = "#ppdPk-Ej1Yeb-LgbsSe-E7ORLb"
RESULT_ITEM = '#pane > div > div.widget-pane-content.cYB2Ge-oHo7ed > div > div > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ > div:not(.TFQHme)'
RESULT_SECTION = "#pane > div > div.widget-pane-content.cYB2Ge-oHo7ed > div > div > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ > div.section-layout.section-scrollbox.cYB2Ge-oHo7ed.cYB2Ge-ti6hGc.siAUzd-neVct-Q3DXx-BvBYQ"
# DETAILS
SHOP_NAME_SELECTOR = ".qBF1Pd.gm2-subtitle-alt-1"
LOCATION_LINK_SELECTOR = ".a4gq8e-aVTXAb-haAclf-jRmmHf-hSRGPd"
SHOP_TYPE_SELECTOR = ".ZY2y6b-RWgCYc:nth-child(2) span:nth-child(1)"
LOCATION_ID_INFO_SELECTOR = ".ZY2y6b-RWgCYc .ZY2y6b-RWgCYc:nth-child(2) > span:last-child"
PHONE_NUMBER_INFO_SELECTOR = ".ZY2y6b-RWgCYc .ZY2y6b-RWgCYc:nth-child(3) span:last-child"
EXTRA_INFO_SELECTOR = ".ZY2Y6B-RWGCYC .ZY2Y6B-RWGCYC:NTH-CHILD(3)"
# OUTPUT COLUMNS
NAME = 'Name'
SHOP_TYPE = "Shop type"
LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
LOCATION = "Location"
PHONE_NUMBER = "Phone number"
EXTRA_INFO = "Extra info"
LOCATION_LINK = "Location link"

OUTPUT_COLUMNS = [
    NAME,
    SHOP_TYPE,
    LATITUDE,
    LONGITUDE,
    LOCATION,
    PHONE_NUMBER,
    EXTRA_INFO,
    LOCATION_LINK,
]

def get_outfile_name():
    curr_time = time.strftime('%Y_%m_%d_%H:%M:%S')
    return f'./data/{curr_time}_agrovets.csv'

def get_search_locations():
    search_locations = []
    with open('./urls.txt', 'r') as urls_file:
        search_locations = urls_file.read().split("\n")
    return search_locations

def set_lang_en(driver):
    driver.get('https://www.google.com/')
    driver.find_element_by_link_text('English').click()

def wait_and_get_element(selector, driver):
    return WebDriverWait(driver, timeout=50).until(lambda d: d.find_element_by_css_selector(selector))

def get_element_if_exists(selector, node):
    elements = node.find_elements_by_css_selector(selector)
    if len(elements) == 0:
        return None
    return elements[0]

def all_result_item_is_visible(driver):
    time.sleep(WAIT_DURATION_SECS)
    start = wait_and_get_element(RESULT_FROM, driver).text
    end = wait_and_get_element(RESULT_TO, driver).text
    total_result_count = int(end) - int(start) + 1 
    # have add one because the last one is a hidden annoying div
    visible_result_count = len(driver.find_elements_by_css_selector(RESULT_ITEM)) - 1
    return total_result_count == visible_result_count

def refresh_the_results(driver):
    """
    Refreshes the results by clicking back and next or refreshing
    Doing this seems to effectively refresh the results when it's not loading
    """
    not_first_results_page = get_prev_page_results(driver)
    if not_first_results_page:
        get_next_page_results(driver)
    else:
        # if this is the first page, no need to go to next page
        driver.refresh()
        time.sleep(LONG_WAIT_DURATION_SECS)

def scroll_to_last_result(driver):
    WebDriverWait(driver, timeout=50).until(lambda d: d.find_element_by_css_selector(RESULT_SECTION))
    seconds_waited = 0
    while not all_result_item_is_visible(driver):
        driver.execute_script(f'document.querySelector("{RESULT_SECTION}").scrollTop=10000;')
        time.sleep(SHORT_WAIT_DURATION_SECS)
        seconds_waited += SHORT_WAIT_DURATION_SECS
        # if we are scrolling infinitely this will refresh the results
        if seconds_waited > MAX_WAIT_DURATION:
            seconds_waited = 0
            refresh_the_results(driver)

def get_coordinates_from_link(link):
    result = re.search('!3d(\d{2}\.\d+)!4d(\d{2}\.\d+)', link)
    if result is None:
        return {
            LATITUDE: None,
            LONGITUDE: None,
        }
    return {
        LATITUDE: result.groups()[0],
        LONGITUDE: result.groups()[1],
    }

def extract_phone_number(phone_number):
    if phone_number is not None and all(c.isnumeric() or c == '-' for c in phone_number.text.strip()):
        return phone_number.text
    return 'N/A'

def extract_details(driver):
    details = []
    for shop in driver.find_elements_by_css_selector(RESULT_ITEM)[:-1]: # last one is a hidden unrequired thing
        shop_name = shop.find_element_by_css_selector( SHOP_NAME_SELECTOR ).text
        location_link = shop.find_element_by_css_selector( LOCATION_LINK_SELECTOR ).get_attribute('href')
        shop_type = shop.find_element_by_css_selector( SHOP_TYPE_SELECTOR ).text
        location_id = get_element_if_exists(LOCATION_ID_INFO_SELECTOR, shop)
        phone_number = get_element_if_exists(PHONE_NUMBER_INFO_SELECTOR, shop)
        extra_info = get_element_if_exists(EXTRA_INFO_SELECTOR, shop)
        info = {
            NAME: shop_name,
            LOCATION_LINK: location_link,
            SHOP_TYPE: shop_type,
            LOCATION: location_id and location_id.text.replace('· ', ''),
            PHONE_NUMBER: extract_phone_number(phone_number),
            EXTRA_INFO: extra_info and extra_info.text,
            **get_coordinates_from_link(location_link)
        }
        details.append(info)
    return details
    
def search(search_text):
    searchbox = driver.find_element_by_css_selector('#searchboxinput')
    searchbox.clear()
    searchbox.send_keys(search_text)
    searchbox.send_keys(Keys.RETURN)

def get_prev_page_results(driver):
    prev_btn = driver.find_element_by_css_selector(PREV_BTN)
    not_first_results_page = prev_btn.is_enabled()
    if not_first_results_page:
        try:
            prev_btn.click()
        except WebDriverException as e:
            print(e)
        time.sleep(WAIT_DURATION_SECS)
    return not_first_results_page

def get_next_page_results(driver):
    next_btn = driver.find_element_by_css_selector(NEXT_BTN)
    has_more_results = next_btn.is_enabled()
    if has_more_results:
        try:
            next_btn.click()
        except WebDriverException as e:
            print(e)
        time.sleep(WAIT_DURATION_SECS)
    return has_more_results

def zoom_level_too_low(driver: webdriver.Chrome):
    match = re.search('@\d{2}\.\d+,\d{2}\.\d+,(\d+)z', driver.current_url)
    if match and len(match.groups()):
        too_low = float(match.groups()[0]) <= MIN_ZOOM_LEVEL
        return too_low
    return True

def get_all_shop_info(driver, url, search_text="agrovet"):
    driver.get(url)
    search(search_text)
    results = []
    has_more_results = True
    # loop through all results
    while has_more_results:
        try:
            scroll_to_last_result(driver)
            results.extend(extract_details(driver))
            has_more_results = not zoom_level_too_low(driver) and get_next_page_results(driver)
        except:
            with open('errors.txt', 'a') as errorFile:
                errorFile.write(f"ERROR: {url}\n")
            return []
    return results

def write_to_csv(results, out_filename, columns, mode='w'):
    try:
        with open(out_filename, mode) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for data in results:
                writer.writerow(data)
    except IOError:
        print("I/O error")

if __name__ == '__main__':
    driver = webdriver.Chrome("./chromedriver")
    set_lang_en(driver)
    locations = get_search_locations()
    total_locations = len(locations)
    out_filename = get_outfile_name()
    for index,location in enumerate(locations, start=1):
        completion_percent = round(index/float(total_locations)*100, 2)
        print(f"{index}/{total_locations}: {completion_percent}% completed: trying {location}")
        results = get_all_shop_info(driver, location)
        write_to_csv(results, out_filename, OUTPUT_COLUMNS, mode='a')
        print(f"Extracted {len(results)} vetshops")
    driver.close()
